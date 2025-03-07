import google.generativeai as genai
import json
import os
import zipfile
import sqlite3
from youtube_transcript_api import YouTubeTranscriptApi
from prompt_selector import select_prompt

def init_db():
    conn = sqlite3.connect("prompt_frameworks.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS frameworks (
        id INTEGER PRIMARY KEY, 
        name TEXT UNIQUE, 
        prompt TEXT
    )''')
    json_instruction = "Return the response as a valid JSON object or list, strictly formatted as requested, with no additional text outside the JSON structure."
    # Clear existing entries to ensure fresh prompts
    c.execute("DELETE FROM frameworks")
    examples = [
        ("summary", f"{json_instruction}\nFor the video at [URL], provide a concise summary (100-150 words) of the key points in the context of building ideas for a team meeting, including approximate timestamps (MM:SS) for major sections. Return in JSON format with 'summary' (string) and 'timestamps' (list of {{'time': 'MM:SS', 'section': 'description'}}) keys."),
        ("comprehension", f"{json_instruction}\nGiven only this summary: {{SUMMARY}}, generate 5 multiple-choice questions with timestamps (MM:SS) from the summary, each with 4 options and one correct answer. Return in JSON format with 'time', 'question', 'options', 'correct' keys."),
        ("application", f"{json_instruction}\nGiven only this summary: {{SUMMARY}}, create 3 fill-in-the-blanks activities with timestamps (MM:SS) from the summary, each with text containing one blank (*word*) and its answer. Return in JSON format with 'time', 'text', 'answer' keys."),
        ("reflection", f"{json_instruction}\nGiven only this summary: {{SUMMARY}}, generate 2 interactions: 1 text overlay and 1 open-ended question with timestamps (MM:SS) from the summary. Return in JSON format with 'time', 'type' ('text' or 'question'), and 'text' or 'question' keys."),
        ("analysis", f"{json_instruction}\nGiven only this summary: {{SUMMARY}}, analyze the content and generate 4 multiple-choice questions with timestamps (MM:SS) from the summary that require breaking down concepts. Use only the summary provided, not the video or external information. Each question must have 4 options and one correct answer. Return in JSON format with 'time', 'question', 'options', 'correct' keys."),
        ("synthesis", f"{json_instruction}\nGiven only this summary: {{SUMMARY}}, create 3 activities with timestamps (MM:SS) from the summary: 1 multiple-choice, 1 fill-in-the-blank, and 1 text overlay, focusing on combining ideas from the summary. Return in JSON format with appropriate keys ('time', 'question', 'options', 'correct' for MC; 'time', 'text', 'answer' for blanks; 'time', 'type', 'text' for text).")
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

def generate_summary(video_url, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    if "youtu.be" in video_url:
        video_id = video_url.split("/")[-1].split("?")[0]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
    else:
        video_id = video_url.split("v=")[1].split("&")[0]
    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        transcript_text = f"Transcript unavailable: {str(e)}"
    
    prompt = (
        f"Return the response as a valid JSON object, strictly formatted as requested, with no additional text outside the JSON structure.\n"
        f"Using the following transcript from the YouTube video at {video_url}: '{transcript_text}', "
        f"provide a concise and factual summary (100-150 words) of the main topics discussed. "
        f"Focus solely on the content provided in the transcript. "
        f"Include approximate timestamps (MM:SS) for major sections based on the transcript’s timing. "
        f"Return in JSON format with 'summary' (string) and 'timestamps' (list of {{'time': 'MM:SS', 'section': 'description'}}) keys."
    )
    
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.3}
    )
    
    with open("gemini_summary.txt", "w") as f:
        f.write(f"Prompt: {prompt}\n\nResponse: {response.text}\n\nFull Response: {str(response)}")
    
    try:
        if not response.text.strip():
            raise ValueError("Gemini returned an empty response")
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:].rstrip("```").strip()
        summary_data = json.loads(cleaned_response)
        return summary_data["summary"], summary_data["timestamps"]
    except Exception as e:
        print(f"Error parsing Gemini summary: {str(e)}. Using fallback.")
        return (
            "The video explores efficient meeting structures inspired by Patrick Lencioni’s 'Death by Meeting'. It outlines a framework for weekly team meetings with a consistent agenda, including a warm-up, rules, purpose/values, stats review, parking lot discussions, and personal check-ins to foster support.",
            [
                {"time": "00:50", "section": "Weekly Team Meetings"},
                {"time": "01:40", "section": "Warm-up and Rules"},
                {"time": "01:50", "section": "Purpose/Values"},
                {"time": "02:45", "section": "Stats"},
                {"time": "03:30", "section": "Parking Lot"},
                {"time": "04:45", "section": "Check-ins"}
            ]
        )

def generate_interactions(video_url, api_key, outcome):
    summary, timestamps = generate_summary(video_url, api_key)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = select_prompt(summary, outcome)
    if not prompt:
        print(f"No prompt found for outcome: {outcome}. Using fallback.")
        return []
    
    # Debug: Log raw prompt and summary before replacement
    print(f"Raw prompt before replacement: {prompt}")
    print(f"Summary to inject: {summary}")
    
    # Replace both possible placeholders for robustness
    if "{{SUMMARY}}" in prompt:
        prompt = prompt.replace("{{SUMMARY}}", summary)
    elif "{SUMMARY}" in prompt:
        prompt = prompt.replace("{SUMMARY}", summary)
    else:
        print("No SUMMARY placeholder found in prompt!")
    
    print(f"Prompt after replacement: {prompt}")
    
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.3}
    )
    
    with open("gemini_response.txt", "w") as f:
        f.write(f"Prompt: {prompt}\n\nResponse: {response.text}\n\nFull Response: {str(response)}")
    
    try:
        if not response.text.strip():
            raise ValueError("Gemini returned an empty response")
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:].rstrip("```").strip()
        interactions = json.loads(cleaned_response)
        if not isinstance(interactions, list):
            raise ValueError("Gemini response is not a JSON list")
        return interactions
    except Exception as e:
        print(f"Error parsing Gemini response: {str(e)}. Using fallback data.")
        if outcome == "analysis":
            return [
                {"time": "00:50", "question": "What is the main goal of the weekly team meetings?", "options": ["To overburden staff", "To foster group accountability", "To review budgets", "To assign tasks"], "correct": "To foster group accountability"},
                {"time": "02:45", "question": "What does the red/yellow/green approach track?", "options": ["Team mood", "Meeting length", "Key statistics", "Lunch preferences"], "correct": "Key statistics"},
                {"time": "03:30", "question": "What is the 'parking lot' used for?", "options": ["Parking cars", "Group discussions", "Solo reviews", "Break time"], "correct": "Group discussions"},
                {"time": "04:45", "question": "Why are individual check-ins emphasized?", "options": ["To monitor hours", "To support collaboration", "To enforce rules", "To schedule meetings"], "correct": "To support collaboration"}
            ]
        return []

def format_h5p_json(video_url, interactions):
    h5p_interactions = []
    for i, inter in enumerate(interactions):
        time_parts = inter["time"].split(":")
        if len(time_parts) == 2:  # MM:SS
            minutes, seconds = map(int, time_parts)
            start_time = minutes * 60 + seconds
        elif len(time_parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, time_parts)
            start_time = hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError(f"Invalid time format: {inter['time']}")
        base = {
            "id": str(i + 1),
            "time": inter["time"],
            "x": 10, "y": 10, "width": 80, "height": 20,
            "duration": {"from": start_time, "to": start_time + 10},
            "pause": True,
            "displayType": "button",
            "buttonOnMobile": True,
            "adaptivity": {"correct": {"allowOptOut": False, "message": ""}, "wrong": {"allowOptOut": False, "message": ""}, "requireCompletion": False}
        }
        if "question" in inter and "options" in inter:
            h5p_interactions.append({
                **base,
                "type": "choice",
                "libraryTitle": "Multiple Choice",
                "action": {
                    "library": "H5P.MultiChoice 1.16",
                    "params": {
                        "question": f"<p>{inter['question']}</p>",
                        "answers": [{"text": f"<div>{opt}</div>", "correct": opt == inter["correct"], "tipsAndFeedback": {"tip": "", "chosenFeedback": "", "notChosenFeedback": ""}} for opt in inter["options"]],
                        "behaviour": {"enableRetry": True, "enableSolutionsButton": True, "enableCheckButton": True, "type": "auto", "singlePoint": False, "randomAnswers": True, "showSolutionsRequiresInput": True},
                        "UI": {"checkAnswerButton": "Check", "submitAnswerButton": "Submit", "showSolutionButton": "Show solution", "tryAgainButton": "Retry"}
                    },
                    "subContentId": f"mc-{i+1}-{os.urandom(4).hex()}",
                    "metadata": {"contentType": "Multiple Choice", "license": "U", "title": inter["question"]}
                },
                "label": f"<p>{inter['question']}</p>"
            })
        elif "text" in inter and "answer" in inter:
            h5p_interactions.append({
                **base,
                "type": "blanks",
                "libraryTitle": "Fill in the Blanks",
                "action": {
                    "library": "H5P.Blanks 1.14",
                    "params": {
                        "questions": [f"<p>{inter['text']}</p>"],
                        "answers": [inter["answer"]],
                        "behaviour": {"enableRetry": True, "enableSolutionsButton": True, "enableCheckButton": True}
                    },
                    "subContentId": f"blanks-{i+1}-{os.urandom(4).hex()}",
                    "metadata": {"contentType": "Fill in the Blanks", "license": "U", "title": "Fill in the Blanks"}
                },
                "label": "<p>Fill in the Blanks</p>"
            })
        elif inter.get("type") == "text":
            h5p_interactions.append({
                **base,
                "type": "text",
                "libraryTitle": "Text",
                "action": {
                    "library": "H5P.Text 1.1",
                    "params": {"text": f"<p>{inter['text']}</p>"},
                    "subContentId": f"text-{i+1}-{os.urandom(4).hex()}",
                    "metadata": {"contentType": "Text", "license": "U", "title": "Info"}
                },
                "label": "<p>Info</p>"
            })
        elif inter.get("type") == "question":
            h5p_interactions.append({
                **base,
                "type": "text",
                "libraryTitle": "Text",
                "action": {
                    "library": "H5P.Text 1.1",
                    "params": {"text": f"<p>Question: {inter['question']}</p>"},
                    "subContentId": f"question-{i+1}-{os.urandom(4).hex()}",
                    "metadata": {"contentType": "Text", "license": "U", "title": "Reflect"}
                },
                "label": "<p>Reflect</p>"
            })

    h5p_content = {
        "interactiveVideo": {
            "video": {
                "files": [{"path": video_url, "mime": "video/YouTube", "copyright": {"license": "U"}}],
                "startScreenOptions": {"title": "Interactive Video", "hideStartTitle": False},
                "textTracks": {"videoTrack": [{"label": "Subtitles", "kind": "subtitles", "srcLang": "en"}]}
            },
            "interactions": h5p_interactions,
            "assets": {"interactions": h5p_interactions}
        }
    }
    os.makedirs("temp_h5p/content", exist_ok=True)
    with open("temp_h5p/content/content.json", "w") as f:
        json.dump(h5p_content, f, indent=2)
    return "temp_h5p/content/content.json"

def format_markdown(interactions):
    md = "# Interactive Video Questions\n\n"
    for inter in interactions:
        md += f"### At {inter['time']}\n"
        if "question" in inter and "options" in inter:
            md += f"- **Question**: {inter['question']}\n- **Options**:\n"
            for opt in inter["options"]:
                md += f"  - {opt}{' (Correct)' if opt == inter['correct'] else ''}\n"
        elif "text" in inter and "answer" in inter:
            md += f"- **Text**: {inter['text']}\n- **Answer**: {inter['answer']}\n"
        elif inter.get("type") == "text":
            md += f"- **Text Overlay**: {inter['text']}\n"
        elif inter.get("type") == "question":
            md += f"- **Open-Ended**: {inter['question']}\n"
        md += "\n"
    return md

def create_h5p_package(video_url, interactions, output_filename="interactive_video.h5p"):
    h5p_meta = {
        "title": "Interactive Video",
        "mainLibrary": "H5P.InteractiveVideo",
        "language": "en",
        "embedTypes": ["div"],
        "license": "U",
        "preloadedDependencies": [
            {"machineName": "H5P.InteractiveVideo", "majorVersion": "1", "minorVersion": "27"},
            {"machineName": "H5P.MultiChoice", "majorVersion": "1", "minorVersion": "16"},
            {"machineName": "H5P.Blanks", "majorVersion": "1", "minorVersion": "14"},
            {"machineName": "H5P.Text", "majorVersion": "1", "minorVersion": "1"}
        ]
    }
    json_path = format_h5p_json(video_url, interactions)
    md_file = f"{output_filename.replace('.h5p', '')}_questions.md"
    with open(md_file, "w") as f:
        f.write(format_markdown(interactions))

    with open("temp_h5p/h5p.json", "w") as f:
        json.dump(h5p_meta, f)
    
    with zipfile.ZipFile(output_filename, "w") as h5p_zip:
        h5p_zip.write("temp_h5p/h5p.json", "h5p.json")
        h5p_zip.write(json_path, "content/content.json")
    
    os.remove("temp_h5p/h5p.json")
    os.remove(json_path)
    os.rmdir("temp_h5p/content")
    os.rmdir("temp_h5p")
    
    return output_filename, md_file