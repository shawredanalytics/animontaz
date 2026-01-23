const ffmpeg = require('fluent-ffmpeg');
const ffmpegPath = require('ffmpeg-static');
const path = require('path');
const fs = require('fs');

ffmpeg.setFfmpegPath(ffmpegPath);

/**
 * Creates a video from a sequence of images and an audio track.
 * Applies "Action Anime" style processing (Saturation boost, High contrast, Dynamic Zoom/Shake).
 * @param {string[]} imagePaths - Array of absolute paths to images.
 * @param {string|null} audioUrl - URL or path to audio file. Can be null.
 * @param {string} outputFilename - Desired output filename (e.g. 'video_123.mp4').
 * @returns {Promise<string>} - Path to the generated video file.
 */
const createVideoFromImages = (imagePaths, audioUrl, outputFilename) => {
  return new Promise((resolve, reject) => {
    const outputPath = path.join(__dirname, '../uploads', outputFilename);
    
    // Duration per image in seconds
    const durationPerImage = 3;
    // Frame rate
    const fps = 30; 
    const totalFrames = durationPerImage * fps;

    let command = ffmpeg();

    // Add inputs
    imagePaths.forEach((img) => {
      // Loop image for the duration. Explicitly set input framerate.
      command = command.input(img).inputOptions([
        '-loop 1', 
        `-framerate ${fps}`, 
        `-t ${durationPerImage}`
      ]);
    });

    // Add audio input if provided
    if (audioUrl) {
       const videoDuration = imagePaths.length * durationPerImage;
       command = command.input(audioUrl).inputOptions(['-t ' + videoDuration]);
    }

    let filterComplex = '';
    const outputs = [];

    for (let i = 0; i < imagePaths.length; i++) {
      // "Action Anime" Filter Chain:
      // 1. scale/pad: Standardize resolution to 1280x720
      // 2. eq: Boost saturation (1.3) and contrast (1.1) - slightly reduced to save bitrate and look natural
      // 3. zoompan:
      //    - Explicitly set fps to match output
      
      // Alternating zoom effect
      const zoomExpr = i % 2 === 0 ? `'min(zoom+0.005,2.0)'` : `'2.0-on/(${totalFrames})'`; 
      
      filterComplex += `[${i}:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,eq=saturation=1.3:contrast=1.1,zoompan=z=${zoomExpr}:d=${totalFrames}:fps=${fps}:x='iw/2-(iw/zoom/2)+sin(time*20)*5':y='ih/2-(ih/zoom/2)+cos(time*15)*5':s=1280x720,setsar=1[v${i}];`;
      outputs.push(`[v${i}]`);
    }

    // Concat all video streams
    filterComplex += `${outputs.join('')}concat=n=${imagePaths.length}:v=1:a=0[v]`;

    // Build Output Options
    const outputOptions = [
      '-map [v]',           
      '-c:v libx264',       
      '-pix_fmt yuv420p',   
      `-r ${fps}`,
      '-crf 28',            // Lower quality for smaller file size
      '-preset veryfast',   // Faster encoding
      '-movflags +faststart' // Optimize for web playback (streamable)
    ];

    if (audioUrl) {
      const audioIndex = imagePaths.length; // Audio is the last input
      outputOptions.push(`-map ${audioIndex}:a`);
      outputOptions.push('-shortest'); 
    }

    command
      .complexFilter(filterComplex)
      .outputOptions(outputOptions)
      .output(outputPath)
      .on('start', (cmdLine) => {
        console.log('Spawned Ffmpeg with command: ' + cmdLine);
      })
      .on('error', (err) => {
        console.error('An error occurred: ' + err.message);
        reject(err);
      })
      .on('end', () => {
        console.log('Processing finished !');
        resolve(outputFilename);
      });

    command.run();
  });
};

module.exports = { createVideoFromImages };
