# H5P Interactive Video Generator v2

Welcome to **H5P Interactive Video Generator v2**! This Streamlit app uses Groq AI to turn YouTube video summaries into interactive H5P lessons for Moodle. Drop in a summary, pick a learning outcome (e.g., comprehension, application), choose a model, and bam—get questions and activities in H5P and Markdown format. Perfect for educators or anyone wanting to spice up video content!

## What’s New in v2 - Python_Streamlit Scripts
- **Manual Summaries**: You provide the video summary—no more guessing from URLs.
- **Groq Models**: Pick from a dropdown of production (e.g., `llama3-70b-8192`) and preview models (e.g., `qwen-2.5-32b`).
- **.env Support**: Store your Groq API key securely.
- **Learning Outcomes**: Generate 5 MCQs (comprehension), 3 fill-ins (application), and more with a single click.
- **Streamlit 1.38.0**: Latest version for a smooth ride.

  ## What’s New in v2 - windows release
  - **v1.0.0-beta**: [Download here](https://github.com/dgcruzing/H5P-Interactive-Video-Generator-v2/releases/tag/v1.0.0-beta).

## Python Quickstart for Newbies

### Prerequisites
- **Python 3.9+**: [Download here](https://www.python.org/downloads/).
- **pip**: Comes with Python—use it to install stuff.
- **A Groq API Key**: Sign up at [console.groq.com](https://console.groq.com) to get one.

### Step 1: Clone the Repo
Grab the code:
```bash
git clone https://github.com/yourusername/H5P-Interactive-Video-Generator-v2.git
cd H5P-Interactive-Video-Generator-v2
```

### Step 2: Set Up Your Environment
Create a virtual environment (keeps things tidy):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
Install the required packages:
```bash
pip install -r requirements.txt
```

### Step 4: Add Your Groq API Key
Create a `.env` file in the root folder:
```plaintext
# .env
GROQ_API_KEY=gsk_your_key_here
```
Replace `gsk_your_key_here` with your actual key. If you skip this, you can enter it in the app later.

### Step 5: Run the App
Launch it:
```bash
python -m streamlit run app.py
```
Your browser should open to `http://localhost:8501`.

### Step 6: Use It!
1. **API Key**: Loads from `.env` or type it in the sidebar.
2. **Model**: Pick one (e.g., `llama3-70b-8192`) from the dropdown.
3. **Video URL**: Enter a YouTube URL (e.g., `https://youtu.be/bI9RZjF-538`).
4. **Summary**: Paste a summary with timestamps (e.g., "HRM is... [00:51]").
5. **Outcome**: Choose "comprehension" for 5 MCQs, "application" for 3 fill-ins, etc.
6. **Generate**: Click "Generate" and download your H5P/Markdown files!

## Example Summary
Try this HRM summary:
```
The video explains human resource management (HRM)... [00:51]. It involves... human capital [01:18]. History: HRM evolved... World Wars [02:38]...
```

## Files
- `app.py`: Main app with UI and logic.
- `core.py`: Groq API and prompt database.
- `addon.py`: Generates interactions from summaries.
- `format.py`: Creates H5P and Markdown outputs.
- `.env`: Stores your API key (don’t share this!).
- `requirements.txt`: Lists dependencies.
```
H5P-Interactive-Video-Generator-v2/
├── .env                # Your Groq API key (not tracked by git)
├── .gitignore          # Ignores .env and temp files
├── app.py              # Main Streamlit app
├── core.py             # Groq API and prompt database
├── addon.py            # Generates interactions from summaries
├── format.py           # Creates H5P and Markdown outputs
├── requirements.txt    # Python dependencies (Streamlit, Groq, etc.)
├── prompt_frameworks.db  # SQLite DB for prompts (auto-generated)
├── groq_response.txt   # Debug output from Groq API
├── interactive_video.h5p  # Generated H5P file
└── interactive_video.md  # Generated Markdown file
```
## Troubleshooting
- **No API Key?**: Check `.env` or enter it manually.
- **Errors?**: Ensure all files are in place and dependencies installed.
- **Stuck?**: Hit "Clear" in the app to reset.

## Contributing
New to Python? Fork this, tweak it, and send a pull request! Ideas welcome.

## Thanks
Powered by Groq AI and Streamlit—big props to their teams!
## Thanks
Powered by Groq AI and Streamlit—big props to their teams!
