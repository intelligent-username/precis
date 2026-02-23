import { useState, useRef } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'
const OLLAMA_URL = 'http://127.0.0.1:11434/v1/completions'
const MODEL_NAME = 'phi4-mini:3.8b'

function App() {
  const [activeTab, setActiveTab] = useState('youtube')
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [transcript, setTranscript] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const callOllama = async (text) => {
    const prompt = `Summarise the following article in 2–4 clear, factual sentences. Do not add opinions or commentary.\n\nArticle:\n${text}\n\nSummary:`

    const res = await fetch(OLLAMA_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: MODEL_NAME,
        prompt,
        max_tokens: 120,
        temperature: 0.2,
        stop: ['\n\n', 'Article:', 'Title:']
      })
    })

    if (!res.ok) {
      const body = await res.text()
      throw new Error(`Ollama error (${res.status}): ${body}`)
    }

    const data = await res.json()
    return data.choices[0].text.trim()
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      let result

      if (activeTab === 'youtube') {
        if (!youtubeUrl.trim()) {
          throw new Error('Please enter a YouTube URL')
        }
        const res = await fetch(`${API_BASE}/summarize/youtube`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: youtubeUrl })
        })
        result = await res.json()
      } else if (activeTab === 'transcript') {
        if (!transcript.trim()) {
          throw new Error('Please enter some text')
        }
        const summary = await callOllama(transcript)
        result = { summary, success: true, source_type: 'transcript', model: MODEL_NAME }
      } else if (activeTab === 'file') {
        if (!selectedFile) {
          throw new Error('Please select a file')
        }
        const formData = new FormData()
        formData.append('file', selectedFile)
        const res = await fetch(`${API_BASE}/summarize/file`, {
          method: 'POST',
          body: formData
        })
        result = await res.json()
      }

      setResponse(result)
    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleFileDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    const file = e.dataTransfer?.files[0] || e.target.files?.[0]
    if (file && file.name.endsWith('.txt')) {
      setSelectedFile(file)
    } else if (file) {
      setError('Only .txt files are supported')
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' bytes'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <>
      <header className="header">
        <a href="/" className="logo">
          <svg className="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
          Précis
        </a>
        <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer" className="btn">
          API Docs
        </a>
      </header>

      <main className="main">
        <div className="container">
          <div className="upload-section fade-in">
            <h1 className="page-title">Summarize Content</h1>
            <p className="page-subtitle">
              Upload a YouTube video, paste a transcript, or drop a text file to generate a summary.
            </p>

            <div className="upload-card">
              <div className="upload-header">
                <div className="upload-title">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  Upload Content
                </div>
              </div>

              <div className="upload-body">
                <div className="tabs">
                  <button
                    className={`tab ${activeTab === 'youtube' ? 'active' : ''}`}
                    onClick={() => setActiveTab('youtube')}
                  >
                    YouTube Video
                  </button>
                  <button
                    className={`tab ${activeTab === 'transcript' ? 'active' : ''}`}
                    onClick={() => setActiveTab('transcript')}
                  >
                    Article / Transcript
                  </button>
                  <button
                    className={`tab ${activeTab === 'file' ? 'active' : ''}`}
                    onClick={() => setActiveTab('file')}
                  >
                    Text File
                  </button>
                </div>

                {/* YouTube Tab */}
                <div className={`tab-panel ${activeTab === 'youtube' ? 'active' : ''}`}>
                  <div className="form-group">
                    <label className="form-label">YouTube URL</label>
                    <input
                      type="url"
                      className="input"
                      placeholder="https://www.youtube.com/watch?v=..."
                      value={youtubeUrl}
                      onChange={(e) => setYoutubeUrl(e.target.value)}
                    />
                    <p className="form-hint">Paste the full URL of a YouTube video to summarize its content.</p>
                  </div>
                </div>

                {/* Transcript Tab */}
                <div className={`tab-panel ${activeTab === 'transcript' ? 'active' : ''}`}>
                  <div className="form-group">
                    <label className="form-label">Article or Transcript Text</label>
                    <textarea
                      className="textarea"
                      placeholder="Paste your article or transcript here..."
                      value={transcript}
                      onChange={(e) => setTranscript(e.target.value)}
                    />
                    <p className="form-hint">Paste any text content you want to summarize.</p>
                  </div>

                  {/* Inline result — only shown when this tab triggered it */}
                  {activeTab === 'transcript' && error && (
                    <div className="inline-result inline-result--error fade-in">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
                      {error}
                    </div>
                  )}
                  {activeTab === 'transcript' && loading && (
                    <div className="inline-result inline-result--loading fade-in">
                      <span className="loading-spinner" style={{ width: 14, height: 14 }} />
                      Generating summary…
                    </div>
                  )}
                  {activeTab === 'transcript' && response && !loading && (
                    <div className="inline-result inline-result--success fade-in">
                      <div className="inline-result__label">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                        Summary
                        <span className="response-badge" style={{ marginLeft: 'auto' }}>{response.model ?? 'phi4-mini'}</span>
                      </div>
                      <p className="inline-result__text">{response.summary}</p>
                    </div>
                  )}
                </div>

                {/* File Tab */}
                <div className={`tab-panel ${activeTab === 'file' ? 'active' : ''}`}>
                  <div className="form-group">
                    <label className="form-label">Text File (.txt)</label>
                    <div
                      className={`dropzone ${selectedFile ? '' : ''}`}
                      onClick={() => fileInputRef.current?.click()}
                      onDrop={handleFileDrop}
                      onDragOver={(e) => e.preventDefault()}
                    >
                      <svg className="dropzone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <p className="dropzone-text">
                        Drag and drop a <strong>.txt</strong> file here, or click to browse
                      </p>
                      <p className="dropzone-hint">Maximum file size: 10 MB</p>
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="file-input"
                      accept=".txt"
                      onChange={handleFileDrop}
                    />

                    {selectedFile && (
                      <div className="file-selected">
                        <div className="file-icon">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                            <line x1="16" y1="13" x2="8" y2="13" />
                            <line x1="16" y1="17" x2="8" y2="17" />
                          </svg>
                        </div>
                        <div className="file-info">
                          <div className="file-name">{selectedFile.name}</div>
                          <div className="file-size">{formatFileSize(selectedFile.size)}</div>
                        </div>
                        <button
                          className="file-remove"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedFile(null)
                          }}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="submit-section">
                  <button
                    className="btn btn-primary btn-lg"
                    onClick={handleSubmit}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="loading-spinner" style={{ width: 16, height: 16 }}></span>
                        Processing...
                      </>
                    ) : (
                      <>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M22 2L11 13" />
                          <path d="M22 2L15 22l-4-9-9-4L22 2z" />
                        </svg>
                        Generate Summary
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Error display — for YouTube / File tabs only (transcript shows inline) */}
            {error && activeTab !== 'transcript' && (
              <div className="response-section fade-in">
                <div className="response-card" style={{ borderColor: 'var(--color-danger-fg)' }}>
                  <div className="response-header" style={{ borderColor: 'var(--color-danger-fg)' }}>
                    <div className="response-title" style={{ color: 'var(--color-danger-fg)' }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                      </svg>
                      Error
                    </div>
                  </div>
                  <div className="response-body">
                    <p className="response-text" style={{ color: 'var(--color-danger-fg)' }}>{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Response display — for YouTube / File tabs only (transcript shows inline) */}
            {response && activeTab !== 'transcript' && (
              <div className="response-section fade-in">
                <div className="response-card">
                  <div className="response-header">
                    <div className="response-title">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                      </svg>
                      Summary
                    </div>
                    <span className="response-badge">{response.source_type}</span>
                  </div>
                  <div className="response-body">
                    <p className="response-text">{response.summary}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="footer">
        <p>Précis © 2026 · Built with ♥ · <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer">API Documentation</a></p>
      </footer>
    </>
  )
}

export default App
