const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const { generateVideo } = require('../services/ai');
const { createVideoFromImages } = require('../services/videoGenerator');

// Configure Multer for file upload
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../uploads');
    if (!fs.existsSync(uploadDir)){
        fs.mkdirSync(uploadDir);
    }
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + Math.round(Math.random() * 1E9) + path.extname(file.originalname));
  }
});

const upload = multer({ storage: storage });

const downloadFile = async (url, dest) => {
  const writer = fs.createWriteStream(dest);
  const response = await axios({
    url,
    method: 'GET',
    responseType: 'stream'
  });
  response.data.pipe(writer);
  return new Promise((resolve, reject) => {
    writer.on('finish', resolve);
    writer.on('error', reject);
  });
};

router.post('/', upload.fields([{ name: 'images', maxCount: 10 }, { name: 'audio', maxCount: 1 }]), async (req, res) => {
  try {
    const { prompt } = req.body;
    const files = req.files || {};
    const imageFiles = files['images'] || [];
    const audioFile = files['audio'] ? files['audio'][0] : null;
    
    // Check if at least one input is provided
    if (!prompt && imageFiles.length === 0) {
      return res.status(400).json({ error: 'Please provide a prompt or upload images.' });
    }

    let imagePaths = [];
    let audioUrl = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"; // Default audio
    let transcript = "";

    // Handle Uploaded Audio
    if (audioFile) {
        audioUrl = path.resolve(audioFile.path);
        // If it's a local file, we need to serve it correctly or just use path for ffmpeg.
        // For frontend playback, we need a URL.
        // Let's create a URL for it.
        // NOTE: audioUrl here is used for BOTH ffmpeg (path) and frontend (url).
        // This is a bit tricky. createVideoFromImages takes audioUrl/path.
        // But the response needs a URL.
        // Let's separate them.
    }
    
    let audioPathForFFmpeg = audioFile ? path.resolve(audioFile.path) : audioUrl;

    // Scenario 1: User uploaded images
    if (imageFiles.length > 0) {
      imagePaths = imageFiles.map(f => path.resolve(f.path));
      
      // If prompt exists, use it for transcript
      if (prompt) {
        transcript = prompt;
      }
    } 
    // Scenario 2: No images, generate from prompt
    else if (prompt) {
      const aiResult = await generateVideo(prompt);
      const { images, transcript: aiTranscript } = aiResult.data;
      
      transcript = aiTranscript;
      
      // Note: We ignore the default audio from AI service to respect "no music unless provided" rule.
      if (!audioFile) {
        audioUrl = null;
        audioPathForFFmpeg = null;
      }

      // Download the generated character images
      const uploadDir = path.join(__dirname, '../uploads');
      if (!fs.existsSync(uploadDir)){
          fs.mkdirSync(uploadDir);
      }

      // Download all generated images
      const downloadPromises = images.map(async (imgUrl, index) => {
         const filename = `ai-gen-${Date.now()}-${index}.jpg`;
         const localImagePath = path.join(uploadDir, filename);
         await downloadFile(imgUrl, localImagePath);
         return localImagePath;
      });

      imagePaths = await Promise.all(downloadPromises);
    }

    // Generate Video
    const outputFilename = `video-${Date.now()}.mp4`;
    await createVideoFromImages(imagePaths, audioPathForFFmpeg, outputFilename);

    const videoUrl = `${req.protocol}://${req.get('host')}/uploads/${outputFilename}`;
    
    // If audio was uploaded, construct its URL for frontend
    if (audioFile) {
        audioUrl = `${req.protocol}://${req.get('host')}/uploads/${audioFile.filename}`;
    }

    res.json({
      status: 'success',
      data: {
        video: videoUrl,
        transcript: transcript,
        audio: audioUrl // Can be null if no audio
      }
    });

  } catch (error) {
    console.error('Error generating video:', error);
    res.status(500).json({ error: 'Failed to generate video: ' + error.message });
  }
});

module.exports = router;
