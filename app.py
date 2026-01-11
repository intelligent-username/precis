from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Précis — MVP")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Précis — MVP</title>
        </head>
        <body>
            <h1>Précis — MVP</h1>
            <p>Welcome to Précis</p>
        </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
