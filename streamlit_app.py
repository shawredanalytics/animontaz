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

# Custom CSS for Cartoon look
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

def generate_with_stable_horde(prompt, width, height, model_name, negative_prompt, api_key="0000000000"):
    """
    Generates an image using the Stable Horde API (Async/Polling).
    """
    url_generate = "https://stablehorde.net/api/v2/generate/async"
    headers = {
        "apikey": api_key,
        "Client-Agent": "Animontaz:1.0:user",
        "Content-Type": "application/json"
    }
    
    # Stable Horde uses '###' to separate positive and negative prompts
    final_prompt = f"{prompt} ### {negative_prompt}"
    
    payload = {
        "prompt": final_prompt,
        "params": {
            "sampler_name": "k_euler_a",
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "steps": 30,
            "n": 1
        },
        "nsfw": True, # Allow artistic freedom (needed for many anime models)
        "censor_nsfw": False,
        "models": [model_name]
    }
    
    try:
        # 1. Submit Request
        response = requests.post(url_generate, headers=headers, json=payload)
        if response.status_code != 202:
            st.error(f"Stable Horde Error: {response.text}")
            return None
            
        request_id = response.json()['id']
        
        # 2. Poll for Status
        status_url = f"https://stablehorde.net/api/v2/generate/status/{request_id}"
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        while True:
            stat_res = requests.get(status_url)
            if stat_res.status_code != 200:
                time.sleep(1)
                continue
                
            stat_data = stat_res.json()
            
            if stat_data['done']:
                progress_bar.progress(1.0)
                status_text.text("Generation Complete!")
                break
                
            if stat_data['faulted']:
                st.error("Generation failed on Stable Horde.")
                return None
            
            # Update progress
            wait_time = stat_data.get('wait_time', 0)
            queue_pos = stat_data.get('queue_position', 0)
            status_text.text(f"Queue Position: {queue_pos} | Est. Wait: {wait_time}s")
            
            time.sleep(2) # Poll every 2 seconds
            
        # 3. Get Image URL
        if stat_data['generations']:
            img_url = stat_data['generations'][0]['img']
            return img_url
        return None
        
    except Exception as e:
        st.error(f"Stable Horde Exception: {str(e)}")
        return None

