# app.py
import streamlit as st
from core import get_frameworks
from addon import generate_interactions
from format import create_h5p_package
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
default_api_key = os.getenv("GROQ_API_KEY")

st.title("H5P Interactive Video Generator")
st.markdown("""
Turn your YouTube videos into interactive lessons for Moodle with ease!  
Enter a video URL and a manual summary, then choose a learning outcome and model to generate activities with Groq AI.
""")

st.sidebar.subheader("API Configuration")
api_key = st.sidebar.text_input("Groq API Key", value=default_api_key or "", type="password", key="groq_api_key_input")
if not api_key:
    st.sidebar.warning("Please provide a Groq API key (via .env or input).")
else:
    model_options = [
        "distil-whisper-large-v3-en", "gemma2-9b-it", "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant", "llama-guard-3-8b", "llama3-70b-8192",
        "llama3-8b-8192", "mixtral-8x7b-32768", "mistral-saba-24b",
        "qwen-2.5-coder-32b", "qwen-2.5-32b", "deepseek-r1-distill-qwen-32b",
        "deepseek-r1-distill-llama-70b-specdec", "deepseek-r1-distill-llama-70b"
    ]
    selected_model = st.sidebar.selectbox("Select LLM Model", model_options, index=model_options.index("llama3-70b-8192"), key="model_select")

st.subheader("Create Your Interactive Video")
video_url = st.text_input("Enter Your YouTube Video URL", value="https://youtu.be/bI9RZjF-538", key="video_url_input", help="Paste the full YouTube URL.")
summary = st.text_area("Enter Video Summary", value="", key="summary_input", height=300, help="Provide a summary with timestamps (e.g., [MM:SS]).")
frameworks = get_frameworks()
outcome = st.selectbox("Select Learning Outcome", frameworks, key="outcome_select", help="Choose the type of activities to generate.")
generate_button = st.button("Generate", key="generate_button")
clear_button = st.button("Clear", key="clear_button")

if clear_button:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    for file in ["interactive_video.h5p", "interactive_video.md"]:
        if os.path.exists(file):
            os.remove(file)
    if os.path.exists("temp_h5p"):
        for root, dirs, files in os.walk("temp_h5p", topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir("temp_h5p")
    st.rerun()

if generate_button and video_url and api_key and summary:
    with st.spinner("Processing your input..."):
        try:
            model = st.session_state.get("model_select", "llama3-70b-8192")
            interactions = generate_interactions(video_url, api_key, outcome, summary, model)
            if not interactions or len(interactions) == 0:
                st.error("Failed to generate interactions.")
                interactions = []
            
            st.write("### Preview Generated Interactions (First 2)")
            st.json(interactions[:2] if len(interactions) > 0 else interactions)
            st.write("### Full Interactions")
            st.json(interactions)
            
            h5p_file, md_file = create_h5p_package(video_url, interactions, "interactive_video.h5p")
            print(f"Generated files: {h5p_file}, {md_file}")
            st.session_state["h5p_file"] = h5p_file  # Fixed: Complete assignment
            st.session_state["md_file"] = md_file
            st.success("Generation complete! Download your files below!")
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.pop("h5p_file", None)
            st.session_state.pop("md_file", None)

if "h5p_file" in st.session_state and "md_file" in st.session_state:
    h5p_file = st.session_state["h5p_file"]
    md_file = st.session_state["md_file"]
    if os.path.exists(h5p_file) and os.path.exists(md_file):
        st.subheader("Download Your Files")
        col1, col2 = st.columns(2)
        with col1:
            with open(h5p_file, "rb") as f:
                st.download_button("Download H5P File", f, file_name=h5p_file, key="download_h5p")
        with col2:
            with open(md_file, "rb") as f:
                st.download_button("Download Markdown", f, file_name=md_file, key="download_md")
    else:
        st.warning("Generated files not found. Please regenerate.")
        st.session_state.pop("h5p_file", None)
        st.session_state.pop("md_file", None)

if video_url:
    st.subheader("Video Preview")
    st.video(video_url)