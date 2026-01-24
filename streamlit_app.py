import streamlit as st
import time
import requests
import random

# Set page config
st.set_page_config(
    page_title="Animontaz",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

try:
    import openai
except ImportError:
    openai = None

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
def generate_storyboard(prompt, api_key):
    if not api_key:
        return None
        
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an expert anime illustrator. Create a sequence of 6 detailed visual scene descriptions for a series of anime illustrations based on the user's prompt. The scenes should flow logically to tell a visual story. Output ONLY the 6 descriptions, one per line, without numbers or prefixes."},
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            scenes = [line.strip() for line in content.split('\n') if line.strip()]
            return scenes[:6]
        else:
            st.warning(f"ChatGPT API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"ChatGPT Error: {str(e)}")
        return None

def generate_images_from_prompt(prompt, api_key=None):
    base_seed = random.randint(0, 1000000)
    
    scenes = []
    if api_key:
        with st.spinner("Consulting with AI Illustrator (ChatGPT)..."):
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

# Main App UI
st.title("ANIMONTAZ")
st.markdown("### AI Anime Image Generator")

# Sidebar for API Key
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("OpenAI API Key (Optional)", type="password", help="Enter your OpenAI API Key to enable ChatGPT-powered scene generation.")

col1, col2 = st.columns([1, 1])

with col1:
    prompt = st.text_area("Enter your prompt", placeholder="A cyberpunk samurai walking in the neon rain...", height=100)
    generate_btn = st.button("GENERATE ANIME PHOTOS")

with col2:
    if generate_btn:
        if not prompt:
            st.warning("Please provide a prompt.")
        else:
            with st.spinner("Summoning your anime photos..."):
                image_urls = generate_images_from_prompt(prompt, api_key)
                
                if image_urls:
                    st.success(f"Generated {len(image_urls)} Anime Photos!")
                    
                    # Display images in a grid
                    for i, url in enumerate(image_urls):
                        st.image(url, caption=f"Scene {i+1}", use_container_width=True)
                        
                        # Add download button for each image
                        try:
                            response = requests.get(url)
                            if response.status_code == 200:
                                st.download_button(
                                    label=f"Download Image {i+1}",
                                    data=response.content,
                                    file_name=f"animontaz_scene_{i+1}.jpg",
                                    mime="image/jpeg"
                                )
                        except Exception as e:
                            st.error(f"Could not load download button for image {i+1}")

st.markdown("---")
st.markdown("Powered by Pollinations.ai")
