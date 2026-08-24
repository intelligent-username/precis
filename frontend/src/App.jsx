import { useEffect, useState, useRef, useCallback, useMemo } from 'react'
import InlineResult from './components/InlineResult'
import { useStreaming } from './hooks/useStreaming'
import { API_BASE } from './config'
const logoSvg = '/logo.svg'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('youtube')
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [transcript, setTranscript] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [modelReady, setModelReady] = useState(null)
  const fileInputRef = useRef(null)
  const warmupAbortRef = useRef(null)
  const warmupTimerRef = useRef(null)

  const ytStreaming = useStreaming()
  const textStreaming = useStreaming()
  const fileStreaming = useStreaming()

  // Memoize streaming map so `active` identity is stable unless tab changes
  const streaming = useMemo(() => ({
    youtube: ytStreaming,
    transcript: textStreaming,
    file: fileStreaming
  }), [ytStreaming, textStreaming, fileStreaming])
  const active = streaming[activeTab]

  const [runningModels, setRunningModels] = useState([])
  const isMounted = useRef(true)
  const prevModelRef = useRef(null)

  // Stable fetchModels — used in intervals and warmup, so must not recreate
  const fetchModels = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/models`)
      if (!res.ok) return
      const data = await res.json()
      if (!isMounted.current) return
      const available = Array.isArray(data.available) ? data.available : []
      const running = Array.isArray(data.running) ? data.running : []
      setModels(available)
      setRunningModels(running)
      const serverDefault = typeof data.default === 'string' ? data.default : ''
      setSelectedModel((prev) => prev || serverDefault || available[0] || '')
    } catch { /* non-fatal */ }
  }, [])

  // Fetch models on mount + every 30s (was 10s → laggy, 30s is enough)
  // Also pause polling when tab hidden to save battery/CPU
  useEffect(() => {
    isMounted.current = true
    fetchModels()
    let interval = null
    const start = () => {
      if (interval) clearInterval(interval)
      interval = setInterval(() => {
        if (document.visibilityState === 'visible') fetchModels()
      }, 30000)
    }
    start()
    const onVis = () => { if (document.visibilityState === 'visible') fetchModels() }
    document.addEventListener('visibilitychange', onVis)
    return () => {
      isMounted.current = false
      clearInterval(interval)
      document.removeEventListener('visibilitychange', onVis)
    }
  }, [fetchModels])

  // Warmup: debounced 400ms, single poll loop, proper cleanup
  useEffect(() => {
    if (!selectedModel) return

    // Debounce: user rapidly switching models shouldn't spam /warmup + /unload
    if (warmupTimerRef.current) clearTimeout(warmupTimerRef.current)
    if (warmupAbortRef.current) warmupAbortRef.current.abort()

    const controller = new AbortController()
    warmupAbortRef.current = controller
    setModelReady(false)

    let pollTimer = null
    let cancelled = false

    const poll = async () => {
      if (cancelled || controller.signal.aborted) return
      try {
        const r = await fetch(
          `${API_BASE}/warmup/status?model=${encodeURIComponent(selectedModel)}`,
          { signal: controller.signal },
        )
        if (r.ok) {
          const data = await r.json()
          if (data.loaded) { if (!cancelled) setModelReady(true); return }
        }
      } catch { /* ignore — will retry */ }
      if (!cancelled && !controller.signal.aborted) pollTimer = setTimeout(poll, 2500)
    }

    const startSequence = async () => {
      // Unload previous only if actually changed — and don't refetch models immediately (laggy)
      if (prevModelRef.current && prevModelRef.current !== selectedModel) {
        try {
          await fetch(`${API_BASE}/unload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: prevModelRef.current }),
            signal: controller.signal,
          })
          // Debounce the follow-up model list refresh — don't block warmup on it
          setTimeout(() => { if (!controller.signal.aborted) fetchModels() }, 800)
        } catch { /* ignore */ }
      }
      prevModelRef.current = selectedModel

      poll()

      try {
        const r = await fetch(`${API_BASE}/warmup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: selectedModel }),
          signal: controller.signal,
        })
        // warmup endpoint is fire-and-forget-ish; if ok, mark ready
        if (r.ok && !cancelled && !controller.signal.aborted) setModelReady(true)
      } catch { /* abort or network — poll will handle */ }
    }

    // Debounce the whole sequence 400ms
    warmupTimerRef.current = setTimeout(startSequence, 400)

    return () => {
      cancelled = true
      controller.abort()
      clearTimeout(pollTimer)
      clearTimeout(warmupTimerRef.current)
    }
  }, [selectedModel, fetchModels])

  // Stable handleSubmit — fixes "frontend stops after script fetching" due to stale closure
  // and fixes keydown listener thrash (was recreating every render)
  const handleSubmit = useCallback(() =>
    active.submit(activeTab, {
      youtubeUrl, transcript, selectedFile,
      selectedModel: selectedModel || undefined,
    }), [active, activeTab, youtubeUrl, transcript, selectedFile, selectedModel])

  const handleFileDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    const file = e.dataTransfer?.files[0] || e.target.files?.[0]
    if (file && file.name.endsWith('.txt')) setSelectedFile(file)
    else if (file) alert('Only .txt files are supported')
  }, [])

  const formatFileSize = useCallback((bytes) => {
    if (bytes < 1024) return bytes + ' bytes'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }, [])

  // Keep refs for keydown so listener doesn't need to re-bind every render
  const activeRef = useRef(active)
  const handleSubmitRef = useRef(handleSubmit)
  const youtubeUrlRef = useRef(youtubeUrl)
  useEffect(() => { activeRef.current = active }, [active])
  useEffect(() => { handleSubmitRef.current = handleSubmit }, [handleSubmit])
  useEffect(() => { youtubeUrlRef.current = youtubeUrl }, [youtubeUrl])

  useEffect(() => {
    const handleKeyDown = (e) => {
      const a = activeRef.current
      // Ctrl + Enter to generate
      if (e.ctrlKey && e.key === 'Enter') {
        if (!a.loading) {
          e.preventDefault()
          handleSubmitRef.current()
        }
      }
      // Ctrl + Alt + C to copy YouTube URL
      if (e.ctrlKey && e.altKey && (e.key === 'c' || e.key === 'C')) {
        e.preventDefault()
        if (youtubeUrlRef.current) {
          navigator.clipboard.writeText(youtubeUrlRef.current).catch(() => {})
        }
        return
      }
      // Ctrl + C to cancel (only when loading, and no text selected)
      if (e.ctrlKey && !e.shiftKey && (e.key === 'c' || e.key === 'C')) {
        if (a.loading) {
          const selection = window.getSelection()?.toString()
          if (!selection) {
            e.preventDefault()
            a.cancel()
          }
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, []) // stable — uses refs

  const TABS = useMemo(() => [
    { key: 'youtube',     label: 'YouTube' },
    { key: 'transcript',  label: 'Text' },
    { key: 'file',        label: 'File' },
  ], [])

  return (
    <>
      {/* ── Main ── */}
      <main className="main">
        <div className="container">
          <div className="content-layout">

            {/* Hero strip */}
            <div className="hero">
              <div className="logo hero-logo">
                <img src={logoSvg} alt="" className="logo-icon" />
                <span className="logo-text">Précis</span>
              </div>
            </div>

            {/* Card */}
            <div className="card-wrap fade-in">

              {/* Segmented tab control */}
              <div className="seg-control">
                {TABS.map(({ key, label }) => (
                  <button
                    key={key}
                    className={`seg-btn${activeTab === key ? ' seg-btn--active' : ''}`}
                    onClick={() => setActiveTab(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {/* Panels */}
              <div className="panels">

                {/* YouTube */}
                <div className={`panel${activeTab === 'youtube' ? ' panel--active' : ''}`}>
                  <div className="field">
                    <label className="field-label">YouTube URL</label>
                    <input
                      type="url"
                      className="input input--lg"
                      placeholder="https://www.youtube.com/watch?v=…"
                      value={youtubeUrl}
                      onChange={(e) => setYoutubeUrl(e.target.value)}
                    />
                  </div>
                  <InlineResult
                    error={ytStreaming.error}
                    loading={ytStreaming.loading}
                    response={ytStreaming.response}
                    streamingText={ytStreaming.streamingText}
                    selectedModel={selectedModel}
                    loadingLabel={ytStreaming.isGenerating ? 'Generating…' : 'Fetching transcript…'}
                    placeholderText={ytStreaming.isGenerating ? 'Waiting for model…' : 'Fetching transcript…'}
                  />
                </div>

                {/* Text / Transcript */}
                <div className={`panel${activeTab === 'transcript' ? ' panel--active' : ''}`}>
                  <div className="field">
                    <label className="field-label">Article or transcript</label>
                    <textarea
                      className="textarea"
                      placeholder="Paste your article or transcript here…"
                      value={transcript}
                      onChange={(e) => setTranscript(e.target.value)}
                    />
                  </div>
                  <InlineResult
                    error={textStreaming.error}
                    loading={textStreaming.loading}
                    response={textStreaming.response}
                    streamingText={textStreaming.streamingText}
                    selectedModel={selectedModel}
                    loadingLabel="Generating…"
                    placeholderText="Waiting for model…"
                  />
                </div>

                {/* File */}
                <div className={`panel${activeTab === 'file' ? ' panel--active' : ''}`}>
                  <div className="field">
                    <label className="field-label">Text file <span className="field-label-hint">(.txt)</span></label>
                    <div
                      className="dropzone"
                      onClick={() => fileInputRef.current?.click()}
                      onDrop={handleFileDrop}
                      onDragOver={(e) => e.preventDefault()}
                    >
                      <svg className="dropzone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3">
                        <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <span className="dropzone-label">.txt</span>
                    </div>
                    <input ref={fileInputRef} type="file" style={{ display: 'none' }} accept=".txt" onChange={handleFileDrop} />

                    {selectedFile && (
                      <div className="file-chip">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                        </svg>
                        <span className="file-chip__name">{selectedFile.name}</span>
                        <span className="file-chip__size">{formatFileSize(selectedFile.size)}</span>
                        <button
                          className="file-chip__remove"
                          onClick={(e) => { e.stopPropagation(); setSelectedFile(null) }}
                          aria-label="Remove file"
                        >
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                  <InlineResult
                    error={fileStreaming.error}
                    loading={fileStreaming.loading}
                    response={fileStreaming.response}
                    streamingText={fileStreaming.streamingText}
                    selectedModel={selectedModel}
                    loadingLabel={fileStreaming.isGenerating ? 'Generating…' : 'Reading file…'}
                    placeholderText={fileStreaming.isGenerating ? 'Waiting for model…' : 'Reading file…'}
                  />
                </div>
              </div>

              {/* Action row */}
              <div className="action-row">
                {active.loading && (
                  <button className="btn btn-cancel" onClick={active.cancel} data-tooltip="Ctrl + C">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                    Cancel
                  </button>
                )}
                <div className="generate-wrapper">
                  <button
                    className="btn btn-primary btn-generate"
                    onClick={handleSubmit}
                    disabled={active.loading}
                    data-tooltip="Ctrl + Enter"
                  >
                    {active.loading ? (
                      <><span className="loading-spinner" style={{ width: 15, height: 15 }} /> Processing…</>
                    ) : (
                      <>
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M22 2L11 13" /><path d="M22 2L15 22l-4-9-9-4L22 2z" />
                        </svg>
                        Generate
                      </>
                    )}
                  </button>
                  <span className="action-hint">
                    {!active.loading && (
                      <>or <kbd>Ctrl</kbd>+<kbd>Enter</kbd></>
                    )}
                  </span>
                </div>
              </div>

            </div>

            {/* Model Selector at bottom right, outside card-wrap */}
            <div className="model-selector-wrap">
              <select
                className={`model-select${modelReady === true ? ' model-select--ready' : modelReady === false ? ' model-select--warming' : ''}`}
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                onFocus={fetchModels}
                disabled={active.loading || models.length === 0}
              >
                {models.map((m) => {
                  const isRunning = runningModels.some(
                    (r) => r === m || r.startsWith(m + ':') || m.startsWith(r + ':')
                  )
                  return (
                    <option key={m} value={m}>
                      {m}{isRunning ? ' (active)' : ''}
                    </option>
                  )
                })}
              </select>
            </div>

          </div>
        </div>
      </main>

      <footer className="footer">
        <span className="footer-sep">·</span>
        <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer">API Docs</a>
      </footer>
    </>
  )
}

export default App
