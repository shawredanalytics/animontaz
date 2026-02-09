import torch
from diffusers import AnimateDiffVideoToVideoPipeline, MotionAdapter, EulerAncestralDiscreteScheduler
from diffusers.utils import export_to_video
from PIL import Image
import numpy as np
import os

class AnimeAnimator:
    def __init__(self):
        print("Initializing AnimeAnimator...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        print(f"Device: {self.device}, Dtype: {self.dtype}")
        
        try:
            # 1. Load Motion Adapter (The 'brain' of movement)
            print("Loading Motion Adapter...")
            self.adapter = MotionAdapter.from_pretrained(
                "guoyww/animatediff-motion-adapter-v1-5-2", 
                torch_dtype=self.dtype
            )
            
            # 2. Load Pipeline (Video-to-Video allow us to start from an image)
            # We use DreamShaper 8 as the base model for high-quality anime/art style
            print("Loading AnimateDiff Video Pipeline (DreamShaper)...")
            self.pipe = AnimateDiffVideoToVideoPipeline.from_pretrained(
                "Lykon/DreamShaper",
                motion_adapter=self.adapter,
                torch_dtype=self.dtype
            )
            
            # 3. Set Scheduler (Euler A is standard for AnimateDiff)
            self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
                self.pipe.scheduler.config, 
                timestep_spacing="trailing",
                beta_schedule="linear"
            )
            
            # 4. Optimizations for 8GB VRAM
            # These are CRITICAL for running on consumer GPUs
            print("Enabling VRAM optimizations...")
            self.pipe.enable_vae_slicing()
            
            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload() # Moves unused models to CPU
            else:
                # If on CPU, we don't need offloading, but we might want sequential offloading if RAM is tight
                # But for now, just keep it simple.
                pass
            
            print("Model loaded successfully!")
            
        except Exception as e:
            print(f"Error initializing model: {e}")
            raise e

    def preprocess_image(self, image_path, width=512, height=512):
        """Loads and resizes the image to 512x512 (standard for SD 1.5 AnimateDiff)."""
        image = Image.open(image_path).convert("RGB")
        image = image.resize((width, height), resample=Image.LANCZOS)
        return image

    def generate(self, image_path, prompt, num_frames=24, strength=0.8, guidance_scale=7.5, steps=25, progress_callback=None):
        """
        Generates a video from a single image.
        
        Args:
            image_path (str): Path to input image.
            prompt (str): Text prompt to guide the animation.
            num_frames (int): Number of frames (16, 24, 32 recommended).
            strength (float): 0.0 to 1.0. Lower = closer to original image, Higher = more motion/hallucination.
            progress_callback: Optional function(step, total_steps) to report progress.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Prepare Input
        init_image = self.preprocess_image(image_path)
        video_input = [init_image] * num_frames
        
        # Enhanced Prompt for Anime
        positive_prompt = (
            f"{prompt}, masterpiece, best quality, highres, anime style, "
            "subtle breathing, slight head movement, wind blowing hair, "
            "cinematic lighting, detailed background"
        )
        
        negative_prompt = (
            "bad quality, worse quality, low resolution, static, motionless, "
            "deformed, distorted, disfigured, bad anatomy, extra limbs, "
            "watermark, text, error"
        )
        
        print(f"Generating {num_frames} frames with prompt: {prompt}")
        
        # Run Pipeline
        generator = torch.Generator(device="cpu").manual_seed(42)
        
        def callback_fn(step, timestep, latents):
            if progress_callback:
                progress_callback(step, steps)
            return latents

        output = self.pipe(
            video=video_input,
            prompt=positive_prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            strength=strength,
            generator=generator
        )
        
        frames = output.frames[0]
        
        # Save Video
        output_path = "output.mp4"
        export_to_video(frames, output_path, fps=8) # 8 FPS gives a nice "anime" feel (on twos/threes)
        
        print(f"Video saved to {output_path}")
        return output_path

if __name__ == "__main__":
    # Simple test
    print("Run app.py to start the UI.")
