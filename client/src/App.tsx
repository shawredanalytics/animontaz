import { useState, useRef, useEffect } from 'react'
import './index.css'

interface GenerationResult {
  character: string;
  audio: string;
  video: string | null;
  transcript: string;
}

function App() {
  const [prompt, setPrompt] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedAudio, setSelectedAudio] = useState<File | null>(null);
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<GenerationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (result && audioRef.current && !result.video) {
      audioRef.current.play().catch(e => console.log("Auto-play prevented", e));
    }
  }, [result]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleAudioChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedAudio(e.target.files[0]);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim() && selectedFiles.length === 0) {
        setError("Please provide a prompt OR upload image(s).");
        return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      if (prompt) formData.append('prompt', prompt);
      
      selectedFiles.forEach((file) => {
        formData.append('images', file);
      });

      if (selectedAudio) {
        formData.append('audio', selectedAudio);
      }

      const response = await fetch('/api/generate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate video');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <nav className="navbar container">
        <a href="#" className="logo">
          Animontaz
        </a>
        <button className="btn">Sign In</button>
      </nav>

      <section className="hero" style={{ 
        backgroundColor: '#000000'
      }}>
        <div className="hero-overlay"></div>
        <div className="hero-content container">
          <h1>Create Your Own Anime Saga</h1>
          <p className="hero-subtitle">
            Turn your words into fully voiced, animated characters instantly. 
            Or upload your own art to bring it to life.
          </p>
          
          <div className="input-group">
            <textarea
              className="prompt-input"
              rows={2}
              placeholder="Describe your character and their line (e.g., A cyberpunk detective saying 'The neon lights never sleep in this city.')"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', width: '100%', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '10px' }}>
                <input 
                    type="file" 
                    accept="image/*"
                    multiple 
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />
                <button 
                    className="btn" 
                    onClick={() => fileInputRef.current?.click()}
                    style={{ 
                        background: selectedFiles.length > 0 ? 'var(--primary)' : 'rgba(255,255,255,0.1)', 
                        fontSize: '0.9rem',
                        padding: '0.5em 1em',
                        border: selectedFiles.length > 0 ? '1px solid var(--primary)' : '1px solid rgba(255,255,255,0.2)'
                    }}
                >
                    {selectedFiles.length > 0 ? `${selectedFiles.length} Image${selectedFiles.length > 1 ? 's' : ''} Selected` : '📷 Upload Images'}
                </button>
                {selectedFiles.length > 0 && (
                    <button 
                        className="btn" 
                        onClick={() => setSelectedFiles([])}
                        style={{ background: 'transparent', padding: '0.5em', color: '#ff4444' }}
                        title="Remove images"
                    >
                        ✕
                    </button>
                )}
                
                <div style={{ flexGrow: 1 }}></div>

                <input 
                    type="file" 
                    accept="audio/*"
                    ref={audioInputRef}
                    onChange={handleAudioChange}
                    style={{ display: 'none' }}
                />
                <button 
                    className="btn" 
                    onClick={() => audioInputRef.current?.click()}
                    style={{ 
                        background: selectedAudio ? 'var(--accent)' : 'rgba(255,255,255,0.1)', 
                        fontSize: '0.9rem',
                        padding: '0.5em 1em',
                        border: selectedAudio ? '1px solid var(--accent)' : '1px solid rgba(255,255,255,0.2)',
                        marginRight: '10px'
                    }}
                >
                    {selectedAudio ? `🎵 ${selectedAudio.name.substring(0, 10)}...` : '🎵 Add Music'}
                </button>
                {selectedAudio && (
                    <button 
                        className="btn" 
                        onClick={() => setSelectedAudio(null)}
                        style={{ background: 'transparent', padding: '0.5em', color: '#ff4444', marginRight: '10px' }}
                        title="Remove audio"
                    >
                        ✕
                    </button>
                )}

                <button 
                className="btn btn-primary" 
                onClick={handleGenerate} 
                disabled={loading}
                style={{ minWidth: '150px' }}
                >
                {loading ? 'Creating...' : 'GENERATE'}
                </button>
            </div>
          </div>

          {error && <div style={{ color: '#ff0055', marginTop: '20px', fontWeight: 'bold' }}>{error}</div>}

          {loading && (
            <div style={{ marginTop: '20px' }}>
              <div className="loader"></div>
              <p>Summoning your character...</p>
            </div>
          )}

          {result && (
            <div className="result-container">
              <div className="video-wrapper" style={{ position: 'relative', overflow: 'hidden' }}>
                {result.video ? (
                   <video controls autoPlay src={result.video} />
                ) : (
                  // Simulated Cinematic Video using Ken Burns effect on the image
                  <div className="cinematic-preview">
                    <img src={result.character} alt="Generated Character" />
                    <div className="cinematic-overlay">
                       <div className="audio-visualizer">
                          <div className="bar"></div>
                          <div className="bar"></div>
                          <div className="bar"></div>
                          <div className="bar"></div>
                          <div className="bar"></div>
                       </div>
                    </div>
                  </div>
                )}
              </div>
              <div className="result-details">
                <div style={{ textAlign: 'left' }}>
                  <h3 style={{ marginBottom: '0.5rem' }}>Dialogue Transcript</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>"{result.transcript}"</p>
                </div>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                   <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '5px' }}>Voice Track</span>
                    <audio ref={audioRef} controls src={result.audio} style={{ height: '30px', width: '200px' }} />
                   </div>
                   {result.video && (
                     <a 
                        href={result.video} 
                        download="anime-saga.mp4" 
                        className="btn" 
                        style={{ 
                            textDecoration: 'none', 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '5px',
                            background: 'var(--secondary)',
                            padding: '0.5em 1em',
                            fontSize: '0.9rem'
                        }}
                     >
                       ⬇ Download Video
                     </a>
                   )}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </>
  )
}

export default App
