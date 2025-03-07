# format.py
import json
import os
import zipfile

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
        if "question" in inter and "options" in inter:  # Multiple Choice
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
        elif "text" in inter and "answer" in inter:  # Fill in the Blanks
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
        elif inter.get("type") == "text":  # Text Overlay
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
        elif inter.get("type") == "question":  # Open-ended (as text)
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
            md += f"- **Fill in the Blank**: {inter['text']}\n- **Answer**: {inter['answer']}\n"
        elif inter.get("type") == "text":
            md += f"- **Text Overlay**: {inter['text']}\n"
        elif inter.get("type") == "question":
            md += f"- **Open-Ended**: {inter['question']}\n"
        md += "\n"
    return md

def create_h5p_package(video_url, interactions, output_file="interactive_video.h5p"):
    print(f"Creating H5P package for video: {video_url}")
    print(f"Number of interactions: {len(interactions)}")
    
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
    md_file = output_file.replace('.h5p', '.md')
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(format_markdown(interactions))  # Use format_markdown directly
    
    with open("temp_h5p/h5p.json", "w") as f:
        json.dump(h5p_meta, f)
    
    with zipfile.ZipFile(output_file, "w") as h5p_zip:
        h5p_zip.write("temp_h5p/h5p.json", "h5p.json")
        h5p_zip.write(json_path, "content/content.json")
    
    os.remove("temp_h5p/h5p.json")
    os.remove(json_path)
    os.rmdir("temp_h5p/content")
    os.rmdir("temp_h5p")
    
    print(f"Successfully created H5P file: {output_file}")
    print(f"Successfully created Markdown file: {md_file}")
    return output_file, md_file