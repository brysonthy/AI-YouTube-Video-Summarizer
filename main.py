"""
Summarize a YouTube video with Cloudflare Workers AI.

Uses the video's captions when available; otherwise downloads the audio and
transcribes it with Whisper, then summarizes the text with Llama.

Setup:
    pip install requests youtube-transcript-api yt-dlp imageio-ffmpeg python-dotenv

Set the video URL, models and credentials in settings.py / .env.
"""
import base64
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import imageio_ffmpeg
import requests
import yt_dlp
from youtube_transcript_api import CouldNotRetrieveTranscript, YouTubeTranscriptApi

import settings

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()  # bundled ffmpeg, no system install needed
HEADERS = {"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"}


def api_url(model: str) -> str:
    return (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{settings.CLOUDFLARE_ACCOUNT_ID}/ai/run/{model}"
    )


def run_model(model: str, payload: dict) -> dict:
    response = requests.post(api_url(model), headers=HEADERS, json=payload, timeout=300)
    if not response.ok:
        raise SystemExit(f"Request failed ({response.status_code}): {response.text}")
    return response.json()["result"]


def get_video_id(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")
    if parsed.path == "/watch":
        return parse_qs(parsed.query)["v"][0]
    match = re.match(r"^/(embed|shorts|live)/([\w-]{11})", parsed.path)
    if match:
        return match.group(2)
    raise ValueError(f"Could not find a video ID in: {url}")


def transcribe_audio(audio: bytes) -> str:
    result = run_model(
        settings.WHISPER_MODEL, {"audio": base64.b64encode(audio).decode()}
    )
    return result["text"].strip()


def transcribe_video(url: str) -> str:
    """Download the audio, split it into pieces, and transcribe each with Whisper."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        options = {
            "format": "bestaudio/best",
            "outtmpl": str(tmp / "audio.%(ext)s"),
            "ffmpeg_location": FFMPEG,
            "quiet": True,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "32"}
            ],
            "postprocessor_args": ["-ac", "1", "-ar", "16000"],  # mono, 16 kHz = small files
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        subprocess.run(
            [
                FFMPEG, "-i", str(tmp / "audio.mp3"),
                "-f", "segment", "-segment_time", str(settings.AUDIO_CHUNK_SECONDS),
                "-c", "copy", str(tmp / "part_%03d.mp3"),
            ],
            check=True,
            capture_output=True,
        )
        parts = sorted(tmp.glob("part_*.mp3"))
        return " ".join(transcribe_audio(p.read_bytes()) for p in parts)


def get_transcript(url: str) -> str:
    try:
        snippets = YouTubeTranscriptApi().fetch(get_video_id(url))
        return " ".join(s.text for s in snippets)
    except CouldNotRetrieveTranscript:
        print("No captions available, transcribing the audio instead (this takes a while)...")
        return transcribe_video(url)


def summarize(text: str) -> str:
    result = run_model(
        settings.MODEL,
        {
            "messages": [
                {"role": "system", "content": settings.SYSTEM_PROMPT},
                {"role": "user", "content": f"Summarize this text:\n\n{text}"},
            ],
            "max_tokens": settings.MAX_TOKENS,
        },
    )
    # Some models return {"response": ...}, others an OpenAI-style "choices" list
    if "response" in result:
        return result["response"]
    return result["choices"][0]["message"]["content"]


def chunk(text: str, size: int) -> list[str]:
    chunks, current = [], ""
    for word in text.split():
        if current and len(current) + len(word) + 1 > size:
            chunks.append(current)
            current = ""
        current += (" " if current else "") + word
    if current:
        chunks.append(current)
    return chunks


transcript = get_transcript(settings.YOUTUBE_URL)

# Summarize each chunk, then summarize the combined summaries if there were several
parts = [summarize(c) for c in chunk(transcript, settings.CHUNK_CHARS)]
summary = parts[0] if len(parts) == 1 else summarize(" ".join(parts))

print(summary)