# core.py
import groq
import sqlite3
import json
import re
import time

def init_db():
    conn = sqlite3.connect("prompt_frameworks.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS frameworks (
        id INTEGER PRIMARY KEY, 
        name TEXT UNIQUE, 
        prompt TEXT
    )''')
    json_instruction = "Immediately return the response as a valid JSON object or list, strictly formatted as requested, with no additional text outside the JSON structure. Do not ask for clarification or additional input—use the provided summary to generate the response now."
    examples = [
        (
            "comprehension", 
            f"{json_instruction}\nGiven this summary: {{SUMMARY}}, generate 5 multiple-choice questions with timestamps (MM:SS) from the summary, "
            "each with 4 options and one correct answer. Return in JSON format with 'time', 'question', 'options', 'correct' keys."
        ),
        (
            "application", 
            f"{json_instruction}\nGiven this summary: {{SUMMARY}}, create 3 fill-in-the-blanks activities with timestamps (MM:SS) from the summary, "
            "each with text containing one blank (*word*) and its answer. Return in JSON format with 'time', 'text', 'answer' keys."
        ),
        (
            "reflection", 
            f"{json_instruction}\nGiven this summary: {{SUMMARY}}, generate 2 interactions: 1 text overlay and 1 open-ended question with timestamps (MM:SS) from the summary. "
            "Return in JSON format with 'time', 'type' ('text' or 'question'), and 'text' or 'question' keys."
        ),
        (
            "analysis", 
            f"{json_instruction}\nGiven this summary: {{SUMMARY}}, analyze the content and immediately generate 4 multiple-choice questions with timestamps (MM:SS) from the summary that require breaking down concepts, "
            "each with 4 options and one correct answer. Return in JSON format with 'time', 'question', 'options', 'correct' keys."
        ),
        (
            "synthesis", 
            f"{json_instruction}\nGiven this summary: {{SUMMARY}}, create 3 activities with timestamps (MM:SS) from the summary: 1 multiple-choice, 1 fill-in-the-blank, and 1 text overlay, "
            "focusing on combining ideas from the summary. Return in JSON format with appropriate keys ('time', 'question', 'options', 'correct' for MC; 'time', 'text', 'answer' for blanks; 'time', 'type', 'text' for text)."
        )
    ]
    c.executemany("INSERT OR IGNORE INTO frameworks (name, prompt) VALUES (?, ?)", examples)
    conn.commit()
    conn.close()

def get_prompt_by_name(name):
    conn = sqlite3.connect("prompt_frameworks.db")
    c = conn.cursor()
    c.execute("SELECT prompt FROM frameworks WHERE name = ?", (name,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_frameworks():
    conn = sqlite3.connect("prompt_frameworks.db")
    c = conn.cursor()
    c.execute("SELECT name FROM frameworks")
    frameworks = [row[0] for row in c.fetchall()]
    conn.close()
    return frameworks

init_db()

def extract_json_from_text(text):
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        return json_match.group(1).strip()
    return text.strip()

def call_groq(messages, api_key, output_file=None, model="llama3-70b-8192"):
    print(f"Calling Groq API with {len(messages)} messages")
    print(f"System message (first 100 chars): {messages[0]['content'][:100]}")
    print(f"User message (first 100 chars): {messages[1]['content'][:100]}")
    print(f"Using model: {model}")
    api_key = api_key.strip()
    
    try:
        client = groq.Groq(api_key=api_key)
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    messages=messages,
                    model=model,  # Use the specified model
                    temperature=0.3
                )
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Connection error on attempt {attempt+1}/{max_retries}: {str(e)}. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
        
        response_text = response.choices[0].message.content
        print(f"Received response (first 100 chars): {response_text[:100]}")
        
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response_text)
            print(f"Wrote response to {output_file}")
        
        cleaned_response = extract_json_from_text(response_text)
        print(f"Cleaned response (first 100 chars): {cleaned_response[:100]}")
        if not cleaned_response:
            print("Warning: Empty JSON response after cleaning")
            return []
        
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw response: {response_text}")
            return []
    except Exception as e:
        print(f"Error calling Groq API: {str(e)}")
        return []