import { useState, useRef } from 'react'
import InlineResult from './components/InlineResult'
import { useStreaming } from './hooks/useStreaming'
import logoSvg from './assets/logo.svg'
import { API_BASE, AVAILABLE_MODELS, DEFAULT_MODEL } from './config'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('youtube')
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [transcript, setTranscript] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL)
  const fileInputRef = useRef(null)

  const { loading, response, error, streamingText, submit } = useStreaming()

  const handleSubmit = () =>
    submit(activeTab, { youtubeUrl, transcript, selectedFile, selectedModel })

  const handleFileDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    const file = e.dataTransfer?.files[0] || e.target.files?.[0]
    if (file && file.name.endsWith('.txt')) setSelectedFile(file)
    else if (file) alert('Only .txt files are supported')
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' bytes'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const ctrlEnter = (e) => {
    if (e.key === 'Enter' && e.ctrlKey && !loading) handleSubmit()
  }

  const resultProps = { error, loading, response, streamingText, selectedModel }

  return (
    <>
      <header className="header">
        <a href="/" className="logo">
          <img src={logoSvg} alt="Précis" className="logo-icon" />
          <span className="logo-text">Précis</span>
        </a>
        <div className="header-actions">
          <select
            className="model-select"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={loading}
          >
            {AVAILABLE_MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer" className="btn" style={{ textDecoration: 'none' }}>
            API Docs
          </a>
        </div>
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
                  {[['youtube', 'YouTube Video'], ['transcript', 'Article / Transcript'], ['file', 'Text File']].map(([key, label]) => (
                    <button key={key} className={`tab ${activeTab === key ? 'active' : ''}`} onClick={() => setActiveTab(key)}>
                      {label}
                    </button>
                  ))}
                </div>

                {/* YouTube */}
                <div className={`tab-panel ${activeTab === 'youtube' ? 'active' : ''}`}>
                  <div className="form-group">
                    <label className="form-label">YouTube URL</label>
                    <input
                      type="url" className="input"
                      placeholder="https://www.youtube.com/watch?v=..."
                      value={youtubeUrl}
                      onChange={(e) => setYoutubeUrl(e.target.value)}
                      onKeyDown={ctrlEnter}
                    />
                    <p className="form-hint">Paste a YouTube URL. Ctrl+Enter to generate.</p>
                  </div>
                  {activeTab === 'youtube' && <InlineResult {...resultProps} loadingLabel="Fetching transcript…" />}
                </div>

                {/* Transcript */}
                <div className={`tab-panel ${activeTab === 'transcript' ? 'active' : ''}`}>
                  <div className="form-group">
                    <label className="form-label">Article or Transcript Text</label>
                    <textarea
                      className="textarea"
                      placeholder="Paste your article or transcript here..."
                      value={transcript}
                      onChange={(e) => setTranscript(e.target.value)}
                      onKeyDown={ctrlEnter}
                    />
                    <p className="form-hint">
                      Paste any text you want to summarize.{' '}
                      <kbd style={{ fontFamily: 'inherit', background: 'var(--color-canvas-inset)', border: '1px solid var(--color-border-muted)', borderRadius: 3, padding: '0 4px', fontSize: 11 }}>Ctrl</kbd>
                      {' + '}
                      <kbd style={{ fontFamily: 'inherit', background: 'var(--color-canvas-inset)', border: '1px solid var(--color-border-muted)', borderRadius: 3, padding: '0 4px', fontSize: 11 }}>Enter</kbd>
                      {' '}to generate.
                    </p>
                  </div>
                  {activeTab === 'transcript' && <InlineResult {...resultProps} loadingLabel="Generating…" />}
                </div>

                {/* File upload */}
                <div className={`tab-panel ${activeTab === 'file' ? 'active' : ''}`}>
                  <div className="form-group">
                    <label className="form-label">Text File (.txt)</label>
                    <div className="dropzone" onClick={() => fileInputRef.current?.click()} onDrop={handleFileDrop} onDragOver={(e) => e.preventDefault()}>
                      <svg className="dropzone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <p className="dropzone-text">Drag and drop a <strong>.txt</strong> file here, or click to browse</p>
                      <p className="dropzone-hint">Maximum file size: 10 MB</p>
                    </div>
                    <input ref={fileInputRef} type="file" className="file-input" accept=".txt" onChange={handleFileDrop} />

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
                        <button className="file-remove" onClick={(e) => { e.stopPropagation(); setSelectedFile(null) }}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                  {activeTab === 'file' && <InlineResult {...resultProps} loadingLabel="Reading file…" />}
                </div>

                <div className="submit-section">
                  <button className="btn btn-primary btn-lg" onClick={handleSubmit} disabled={loading}>
                    {loading ? (
                      <><span className="loading-spinner" style={{ width: 16, height: 16 }} /> Processing...</>
                    ) : (
                      <>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M22 2L11 13" /><path d="M22 2L15 22l-4-9-9-4L22 2z" />
                        </svg>
                        Generate Summary
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="footer">
        <p>Précis © 2026 · <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer">API Documentation</a></p>
      </footer>
    </>
  )
}

export default App
