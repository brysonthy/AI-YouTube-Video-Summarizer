"""Configuration for summarize_video.py."""
import os

from dotenv import load_dotenv

# Load variables from the .env file in this folder
load_dotenv()

# Credentials (defined in .env)
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")

# Video to summarize
YOUTUBE_URL = "https://www.youtube.com/watch?v=dJJ77spomeU"

# Model settings
MODEL = "@cf/meta/llama-3.1-8b-instruct-fp8"
SYSTEM_PROMPT = "You summarize YouTube video transcripts clearly and concisely."
MAX_TOKENS = 512      # max tokens per generated summary
CHUNK_CHARS = 12000   # long transcripts are split into pieces of about this size

# Speech-to-text fallback (used when a video has no captions)
WHISPER_MODEL = "@cf/openai/whisper-large-v3-turbo"
AUDIO_CHUNK_SECONDS = 300  # audio is split into 5-minute pieces before upload