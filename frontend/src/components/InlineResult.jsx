import ReactMarkdown from 'react-markdown'

export default function InlineResult({ error, loading, response, streamingText, selectedModel, loadingLabel, placeholderText }) {
    return (
        <>
            {error && (
                <div className="inline-result inline-result--error fade-in">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    {error}
                </div>
            )}

            {loading && (
                <div className="inline-result inline-result--streaming fade-in">
                    <div className="inline-result__label">
                        <span className="loading-spinner" style={{ width: 11, height: 11, borderWidth: 1.5 }} />
                        {streamingText ? 'Generating' : (loadingLabel || 'Processing')}
                        <span className="response-badge" style={{ marginLeft: 'auto' }}>{selectedModel}</span>
                    </div>
                    <div className="inline-result__text">
                        {streamingText ? (
                            <ReactMarkdown>{streamingText}</ReactMarkdown>
                        ) : (
                            <span className="streaming-placeholder">{placeholderText || loadingLabel || 'Waiting…'}</span>
                        )}
                        <span className="streaming-cursor">▌</span>
                    </div>
                </div>
            )}

            {response && !loading && (
                <div className="inline-result inline-result--success fade-in">
                    <div className="inline-result__label">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <polyline points="20 6 9 17 4 12" />
                        </svg>
                        Summary
                        {response.cancelled && (
                            <span style={{ fontWeight: 400, opacity: 0.6, textTransform: 'none', letterSpacing: 0, marginLeft: 4 }}>· partial</span>
                        )}
                        <span className="response-badge" style={{ marginLeft: 'auto' }}>{response.model ?? selectedModel}</span>
                    </div>
                    <div className="inline-result__text">
                        <ReactMarkdown>{response.summary}</ReactMarkdown>
                    </div>
                </div>
            )}
        </>
    )
}
