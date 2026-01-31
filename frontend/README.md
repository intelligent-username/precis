# Frontend

A GitHub-inspired dark theme frontend for the Précis content summarization API.

## Features

- **YouTube Video Summarization**: Paste a YouTube URL to summarize video content
- **Article/Transcript Summarization**: Paste any text directly to summarize
- **File Upload**: Drag and drop or browse for `.txt` files to summarize

## Prerequisites

- Node.js 18+ (or Bun)
- The backend API running at `http://localhost:8000`

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

Or with Bun:

```bash
bun install
```

### 2. Start the Development Server

```bash
npm run dev
```

Or with Bun:

```bash
bun run dev
```

The frontend will be available at [http://localhost:5173](http://localhost:5173).

### 3. Start the Backend API (Required)

In a separate terminal, navigate to the backend directory and run:

```bash
cd ../backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/summarize/youtube` | POST | Summarize YouTube video |
| `/summarize/transcript` | POST | Summarize text content |
| `/summarize/file` | POST | Summarize uploaded .txt file |

## Build for Production

```bash
npm run build
```

The output will be in the `dist/` directory.
