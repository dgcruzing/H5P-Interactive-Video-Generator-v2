# addon.py
from core import call_groq, get_prompt_by_name

def generate_interactions(video_url, api_key, framework, summary, model="llama3-70b-8192"):
    if "youtu.be" in video_url:
        video_id = video_url.split("/")[-1].split("?")[0]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    prompt_template = get_prompt_by_name(framework)
    if not prompt_template:
        print(f"Warning: No prompt template for framework: {framework}")
        return []
    
    messages = [
        {"role": "system", "content": prompt_template.replace("{{SUMMARY}}", "").strip()},
        {"role": "user", "content": f"Summary: {summary}"}
    ]
    
    print(f"Generating interactions with framework: {framework}")
    print(f"Summary length: {len(summary)} characters")
    print(f"Using model: {model}")
    interactions = call_groq(messages, api_key, "groq_response.txt", model)
    return interactions