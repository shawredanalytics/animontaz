# Animontaz Video Generator (MVP)

A simple, local AI tool to convert static anime images into short, looping videos using **AnimateDiff**.

## 🚀 Features
- **Image-to-Video:** Upload a PNG/JPG and watch it come to life.
- **Anime Optimized:** Tuned for "breathing" and subtle character motion.
- **Hybrid Processing:** Run locally on your GPU or in the cloud via Google Colab.
- **Tech Stack:** Python, PyTorch, Diffusers, AnimateDiff, Gradio.

## ☁️ Cloud GPU (Recommended for non-NVIDIA users)
If you don't have a powerful NVIDIA GPU locally, you can run this tool for free on Google Colab.

**Option 1: Use the provided Notebook file**
1.  Download the `Animontaz_Colab.ipynb` file from this directory.
2.  Go to [Google Colab](https://colab.research.google.com/).
3.  Click **Upload** and select the file.

**Option 2: Use your existing Colab Notebook**
If you already have a notebook (like [this one](https://colab.research.google.com/drive/1PjSeT_UkgwpNeNSUt3LOaWa6mtJ7-P7u#scrollTo=rAu25GrpAgUO)), simply copy the code from `Animontaz_Colab.ipynb` into it.

**Steps to Connect:**
1.  In Colab, go to **Runtime > Change runtime type** and select **T4 GPU**.
2.  Run all cells.
3.  Look for the output line: `Running on public URL: https://xxxx.gradio.live`
4.  Copy that URL.
5.  Paste it into the **Anime Video** tab in the local Animontaz app.

## 🛠 Prerequisites (Local Run)
- **NVIDIA GPU** with at least **8GB VRAM**.
- **Python 3.10+** installed.
- **CUDA Toolkit** (installed with PyTorch).

## 📦 Installation (Local)

1. **Open a terminal** in this folder:
   ```bash
   cd anime_video_mvp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This will install PyTorch and Diffusers.*

3. **(Optional) Install FFmpeg:**
   The tool uses `imageio` which usually handles this, but if you get video saving errors, install FFmpeg manually or via:
   ```bash
   pip install imageio-ffmpeg
   ```

## 🏃 Usage (Local)

1. **Run the App:**
   ```bash
   python app.py
   ```

2. **First Run Warning:**
   - On the first run, the app will download **~5-6 GB** of AI models from Hugging Face.
   - Please be patient! It depends on your internet speed.

3. **Generate:**
   - Open the local URL (usually `http://127.0.0.1:7860`).
   - Upload an anime image.
   - (Optional) Add a prompt describing the character.
   - Click **Generate Video**.

## 🧩 Technical Details

- **Base Model:** `Lykon/DreamShaper` (Stable Diffusion 1.5 Fine-tune)
- **Motion Module:** `AnimateDiff v1.5.2`
- **Pipeline:** `AnimateDiffVideoToVideoPipeline`
- **Logic:** The input image is duplicated to create a static video sequence, which is then passed through AnimateDiff with a high `strength` (0.8) to induce motion while preserving the original composition.

## ⚠️ Troubleshooting

- **Out of Memory (OOM):**
  - The code already enables `enable_model_cpu_offload()` and `enable_vae_slicing()`.
  - If you still crash, try closing other apps or reducing `num_frames` in `app.py` to 16.

- **"Module not found" errors:**
  - Ensure you are in the correct virtual environment or installed requirements successfully.
