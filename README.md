# YouTube Video Summarizer (Cloudflare Workers AI)

Give it a YouTube URL and it prints a short summary of the video.

It uses the video's captions when they exist. If the video has none, it downloads the audio, transcribes it with Whisper, and summarizes the text with Llama. All AI calls run on Cloudflare Workers AI.

## How it works

```
YouTube URL (settings.py)
        │
        ▼
 Get the video ID
        │
        ▼
 Fetch captions ──── found ────────────────────┐
 (youtube-transcript-api)                      │
        │ not available                        │
        ▼                                      │
 Download audio (yt-dlp)                       │
        │                                      │
        ▼                                      │
 Convert to small mono MP3 and                 │
 split into 5-minute pieces (ffmpeg)           │
        │                                      │
        ▼                                      │
 Transcribe each piece                         │
 (Whisper on Workers AI)                       │
        │                                      │
        ▼                                      ▼
              Full transcript text
                        │
                        ▼
      Split into chunks (about 12,000 characters)
                        │
                        ▼
      Summarize each chunk (Llama on Workers AI)
                        │
                        ▼
      If there were several chunks, summarize the
      chunk summaries into one final summary
                        │
                        ▼
                  Print the summary
```

### Step by step

1. **Video ID.** `get_video_id()` pulls the ID out of `youtube.com/watch?v=`, `youtu.be/`, `/shorts/`, `/embed/` and `/live/` links.
2. **Captions first.** `get_transcript()` asks YouTube for the captions (uploaded or auto-generated). This is fast and free.
3. **Speech-to-text fallback.** If captions can't be retrieved, `transcribe_video()` downloads the audio with `yt-dlp`, converts it to small mono 16 kHz MP3 files, and splits it into 5-minute pieces. Each piece is sent to Whisper (base64-encoded) and the text is joined together. This is slower and uses more of your Cloudflare free allowance.
4. **Chunking.** Long transcripts are split into pieces of about `CHUNK_CHARS` characters so they fit in the model's input.
5. **Summarizing.** Each chunk is sent to the Llama model with a prompt asking for a summary. If there was more than one chunk, the partial summaries are summarized again into one final summary.
6. **Output.** The summary is printed to the terminal.

Calls to Cloudflare use the REST API directly with `requests` (`https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/run/<model>`), not the `cloudflare` Python SDK, which failed on model names containing slashes in testing.

## Files

| File | Purpose |
|---|---|
| `summarize_video.py` (your `main.py`) | The program: captions, transcription, chunking, summarizing |
| `settings.py` | All configuration: video URL, models, limits, prompt |
| `.env` | Your Cloudflare credentials (keep private) |

## Setup

1. **Install Python packages** (inside your virtual environment):

   ```
   pip install requests youtube-transcript-api yt-dlp imageio-ffmpeg python-dotenv
   ```

   `imageio-ffmpeg` bundles an `ffmpeg` binary, so you don't need to install ffmpeg separately.

2. **Create a `.env` file** in the same folder, with no quotes or spaces around the `=`:

   ```
   CLOUDFLARE_ACCOUNT_ID=your_account_id
   CLOUDFLARE_API_TOKEN=your_api_token
   ```

   - The account ID is on the Cloudflare dashboard (Workers & Pages overview).
   - Create the API token under My Profile → API Tokens, with Workers AI permissions.
   - If you use git, add `.env` to `.gitignore`.

3. **Set the video** in `settings.py`:

   ```python
   YOUTUBE_URL = "https://www.youtube.com/watch?v=VIDEO_ID"
   ```

4. **Run it:**

   ```
   python summarize_video.py
   ```

   (or `python main.py` if you kept that file name)

## Settings (`settings.py`)

| Setting | Default | Meaning |
|---|---|---|
| `YOUTUBE_URL` | placeholder | Video to summarize |
| `MODEL` | `@cf/meta/llama-3.1-8b-instruct-fp8` | Model used for summaries |
| `SYSTEM_PROMPT` | "You summarize YouTube video transcripts clearly and concisely." | Edit to change the style, e.g. ask for bullet points |
| `MAX_TOKENS` | `512` | Maximum length of each summary |
| `CHUNK_CHARS` | `12000` | Approximate transcript size per summarizing call |
| `WHISPER_MODEL` | `@cf/openai/whisper-large-v3-turbo` | Speech-to-text model for videos without captions |
| `AUDIO_CHUNK_SECONDS` | `300` | Length of each audio piece sent to Whisper |

### Choosing a model

All Workers AI models draw from the same daily free allowance, and bigger models use more of it. Check Cloudflare's pricing page for current limits.

| Model | Quality | Allowance use |
|---|---|---|
| `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Best | Heaviest |
| `@cf/google/gemma-4-26b-a4b-it` | Very good | Medium |
| `@cf/meta/llama-3.1-8b-instruct-fp8` | Good | Light |
| `@cf/meta/llama-3.2-3b-instruct` | Decent | Lightest |

To switch, change `MODEL` in `settings.py`. Model availability changes over time. For example, `@cf/facebook/bart-large-cnn` was retired on 2026-05-30.

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `ValueError: Expected a non-empty value for account_id` | `.env` is missing, misnamed (e.g. `.env.txt`), or in a different folder |
| `Request failed (410) ... deprecated` | The model was retired. Pick another from the Cloudflare model catalog and set `MODEL` |
| `Request failed (400) ... max_tokens` | Lower `MAX_TOKENS` to the limit the error message names |
| `No captions available` / `TranscriptsDisabled` | The video has no captions, or YouTube is blocking your connection. The script falls back to speech-to-text automatically |
| `yt-dlp` download errors | Update it with `pip install -U yt-dlp`. If YouTube is blocking your network, try another network or video |
| Whisper request fails | Check the error text from Cloudflare; the model name or request format may have changed |
| Slow run on a long video | Speech-to-text makes one Whisper call per 5 minutes of audio. Try a short video first |

## Limitations

- Summary quality depends on the model and on the transcript quality. Auto-generated captions can contain mistakes.
- Videos with no speech, or in languages the chosen models handle poorly, may give poor results.
- Download and transcription may be blocked by YouTube for some networks (VPNs, cloud servers).
- Only use videos you have the right to process, and follow YouTube's terms of service.
