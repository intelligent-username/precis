import { useState, useRef } from 'react'
import { API_BASE, authHeaders } from '../config'

export function useStreaming() {
    const [loading, setLoading] = useState(false)
    const [response, setResponse] = useState(null)
    const [error, setError] = useState(null)
    const [streamingText, setStreamingText] = useState('')
    const [isGenerating, setIsGenerating] = useState(false)
    const abortRef = useRef(null)
    // Tracks accumulated text in real-time so cancel() can save it as a response
    const accumulatedRef = useRef('')
    // Incremented on each submit so stale completions don't overwrite fresh state
    const submitIdRef = useRef(0)
    // RAF throttle for streaming updates — prevents "laggy" re-renders on every token
    const rafRef = useRef(null)
    const pendingTextRef = useRef('')

    const flushStreamingText = () => {
        if (pendingTextRef.current) {
            setStreamingText(pendingTextRef.current)
        }
        rafRef.current = null
    }

    const scheduleStreamingUpdate = (text) => {
        pendingTextRef.current = text
        accumulatedRef.current = text
        if (rafRef.current == null) {
            // Throttle to animation frame (~60fps max) instead of per-token setState
            rafRef.current = requestAnimationFrame(flushStreamingText)
        }
    }

    const readNDJSONStream = async (res) => {
        if (!res.body) throw new Error('Streaming not supported by browser')
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let accumulated = ''
        let buffer = ''
        let streamError = null

        try {
            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop()

                for (const line of lines) {
                    if (!line.trim()) continue
                    try {
                        const chunk = JSON.parse(line)
                        if (chunk.error) {
                            streamError = String(chunk.error)
                            continue
                        }
                        if (chunk.response) {
                            accumulated += chunk.response
                            scheduleStreamingUpdate(accumulated)
                        }
                    } catch { /* skip malformed */ }
                }
            }
            // Handle trailing buffer (no final newline) — fixes "stops after script fetching"
            if (buffer && buffer.trim()) {
                try {
                    const chunk = JSON.parse(buffer)
                    if (chunk.error) streamError = String(chunk.error)
                    else if (chunk.response) {
                        accumulated += chunk.response
                        scheduleStreamingUpdate(accumulated)
                    }
                } catch { /* ignore */ }
            }
            // Ensure final frame flushed
            if (rafRef.current) {
                cancelAnimationFrame(rafRef.current)
                rafRef.current = null
            }
            pendingTextRef.current = accumulated
            accumulatedRef.current = accumulated
            // Only set final state if not already scheduled — avoid double render
            // We set directly to ensure final text is visible before clearing in finally
            if (accumulated) setStreamingText(accumulated)
        } finally {
            try { reader.releaseLock() } catch {}
        }

        if (streamError) {
            throw new Error(streamError)
        }

        const finalText = accumulated.trim()
        if (!finalText) {
            throw new Error('Model returned an empty response. Try again or pick a different model.')
        }

        return finalText
    }

    const streamFrom = async (endpoint, { json, formData } = {}) => {
        abortRef.current = new AbortController()

        const fetchOpts = {
            method: 'POST',
            signal: abortRef.current.signal,
        }

        if (json) {
            fetchOpts.headers = authHeaders({ 'Content-Type': 'application/json' })
            fetchOpts.body = JSON.stringify(json)
        } else if (formData) {
            fetchOpts.headers = authHeaders()
            fetchOpts.body = formData
        }

        const res = await fetch(`${API_BASE}${endpoint}`, fetchOpts)

        if (!res.ok) {
            const body = await res.text()
            let detail = `Backend error (${res.status})`
            try { detail = JSON.parse(body).detail } catch { /* use default */ }
            throw new Error(detail)
        }

        setIsGenerating(true)
        return readNDJSONStream(res)
    }

    const submit = async (activeTab, { youtubeUrl, transcript, selectedFile, selectedModel }) => {
        // Abort any in-flight request before starting a new one
        abortRef.current?.abort()

        const myId = ++submitIdRef.current

        setLoading(true)
        setError(null)
        setResponse(null)
        setStreamingText('')
        setIsGenerating(false)
        accumulatedRef.current = ''

        try {
            let summary

            if (activeTab === 'youtube') {
                if (!youtubeUrl.trim()) throw new Error('Please enter a YouTube URL')
                summary = await streamFrom('/summarize/youtube', { json: { url: youtubeUrl, model: selectedModel } })
            } else if (activeTab === 'transcript') {
                if (!transcript.trim()) throw new Error('Please enter some text')
                summary = await streamFrom('/summarize/transcript', { json: { text: transcript, model: selectedModel } })
            } else if (activeTab === 'file') {
                if (!selectedFile) throw new Error('Please select a file')
                const fd = new FormData()
                fd.append('file', selectedFile)
                summary = await streamFrom(`/summarize/file?model=${encodeURIComponent(selectedModel)}`, { formData: fd })
            }

            if (submitIdRef.current !== myId) return  // superseded by a newer submit
            setResponse({ summary, success: true, source_type: activeTab, model: selectedModel })
        } catch (err) {
            if (submitIdRef.current !== myId) return  // superseded: don't touch state
            if (err.name === 'AbortError') {
                // User cancelled: keep whatever was generated so far as the result
                const partial = accumulatedRef.current.trim()
                if (partial) {
                    setResponse({
                        summary: partial,
                        success: true,
                        source_type: activeTab,
                        model: selectedModel,
                        cancelled: true
                    })
                }
                // If nothing was generated yet, just reset silently (no error shown)
                return
            }
            setError(err.message || 'An error occurred')
        } finally {
            // Only the current submit should clear loading: stale ones must not interfere
            if (submitIdRef.current === myId) {
                setLoading(false)
                setStreamingText('')
                setIsGenerating(false)
            }
        }
    }

    const cancel = () => {
        if (rafRef.current) {
            cancelAnimationFrame(rafRef.current)
            rafRef.current = null
        }
        abortRef.current?.abort()
    }

    return { loading, response, error, streamingText, isGenerating, submit, cancel }
}
