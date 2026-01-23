// Mock AI Service
// In a real application, this would interact with APIs like OpenAI, ElevenLabs, D-ID, etc.

const generateVideo = async (prompt, uploadedImageUrl = null) => {
  console.log(`Processing request. Prompt: ${prompt}, Image Uploaded: ${!!uploadedImageUrl}`);

  // Simulate processing time
  await new Promise(resolve => setTimeout(resolve, 3000));

  let dialogue = "I am ready to face my destiny.";
  let characterImageUrls = [];

  if (prompt) {
    // 1. Analyze prompt (Mock)
    // Extract character, dialogue, scene
    const extractedDialogue = prompt.match(/"([^"]*)"/)?.[1];
    if (extractedDialogue) {
        dialogue = extractedDialogue;
    }
  }

  // 2. Generate Character Images (Real - using Pollinations.ai) IF no image uploaded
  if (uploadedImageUrl) {
      characterImageUrls = [uploadedImageUrl];
  } else if (prompt) {
    // Clean prompt for image generation (remove quotes and extra words)
    const imagePrompt = prompt.replace(/"[^"]*"/g, '').replace(/saying|says/g, '').trim();
    
    // Generate 4 scenes for a continuous feel
    // We try to keep consistency by using the same seed but different camera angles
    const baseSeed = Math.floor(Math.random() * 1000000);
    const scenes = [
        "wide angle establishing shot, cinematic composition",
        "medium shot, dynamic action pose",
        "close up, detailed expression, dramatic lighting",
        "dynamic angle, intense atmosphere, movie still"
    ];

    characterImageUrls = scenes.map((sceneDesc, index) => {
        // We use slightly different seeds (base + index) to get variation, 
        // OR same seed with different prompts. 
        // Experience says same seed + different prompt changes the image too much anyway, 
        // but let's try to keep the core style prompts very strong.
        const fullPrompt = `anime style, masterpiece, best quality, 8k, cinematic lighting, detailed character design, ${imagePrompt}, ${sceneDesc}`;
        const encodedPrompt = encodeURIComponent(fullPrompt);
        return `https://image.pollinations.ai/prompt/${encodedPrompt}?width=1024&height=576&seed=${baseSeed + index}&nologo=true`;
    });

  } else {
     // Fallback if no image and no prompt
     characterImageUrls = ["https://via.placeholder.com/1024x576?text=No+Image+Generated"];
  }

  // 3. Generate Audio (Mock)
  // We return a placeholder, but the controller handles silence if user didn't upload any.
  const audioUrl = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"; 

  return {
    status: 'success',
    data: {
      character: characterImageUrls[0], // Main thumbnail
      images: characterImageUrls,       // All generated frames
      audio: audioUrl,
      video: null, 
      transcript: dialogue
    }
  };
};

module.exports = {
  generateVideo
};
