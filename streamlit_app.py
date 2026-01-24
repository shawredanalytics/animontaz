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
def generate_storyboard(prompt, api_key, style_name="Anime"):
    system_instruction = f"You are an expert {style_name} illustrator. Create a detailed visual description for a high-quality illustration based on the user's prompt. Output ONLY the description, without any prefixes."
    
    if api_key:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].strip()
                return [content]
            else:
                st.warning(f"ChatGPT API Error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"ChatGPT Error: {str(e)}")
            return None
    else:
        # Use Pollinations.ai Text API if no OpenAI key is provided
        try:
            full_prompt = f"{system_instruction}\n\nUser Prompt: {prompt}"
            encoded_prompt = requests.utils.quote(full_prompt)
            # Use 'openai' model via Pollinations (free tier)
            url = f"https://text.pollinations.ai/{encoded_prompt}?model=openai"
            
            response = requests.get(url)
            if response.status_code == 200:
                content = response.text.strip()
                return [content]
            else:
                # Silent failure to fallback to raw prompt
                return None
        except Exception:
            return None

def generate_images_from_prompt(prompt, width, height, num_images, style_name, style_prompt, negative_prompt, seed, enhance_prompt, api_key=None):
    if seed == -1:
        base_seed = random.randint(0, 1000000)
    else:
        base_seed = seed
    
    scenes = []
    if enhance_prompt: # Use AI Illustrator (OpenAI or Pollinations)
        with st.spinner(f"Consulting with AI Illustrator ({style_name} Expert)..."):
            scenes = generate_storyboard(prompt, api_key, style_name)
            # Ensure we generate the requested number of images even if AI gives one description
            if scenes and len(scenes) == 1 and num_images > 1:
                scenes = scenes * num_images
            
    if not scenes:
        image_prompt = prompt.replace('"', '').replace('saying', '').replace('says', '').strip()
        # Fallback scenes are just the raw prompt
        scenes = [image_prompt] * num_images
    
    image_urls = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, scene_desc in enumerate(scenes):
        status_text.text(f"Generating Image {index + 1}/{len(scenes)}...")
        
        if enhance_prompt:
            # Construct the final prompt with style and quality boosters
            style_part = f"{style_prompt}, " if style_prompt else ""
            # Combine everything: Style keywords + Quality tags + Scene Description
            full_prompt = f"{style_part}masterpiece, best quality, 8k, cinematic lighting, detailed character design, {scene_desc}"
        else:
            # Raw prompt mode - just append style if selected, but no quality boosters
            style_part = f"{style_prompt}, " if style_prompt else ""
            full_prompt = f"{style_part}{scene_desc}"
        
        encoded_prompt = requests.utils.quote(full_prompt)
        encoded_negative = requests.utils.quote(negative_prompt)
        
        # Add negative prompt to avoid bad anatomy
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={base_seed + index}&nologo=true&negative={encoded_negative}"
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
    api_key = st.text_input("OpenAI API Key (Optional)", type="password", help="Enter your OpenAI API Key to enable ChatGPT-powered scene generation. If left blank, Pollinations AI (Free) will be used for both text and images.")
    
    st.markdown("### 🎨 Customization")
    
    style_option = st.selectbox(
        "Art Style",
        ["Default", "Cyberpunk", "Studio Ghibli", "Dark Fantasy", "90s Retro Anime", "Watercolor", "Manga (B&W)"],
        index=0
    )
    
    style_prompts = {
        "Default": "",
        "Cyberpunk": "neon lights, futuristic city, cybernetic enhancements, high tech, sci-fi atmosphere",
        "Studio Ghibli": "lush nature, vibrant colors, hand painted style, peaceful atmosphere, detailed background",
        "Dark Fantasy": "dark atmosphere, gothic architecture, dramatic shadows, mysterious, ethereal",
        "90s Retro Anime": "grainy texture, vintage anime style, cel shaded, 90s aesthetic, vhs glitch",
        "Watercolor": "watercolor painting style, soft edges, artistic, dreamy, pastel colors",
        "Manga (B&W)": "black and white, manga style, screentones, ink lines, dramatic shading"
    }
    
    col_w, col_h = st.columns(2)
    with col_w:
        width = st.number_input("Width", min_value=256, max_value=2048, value=1024, step=64)
    with col_h:
        height = st.number_input("Height", min_value=256, max_value=2048, value=1024, step=64)
        
    num_images = st.slider("Number of Images", min_value=1, max_value=4, value=1)

    with st.expander("Advanced Options"):
        seed = st.number_input("Seed (-1 for random)", value=-1, step=1)
        enhance_prompt = st.checkbox("Enhance Prompt (Quality Boosters)", value=True, help="If checked, adds 'masterpiece, best quality, 8k' etc. to your prompt. Uncheck for raw prompting.")
        negative_prompt = st.text_area("Negative Prompt (What to avoid)", value="bad anatomy, blurred, watermark, text, error, missing limbs, extra digits, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, username, blurry", height=100)

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
                image_urls = generate_images_from_prompt(prompt, width, height, num_images, style_option, style_prompts[style_option], negative_prompt, seed, enhance_prompt, api_key)
                
                if image_urls:
                    st.success(f"Generated {len(image_urls)} Anime Photos!")
                    
                    for i, url in enumerate(image_urls):
                        st.image(url, caption=f"Generated Anime Art #{i+1}", use_container_width=True)
                        
                        try:
                            response = requests.get(url)
                            if response.status_code == 200:
                                st.download_button(
                                    label=f"Download Image #{i+1}",
                                    data=response.content,
                                    file_name=f"animontaz_art_{i+1}.jpg",
                                    mime="image/jpeg",
                                    key=f"dl_{i}"
                                )
                        except Exception as e:
                            st.error(f"Could not load download button for image {i+1}")

st.markdown("---")
st.markdown("Powered by Pollinations.ai")
