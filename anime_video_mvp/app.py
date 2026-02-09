import gradio as gr
import os
import torch
from animate import AnimeAnimator

# Global model instance
animator = None

def load_model():
    global animator
    if animator is None:
        print("Loading AI Model (this may take a minute)...")
        animator = AnimeAnimator()
    return animator

def generate_video(image_path, prompt, progress=gr.Progress()):
    if not image_path:
        return None
    
    try:
        model = load_model()
        
        # Default prompt engineering if user leaves it empty
        if not prompt:
            prompt = "1girl, cute, smiling, looking at viewer, solo, upper body"
            
        # Adjust settings for CPU
        is_cpu = model.device == "cpu"
        num_frames = 8 if is_cpu else 24
        steps = 10 if is_cpu else 25
        
        if is_cpu:
            gr.Info(f"CPU Mode: Generating {num_frames} frames with {steps} steps (Faster preview mode)")
            
        def progress_wrapper(step, total):
            progress((step, total), desc=f"Denoising step {step}/{total}")
            
        output_video = model.generate(
            image_path=image_path,
            prompt=prompt,
            num_frames=num_frames, 
            strength=0.8,
            steps=steps,
            progress_callback=progress_wrapper
        )
        return output_video
    except Exception as e:
        raise gr.Error(f"Generation Failed: {str(e)}")

# UI Layout
with gr.Blocks(title="Animontaz Video MVP") as demo:
    gr.Markdown(
        """
        # 🎬 Animontaz Video Generator (MVP)
        Turn your anime images into short video loops using **AnimateDiff**.
        """
    )

    if not torch.cuda.is_available():
        gr.Markdown("⚠️ **WARNING: CUDA GPU not detected.** Running on CPU. Video generation will be extremely slow (several minutes).", elem_classes=["error-message"])
    
    with gr.Row():
        with gr.Column():
            input_image = gr.Image(label="Upload Anime Image", type="filepath", height=400)
            prompt_input = gr.Textbox(
                label="Prompt (Optional)", 
                placeholder="Describe the character (e.g., '1girl, smiling, wind blowing hair')",
                lines=2
            )
            generate_btn = gr.Button("✨ Generate Video", variant="primary", size="lg")
            
            with gr.Accordion("Technical Details", open=False):
                gr.Markdown(
                    """
                    - **Model:** Lykon/DreamShaper (SD 1.5)
                    - **Motion:** AnimateDiff v1.5.2
                    - **Frames:** 24 frames
                    - **FPS:** 8 FPS (Anime style)
                    - **Strength:** 0.8 (High fidelity to original image)
                    """
                )
        
        with gr.Column():
            output_video = gr.Video(label="Generated Animation", height=400, autoplay=True)
            
    generate_btn.click(
        fn=generate_video,
        inputs=[input_image, prompt_input],
        outputs=[output_video]
    )

if __name__ == "__main__":
    # Ensure CUDA is available for best performance
    if not torch.cuda.is_available():
        print("WARNING: CUDA not found. Running on CPU will be extremely slow.")
        
    demo.launch(share=True)
