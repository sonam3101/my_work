# Testing VidSave

## Backend

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies: `pip install -r requirements.txt`.
3. Start the API server: `FLASK_APP=backend.app flask run` or `python backend/app.py`.
4. In a separate terminal, verify the health endpoint: `curl http://127.0.0.1:5000/api/health` (expect `{"status": "ok"}`).
5. Check metadata extraction: `curl -X POST http://127.0.0.1:5000/api/info -H 'Content-Type: application/json' -d '{"url": "<video_url>"}'`.
6. Trigger a download: `curl -X POST http://127.0.0.1:5000/api/download -H 'Content-Type: application/json' -d '{"url": "<video_url>"}' --output sample.mp4` and ensure the file saves.

## Frontend

With the backend running, open `index.html` in a browser or serve it with a static file server. Paste a supported URL, wait for formats to load, choose an option, and confirm the browser saves the video file.
