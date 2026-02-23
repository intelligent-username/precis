import { useState, useRef } from 'react'

const API_BASE = 'http://localhost:8000'

export function useStreaming() {
    const [loading, setLoading] = useState(false)
    const [response, setResponse] = useState(null)
    const [error, setError] = useState(null)
    const [streamingText, setStreamingText] = useState('')
    const abortRef = useRef(null)

    const readNDJSONStream = async (res) => {
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let accumulated = ''
        let buffer = ''

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
                    if (chunk.response) {
                        accumulated += chunk.response
                        setStreamingText(accumulated)
                    }
                } catch { /* skip malformed */ }
            }
        }

        return accumulated.trim()
    }

    const streamFrom = async (endpoint, { json, formData } = {}) => {
        abortRef.current = new AbortController()

        const fetchOpts = {
            method: 'POST',
            signal: abortRef.current.signal,
        }

        if (json) {
            fetchOpts.headers = { 'Content-Type': 'application/json' }
            fetchOpts.body = JSON.stringify(json)
        } else if (formData) {
            fetchOpts.body = formData
        }

        const res = await fetch(`${API_BASE}${endpoint}`, fetchOpts)

        if (!res.ok) {
            const body = await res.text()
            let detail = `Backend error (${res.status})`
            try { detail = JSON.parse(body).detail } catch { /* use default */ }
            throw new Error(detail)
        }

        return readNDJSONStream(res)
    }

    const submit = async (activeTab, { youtubeUrl, transcript, selectedFile, selectedModel }) => {
        setLoading(true)
        setError(null)
        setResponse(null)
        setStreamingText('')

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

            setResponse({ summary, success: true, source_type: activeTab, model: selectedModel })
        } catch (err) {
            setError(err.message || 'An error occurred')
        } finally {
            setLoading(false)
        }
    }

    return { loading, response, error, streamingText, submit }
}
