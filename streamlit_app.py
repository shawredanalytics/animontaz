import streamlit as st
import os
import time
import requests
import subprocess
import random
import math
from datetime import datetime
import openai

# Set page config
st.set_page_config(
    page_title="Animontaz",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Anime Cyberpunk look
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #ff0055, #ff00aa);
        border: none;
        border-radius: 4px;
        color: white;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        width: 100%;
        padding: 0.75rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(255, 0, 85, 0.2);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 0, 85, 0.4);
        background: linear-gradient(90deg, #ff00aa, #ff0055);
    }

    /* Titles */
    h1 {
        font-family: 'Arial Black', sans-serif;
        background: linear-gradient(to right, #000000, #333333);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        font-size: 3.5rem !important;
        letter-spacing: -2px;
        margin-bottom: 0.5rem !important;
    }
    h3 {
        color: #ff0055 !important;
        font-weight: 300 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase;
        font-size: 1.2rem !important;
        margin-top: 0 !important;
        opacity: 0.9;
    }

    /* Text Input Area */
    .stTextArea textarea {
        background-color: #f5f5f5 !important;
        color: #000000 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        font-size: 1.1rem;
        transition: border-color 0.3s ease;
    }
    .stTextArea textarea:focus {
        border-color: #ff0055 !important;
        box-shadow: 0 0 10px rgba(255, 0, 85, 0.1) !important;
    }
    .stTextArea label {
        color: #333333 !important;
        font-weight: bold;
        letter-spacing: 1px;
    }

    /* File Uploader Customization */
    [data-testid="stFileUploader"] {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: #f8f9fa;
        border: 1px dashed #cccccc;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        background-color: #f0f0f0;
        border-color: #ff0055;
    }
    [data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }
    /* Force text color in uploader to be visible */
    [data-testid="stFileUploader"] small {
        color: #666666 !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #e0e0e0 !important;
        color: #000000 !important;
        border: none !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-color: #ff0055 transparent #ff00aa transparent !important;
    }

    /* Success/Error messages */
    .stAlert {
        background-color: #fff0f5;
        border: 1px solid #ff0055;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def download_file(url, filename):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return filename
    return None

def get_ffmpeg_path():
    # Check if ffmpeg is in PATH
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return "ffmpeg"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for local ffmpeg-static (common in local dev)
    local_ffmpeg = os.path.join(os.getcwd(), "server", "node_modules", "ffmpeg-static", "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
        
    return None

def generate_storyboard(prompt, api_key):
    if not api_key:
        return None
        
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert anime director. Create a sequence of 6 detailed visual scene descriptions for a short anime video based on the user's prompt. The scenes should flow logically to tell a mini-story. Output ONLY the 6 descriptions, one per line, without numbers or prefixes."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        scenes = [line.strip() for line in content.split('\n') if line.strip()]
        return scenes[:6]
    except Exception as e:
        st.error(f"ChatGPT Error: {str(e)}")
        return None

def generate_images_from_prompt(prompt, api_key=None):
    base_seed = random.randint(0, 1000000)
    
    scenes = []
    if api_key:
        with st.spinner("Consulting with AI Director (ChatGPT)..."):
            scenes = generate_storyboard(prompt, api_key)
            
    if not scenes:
        image_prompt = prompt.replace('"', '').replace('saying', '').replace('says', '').strip()
        # Fallback scenes
        suffixes = [
            "wide angle establishing shot, cinematic composition, highly detailed environment",
            "medium shot, dynamic action pose, intense gaze, detailed character design",
            "close up, detailed expression, dramatic lighting, anime masterpiece",
            "low angle shot, looking up at character, heroic stance, epic atmosphere",
            "side profile, emotional expression, wind blowing hair, cinematic lighting",
            "wide shot, battle ready pose, dynamic background, movie still quality"
        ]
        scenes = [f"{image_prompt}, {s}" for s in suffixes]
    
    image_urls = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, scene_desc in enumerate(scenes):
        status_text.text(f"Generating Scene {index + 1}/{len(scenes)}...")
        # Add character consistency tags
        full_prompt = f"anime style, masterpiece, best quality, 8k, cinematic lighting, detailed character design, {scene_desc}"
        encoded_prompt = requests.utils.quote(full_prompt)
        # Add negative prompt to avoid bad anatomy
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&seed={base_seed + index}&nologo=true&negative=bad%20anatomy,blurred,watermark,text,error,missing%20limbs"
        image_urls.append(url)
        progress_bar.progress((index + 1) / len(scenes))
        time.sleep(0.5) # Slight delay to be nice to the API
    
    status_text.empty()
    progress_bar.empty()
    return image_urls

def create_video_from_images(image_paths, audio_path, output_filename):
    duration_per_image = 3
    fps = 30
    total_frames = duration_per_image * fps
    
    ffmpeg_cmd = get_ffmpeg_path()
    if not ffmpeg_cmd:
        st.error("FFmpeg is not installed or not in PATH. Please install FFmpeg.")
        return None

    # Construct Filter Complex
    filter_complex = ""
    inputs = []
    
    # Add image inputs
    cmd = [ffmpeg_cmd, "-y"]
    
    for i, img_path in enumerate(image_paths):
        cmd.extend(["-loop", "1", "-framerate", str(fps), "-t", str(duration_per_image), "-i", img_path])
        
        # Zoom expression
        if i % 2 == 0:
            zoom_expr = "'min(zoom+0.005,2.0)'"
        else:
            zoom_expr = f"'2.0-on/({total_frames})'"
            
        filter_complex += f"[{i}:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,eq=saturation=1.3:contrast=1.1,zoompan=z={zoom_expr}:d={total_frames}:fps={fps}:x='iw/2-(iw/zoom/2)+sin(time*20)*5':y='ih/2-(ih/zoom/2)+cos(time*15)*5':s=1280x720,setsar=1[v{i}];"
        inputs.append(f"[v{i}]")

    # Add audio input
    if audio_path:
        video_duration = len(image_paths) * duration_per_image
        cmd.extend(["-i", audio_path, "-t", str(video_duration)])
    
    # Concat filter
    filter_complex += f"{''.join(inputs)}concat=n={len(image_paths)}:v=1:a=0[v]"
    
    cmd.extend(["-filter_complex", filter_complex])
    
    output_options = [
        "-map", "[v]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-crf", "28",
        "-preset", "veryfast",
        "-movflags", "+faststart"
    ]
    
    if audio_path:
        audio_index = len(image_paths)
        output_options.extend(["-map", f"{audio_index}:a", "-shortest"])
        
    cmd.extend(output_options)
    cmd.append(output_filename)
    
    # Run FFmpeg
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            st.error(f"FFmpeg Error: {stderr.decode()}")
            return None
        return output_filename
    except Exception as e:
        st.error(f"Error executing FFmpeg: {str(e)}")
        return None

# Main App UI
st.title("ANIMONTAZ")
st.markdown("### Create Your Own Anime Saga")

# Sidebar for API Key
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("OpenAI API Key (Optional)", type="password", help="Enter your OpenAI API Key to enable ChatGPT-powered storyboarding.")

col1, col2 = st.columns([1, 1])

with col1:
    prompt = st.text_area("Enter your prompt", placeholder="A cyberpunk samurai walking in the neon rain...", height=100)
    
    uploaded_images = st.file_uploader("Or Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    uploaded_audio = st.file_uploader("Add Background Music", type=['mp3', 'wav'])
    
    generate_btn = st.button("GENERATE VIDEO")

with col2:
    if generate_btn:
        if not prompt and not uploaded_images:
            st.warning("Please provide a prompt or upload images.")
        else:
            with st.spinner("Summoning your anime video..."):
                # Create a temporary directory for processing
                os.makedirs("temp_process", exist_ok=True)
                
                image_paths = []
                
                # 1. Handle Images
                if uploaded_images:
                    for i, img_file in enumerate(uploaded_images):
                        file_path = os.path.join("temp_process", f"upload_{i}.jpg")
                        with open(file_path, "wb") as f:
                            f.write(img_file.getbuffer())
                        image_paths.append(file_path)
                elif prompt:
                    image_urls = generate_images_from_prompt(prompt, api_key)
                    for i, url in enumerate(image_urls):
                        file_path = os.path.join("temp_process", f"gen_{i}.jpg")
                        if download_file(url, file_path):
                            image_paths.append(file_path)
                
                # 2. Handle Audio
                audio_path = None
                if uploaded_audio:
                    audio_path = os.path.join("temp_process", "input_audio.mp3")
                    with open(audio_path, "wb") as f:
                        f.write(uploaded_audio.getbuffer())
                
                # 3. Generate Video
                if image_paths:
                    output_video = f"output_{int(time.time())}.mp4"
                    result_path = create_video_from_images(image_paths, audio_path, output_video)
                    
                    if result_path and os.path.exists(result_path):
                        st.video(result_path)
                        
                        with open(result_path, "rb") as file:
                            st.download_button(
                                label="DOWNLOAD VIDEO",
                                data=file,
                                file_name="animontaz_video.mp4",
                                mime="video/mp4"
                            )
                        
                        # Cleanup
                        # os.remove(result_path) # Optional: Keep for debugging
                else:
                    st.error("Failed to process images.")

st.markdown("---")
st.markdown("Powered by Pollinations.ai & FFmpeg")
