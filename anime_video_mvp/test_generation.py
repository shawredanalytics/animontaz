import torch
from animate import AnimeAnimator
from PIL import Image
import os

def test_generation():
    print("Creating dummy image...")
    img = Image.new('RGB', (512, 512), color = 'red')
    img_path = "test_image.png"
    img.save(img_path)

    print("Initializing Animator...")
    try:
        animator = AnimeAnimator()
    except Exception as e:
        print(f"FAILED to initialize: {e}")
        return

    print("Generating video...")
    try:
        # Generate only 4 frames to be quick
        output = animator.generate(img_path, "1girl, smiling", num_frames=4, steps=10)
        print(f"SUCCESS! Video generated at: {output}")
    except Exception as e:
        print(f"FAILED to generate: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()
