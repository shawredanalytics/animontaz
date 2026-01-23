import streamlit as st
import os
import time
import requests
import subprocess
import random
import math
from datetime import datetime

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
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    .stButton>button {
        background: linear-gradient(45deg, #ff0055, #00ffff);
        border: none;
        color: white;
        font-weight: bold;
        letter-spacing: 2px;
        text-transform: uppercase;
        width: 100%;
        padding: 0.5rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.5);
    }
    h1 {
        font-family: 'Arial Black', sans-serif;
        background: linear-gradient(to right, #fff, #888);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: -2px;
    }
    .css-1d391kg {
        background-color: rgba(20, 20, 20, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 20px;
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

def generate_images_from_prompt(prompt):
    image_prompt = prompt.replace('"', '').replace('saying', '').replace('says', '').strip()
    base_seed = random.randint(0, 1000000)
    scenes = [
        "wide angle establishing shot, cinematic composition",
        "medium shot, dynamic action pose",
        "close up, detailed expression, dramatic lighting",
        "dynamic angle, intense atmosphere, movie still"
    ]
    
    image_urls = []
    for index, scene_desc in enumerate(scenes):
        full_prompt = f"anime style, masterpiece, best quality, 8k, cinematic lighting, detailed character design, {image_prompt}, {scene_desc}"
        encoded_prompt = requests.utils.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&seed={base_seed + index}&nologo=true"
        image_urls.append(url)
    
    return image_urls

def create_video_from_images(image_paths, audio_path, output_filename):
    duration_per_image = 3
    fps = 30
    total_frames = duration_per_image * fps
    
    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        st.error("FFmpeg is not installed or not in PATH. Please install FFmpeg.")
        return None

    # Construct Filter Complex
    filter_complex = ""
    inputs = []
    
    # Add image inputs
    cmd = ["ffmpeg", "-y"]
    
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
                    image_urls = generate_images_from_prompt(prompt)
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
