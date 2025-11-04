import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, jsonify, request, send_file, after_this_request
from werkzeug.exceptions import HTTPException
import yt_dlp

app = Flask(__name__)


class ClientError(Exception):
    """Error raised for invalid client input."""


URL_PATTERN = re.compile(r"^https?://")


def validate_url(url: Optional[str]) -> str:
    if not url:
        raise ClientError("A media URL is required.")
    if not URL_PATTERN.match(url):
        raise ClientError("Only http(s) URLs are supported.")
    return url


def build_downloader_opts(tmpdir: Path, download_format: Optional[str]) -> Dict:
    format_selector = download_format or "bv*+ba/b"
    return {
        "format": format_selector,
        "outtmpl": str(tmpdir / "%(title).200s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "restrictfilenames": True,
        "nocheckcertificate": True,
    }


@app.errorhandler(Exception)
def handle_error(exc):
    if isinstance(exc, ClientError):
        response = {"error": str(exc)}
        return jsonify(response), 400
    if isinstance(exc, HTTPException):
        return jsonify({"error": exc.description}), exc.code
    app.logger.exception("Unexpected server error")
    return jsonify({"error": "The server encountered an unexpected error."}), 500


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/info")
def video_info():
    payload = request.get_json(silent=True) or {}
    url = validate_url(payload.get("url"))

    ydl_opts = {"skip_download": True, "quiet": True, "nocheckcertificate": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    response = {
        "title": info.get("title"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader"),
        "thumbnail": info.get("thumbnail"),
        "webpage_url": info.get("webpage_url"),
        "formats": [
            {
                "format_id": fmt.get("format_id"),
                "ext": fmt.get("ext"),
                "resolution": fmt.get("resolution") or fmt.get("format_note"),
                "filesize": fmt.get("filesize") or fmt.get("filesize_approx"),
                "vcodec": fmt.get("vcodec"),
                "acodec": fmt.get("acodec"),
            }
            for fmt in info.get("formats", [])
            if fmt.get("acodec") != "none" or fmt.get("vcodec") != "none"
        ],
    }
    return jsonify(response)


@app.post("/api/download")
def download_video():
    payload = request.get_json(silent=True) or {}
    url = validate_url(payload.get("url"))
    download_format = payload.get("format")

    tmpdir = Path(tempfile.mkdtemp(prefix="vidsave-"))
    ydl_opts = build_downloader_opts(tmpdir, download_format)

    downloaded_path: Optional[Path] = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = Path(ydl.prepare_filename(info))
    except yt_dlp.utils.DownloadError as exc:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise ClientError(str(exc).split("\n")[0])
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise

    if not downloaded_path or not downloaded_path.exists():
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise ClientError("The video could not be downloaded.")

    filename = downloaded_path.name

    def cleanup():
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            app.logger.warning("Failed to clean temporary directory %s", tmpdir)

    @after_this_request
    def remove_tmpdir(response):  # type: ignore[override]
        cleanup()
        return response

    return send_file(
        downloaded_path,
        as_attachment=True,
        download_name=filename,
        mimetype="application/octet-stream",
        max_age=0,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