def create_gumroad_product(api_key, name, description, price, tags, image_url=None):
    try:
        url = "https://api.gumroad.com/v2/products"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Step 1: Create Product (Metadata)
        data = {
            "name": name,
            "description": description,
            "price": int(price * 100), # cents
            "currency": "usd",
            "tags": tags
        }
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            product_data = response.json()['product']
            product_url = product_data['short_url']
            product_id = product_data['id']
            
            # Step 2: Upload Cover Image (if available)
            if image_url:
                # Note: Gumroad doesn't have a simple public API endpoint for cover upload on created products easily.
                # However, many users report success by passing files in the initial request or using undocumented endpoints.
                # Since the previous attempt failed, let's try a safer approach:
                # Just return the product URL and let the user upload the cover manually for reliability.
                # OR retry the initial request with files properly if we want to be persistent.
                pass 
                
            return {'short_url': product_url, 'id': product_id}
        else:
            st.error(f"Gumroad API Error ({response.status_code}): {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def generate_images_from_prompt(prompt, width, height, num_images, style_name, style_prompt, negative_prompt, seed, enhance_prompt, format_option, api_key=None, generation_source="Pollinations AI (Fast)", horde_api_key="0000000000", horde_model="DreamShaper"):
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
    
    # Define Format Keywords
    format_keywords = ""
    if "Sticker" in format_option:
        format_keywords = "die-cut sticker, white background, vector style, cute, simple, distinct outline"
    elif "T-Shirt" in format_option:
        format_keywords = "t-shirt design, vector art, isolated on black background, clean lines, high contrast, screen print style"
    elif "Poster" in format_option:
        format_keywords = "high detailed poster, wall art, 8k resolution, cinematic composition, highly detailed, sharp focus"
    elif "Character Design" in format_option:
        format_keywords = "character design sheet, full body, multiple views, concept art, reference sheet, white background"
    
    for index, scene_desc in enumerate(scenes):
        status_text.text(f"Generating Image {index + 1}/{len(scenes)}...")
        
        if enhance_prompt:
            # Construct the final prompt with style and quality boosters
            style_part = f"{style_prompt}, " if style_prompt else ""
            
            # Determine quality boosters based on style
            if "Disney" in style_name or "3D" in style_name:
                quality_boosters = "masterpiece, best quality, 8k, cinematic lighting, 3d render, unreal engine, detailed character design"
            elif "Classic" in style_name or "Retro" in style_name:
                quality_boosters = "high quality, detailed, vibrant colors, clean lines, 2d animation style"
            elif "Modern" in style_name:
                quality_boosters = "high quality, sharp vector art, bold colors, modern design"
            elif "Comic" in style_name or "Pop Art" in style_name:
                quality_boosters = "detailed ink work, halftone patterns, bold lines, dynamic shading"
            elif "Claymation" in style_name:
                quality_boosters = "clay texture, stop motion look, handmade feel, depth of field"
            elif "Oil Painting" in style_name:
                quality_boosters = "oil painting texture, visible brushstrokes, canvas texture, masterpiece, classic art"
            elif "Concept Art" in style_name or "Cyberpunk" in style_name:
                quality_boosters = "digital concept art, trending on artstation, highly detailed, intricate, cinematic"
            elif "Realistic" in style_name:
                quality_boosters = "photorealistic, hyperrealistic, 8k, highly detailed, sharp focus, professional photography"
            else:
                # Default
                quality_boosters = "high quality, detailed, vibrant, expressive, digital art"

            # Combine everything: Style + Quality + Format + Scene
            full_prompt = f"{style_part}{quality_boosters}, {format_keywords}, {scene_desc}"
        else:
            # Raw prompt mode - just append style if selected, but no quality boosters
            style_part = f"{style_prompt}, " if style_prompt else ""
            full_prompt = f"{style_part}{format_keywords}, {scene_desc}"
        
        # Clean up commas
        full_prompt = full_prompt.replace(", ,", ",").strip(", ")
        
        if generation_source == "Pollinations AI (Fast)":
            encoded_prompt = requests.utils.quote(full_prompt)
            encoded_negative = requests.utils.quote(negative_prompt)
            
            # Add negative prompt to avoid bad anatomy
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={base_seed + index}&nologo=true&negative={encoded_negative}"
            image_urls.append(url)
            time.sleep(0.5) # Slight delay to be nice to the API
            
        elif generation_source == "Stable Horde (Specific Models)":
            # Call Stable Horde
            status_text.text(f"Queueing Image {index + 1}/{len(scenes)} on Stable Horde ({horde_model})...")
            img_url = generate_with_stable_horde(full_prompt, width, height, horde_model, negative_prompt, horde_api_key)
            if img_url:
                image_urls.append(img_url)
            else:
                st.warning(f"Failed to generate image {index+1} via Stable Horde.")
        
        progress_bar.progress((index + 1) / len(scenes))
    
    status_text.empty()
    progress_bar.empty()
    return image_urls

# Main App UI
st.title("ANIMONTAZ")
st.markdown("### AI Digital Art & Cartoon Studio")

# Sidebar for API Key
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("OpenAI API Key (Optional)", type="password", help="Enter your OpenAI API Key to enable ChatGPT-powered scene generation. If left blank, Pollinations AI (Free) will be used for both text and images.")
    
    generation_source = st.selectbox(
        "Image Generation Source",
        ["Pollinations AI (Fast)", "Stable Horde (Specific Models)"],
        help="Choose 'Pollinations AI' for speed, or 'Stable Horde' to use specific models (slower, but more control)."
    )
    
    horde_api_key = "0000000000"
    horde_model = "DreamShaper"
    
    if generation_source == "Stable Horde (Specific Models)":
        horde_api_key = st.text_input("Stable Horde API Key (Optional)", value="0000000000", type="password", help="Register at stablehorde.net for a key to get faster generation. '0000000000' is anonymous.")
        horde_model = st.selectbox(
            "Model Selection",
            ["DreamShaper", "Deliberate", "Stable Diffusion XL", "ToonYou", "Disney Pixar Cartoon Type B", "Anything Diffusion", "CyberRealistic", "Rev Animated"],
            index=0
        )
    
    st.markdown("### � Store Integration")
    gumroad_access_token = st.text_input("Gumroad Access Token (Optional)", type="password", help="Enter your Gumroad Access Token to automatically draft products.")
    
    st.markdown("### �� Art Direction")
    
    format_option = st.selectbox(
        "Output Format (Commercial Use)",
        [
            "Standard Digital Art",
            "Sticker Design (Die-cut, White BG)",
            "T-Shirt Design (Isolated, Vector)",
            "Wall Art / Poster (High Detail)",
            "Character Design (Full Body Sheet)"
        ],
        index=0,
        help="Optimizes the prompt for specific selling formats."
    )
    
    style_option = st.selectbox(
        "Art Style",
        [
            "Disney / Pixar 3D",
            "Classic Cartoon (2D)",
            "Modern Cartoon",
            "Comic Book",
            "Claymation",
            "Vector Art",
            "3D Animation",
            "Oil Painting",
            "Watercolor",
            "Cyberpunk / Synthwave",
            "Concept Art",
            "Pop Art",
            "Realistic Portrait",
            "Surrealism"
        ],
        index=0
    )
    
    style_prompts = {
        "Disney / Pixar 3D": "3d render, pixar style, disney style, cgsociety, unreal engine 5, cute, expressive, smooth",
        "Classic Cartoon (2D)": "flat color, thick outlines, 1990s cartoon style, hanna barbera style, vibrant, funny",
        "Modern Cartoon": "calarts style, adventure time style, vector art, flat design, bright colors, simple",
        "Comic Book": "comic book style, marvel style, dc style, bold lines, dynamic action, halftone patterns",
        "Claymation": "claymation style, aardman style, stop motion, plasticine, textured, handmade",
        "Vector Art": "vector art, adobe illustrator, flat design, minimal, clean, sharp",
        "3D Animation": "3d character, blender render, maya, cute 3d art, stylized 3d",
        "Oil Painting": "oil painting, thick impasto, palette knife, classic art style, textured",
        "Watercolor": "watercolor painting, soft edges, wet on wet, artistic, dreamy, pastel colors",
        "Cyberpunk / Synthwave": "cyberpunk, synthwave, neon lights, futuristic, retro sci-fi, high tech, glowing",
        "Concept Art": "digital concept art, highly detailed, atmospheric, epic scale, trending on artstation",
        "Pop Art": "pop art style, warhol style, bright colors, repetition, bold contrast, retro",
        "Realistic Portrait": "professional portrait, studio lighting, bokeh, 85mm lens, sharp focus, skin texture",
        "Surrealism": "surreal art, dreamlike, dali style, impossible geometry, ethereal, mysterious"
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
        negative_prompt = st.text_area("Negative Prompt (What to avoid)", value="bad anatomy, blurred, watermark, text, error, missing limbs, extra digits, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, username, blurry, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, ugly, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck", height=100)

col1, col2 = st.columns([1, 1])

with col1:
    prompt = st.text_area("Enter your prompt", placeholder="A majestic lion wearing a crown, galaxy background...", height=100)
    generate_btn = st.button("GENERATE DIGITAL ART")

with col2:
    if generate_btn:
        if not prompt:
            st.warning("Please provide a prompt.")
        else:
            with st.spinner("Creating your masterpiece..."):
                image_urls = generate_images_from_prompt(prompt, width, height, num_images, style_option, style_prompts[style_option], negative_prompt, seed, enhance_prompt, format_option, api_key, generation_source, horde_api_key, horde_model)
                
                if image_urls:
                    st.success(f"Generated {len(image_urls)} Artworks!")
                    
                    for i, url in enumerate(image_urls):
                        st.image(url, caption=f"Generated Art #{i+1}", use_container_width=True)
                        
                        try:
                            response = requests.get(url)
                            if response.status_code == 200:
                                st.download_button(
                                    label=f"Download Art #{i+1}",
                                    data=response.content,
                                    file_name=f"animontaz_art_{i+1}.jpg",
                                    mime="image/jpeg",
                                    key=f"dl_{i}"
                                )
                        except Exception as e:
                            st.error(f"Could not load download button for image {i+1}")

                        # Store Integration
                        with st.expander(f"💰 Sell Art #{i+1}"):
                            st.markdown("#### 📝 Product Details")
                            
                            default_title = f"{format_option} - {style_option} #{i+1}"
                            p_title = st.text_input("Title", value=default_title, key=f"title_{i}")
                            
                            default_desc = f"**Format:** {format_option}\n**Style:** {style_option}\n**Prompt:** {prompt}\n\nHigh-resolution digital artwork created with Animontaz."
                            p_desc = st.text_area("Description", value=default_desc, key=f"desc_{i}")
                            
                            p_price = st.number_input("Price ($)", value=4.99, step=0.5, key=f"price_{i}")
                            
                            if gumroad_access_token:
                                if st.button(f"🚀 Draft on Gumroad", key=f"gum_btn_{i}"):
                                    with st.spinner("Creating product on Gumroad..."):
                                        # Generate tags based on style and format
                                        tags = f"{style_option}, {format_option}, Digital Art, AI Art, Animontaz"
                                        result = create_gumroad_product(gumroad_access_token, p_title, p_desc, p_price, tags, url)
                                        
                                        if result:
                                            product_url = result['short_url']
                                            product_id = result['id']
                                            edit_url = f"https://gumroad.com/products/{product_id}/edit"
                                            
                                            st.success(f"Product Created Successfully!")
                                            st.balloons()
                                            
                                            # Large call to action button to open Gumroad
                                            st.markdown(f"""
                                                <a href="{edit_url}" target="_blank" style="text-decoration: none;">
                                                    <div style="background-color: #ff0055; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                                        🚀 CLICK HERE TO FINISH ON GUMROAD
                                                    </div>
                                                </a>
                                            """, unsafe_allow_html=True)
                                            
                                            st.info("Product drafted! Click the button above to upload your image and publish.")
                            else:
                                st.info("💡 Enter your Gumroad Access Token in the sidebar to automatically create products.")
                                
                            st.markdown("#### 🌐 Other Platforms")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.markdown("[Redbubble Upload](https://www.redbubble.com/portfolio/images/new)")
                            with c2:
                                st.markdown("[Teespring Launcher](https://teespring.com/dashboard/campaigns)")
                            with c3:
                                st.markdown("[Etsy Shop](https://www.etsy.com/your/shops/me/dashboard)")

st.markdown("---")
st.markdown("Powered by Pollinations.ai & Stable Horde")
