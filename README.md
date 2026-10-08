# YouTube Video Summarizer — Cloudflare Workers AI

A Python tool that takes a YouTube URL and generates a short, readable summary using **Cloudflare Workers AI**.

It uses **YouTube captions when available**. If captions cannot be retrieved, it automatically downloads the video's audio, transcribes it with **Whisper**, and summarizes the transcript with **Llama**.

## Features

* 🎬 Accepts standard YouTube URLs
* 📝 Uses YouTube captions when available
* 🎙️ Automatically falls back to Whisper speech-to-text
* 🤖 Summarizes transcripts with Llama on Cloudflare Workers AI
* ✂️ Splits long transcripts into manageable chunks
* 🔄 Combines multiple chunk summaries into one final summary
* ⚙️ Configuration is separated into `settings.py`
* 🔐 Cloudflare credentials are loaded from `.env`
* 💻 Runs locally with Python

## Example

### Input

**YouTube URL:**
https://www.youtube.com/watch?v=dJJ77spomeU

### Output

```text
The speaker discusses current market trends and analyzes Singaporean and Malaysian banking stocks.

Key points:

- The NASDAQ and S&P 500 have declined, but the speaker considers this manageable rather than a major concern.
- US Treasury yields have risen, contributing to significant pressure on bond prices and the broader global bond market.
- Weakness in the bond and gold markets is highlighted as an important warning signal.
- Singapore banks — DBS, OCBC, and UOB — as well as Malaysian banks, have been affected by the decline in bond prices.
- The speaker emphasizes that Singapore banks are not invincible and can experience significant declines during major market disruptions.
- The current environment is described as a K-shaped economy, where some companies and sectors continue to perform strongly while others struggle.
- The speaker attributes the market pressure to inflation, government borrowing, higher yields, and falling bond prices.

### Bank Stock Crash Analysis

The speaker uses historical data to examine DBS and OCBC, focusing on:

1. Predictability of major declines
2. Historical crash depth
3. Recovery time
4. Potential opportunities during significant market corrections

The speaker concludes that OCBC appears to be a more suitable candidate for a "crash buying" strategy, while DBS is considered less attractive for this particular approach.

### Investment Strategy

The broader strategy is to avoid assuming that large, established banks will always rise. Instead, investors can study historical crashes and prepare for periods when fundamentally strong companies become significantly cheaper.

The speaker also discusses an investing course covering:

- Investing confidence
- Crash-buying strategies
- A systematic approach to investing
- Evaluating opportunities during major market corrections

Note: This summary reflects the video's discussion and opinions. It is not financial advice or a recommendation to buy or sell any security.

### Additional Q&A

The video also includes viewer questions, including a discussion about MSM pills, which the speaker describes as natural and non-steroid-based.
```

## How It Works

```text
                    YouTube URL
                         │
                         ▼
                  Extract Video ID
                         │
                         ▼
                  Fetch Captions
                         │
             ┌───────────┴───────────┐
             │                       │
          Captions                 No captions
          available               available
             │                       │
             │                       ▼
             │                 Download Audio
             │                       │
             │                       ▼
             │              Convert + Split Audio
             │                       │
             │                       ▼
             │                 Whisper STT
             │                       │
             └───────────┬───────────┘
                         │
                         ▼
                  Full Transcript
                         │
                         ▼
              Split into Text Chunks
                         │
                         ▼
                 Llama Summarization
                         │
                         ▼
              Combine Chunk Summaries
                         │
                         ▼
                  Final Summary
                         │
                         ▼
                  Print to Terminal
```

## Processing Flow

### 1. Extract the Video ID

`get_video_id()` extracts the YouTube video ID from supported URLs including:

* `youtube.com/watch?v=...`
* `youtu.be/...`
* `youtube.com/shorts/...`
* `youtube.com/embed/...`
* `youtube.com/live/...`

### 2. Fetch Captions

`get_transcript()` attempts to retrieve the video's captions using `youtube-transcript-api`.

Both uploaded and auto-generated captions may be available.

Captions are preferred because they are:

* Faster
* Cheaper
* Easier to process
* More efficient than audio transcription

### 3. Whisper Fallback

If captions cannot be retrieved, `transcribe_video()` automatically:

1. Downloads the video's audio using `yt-dlp`
2. Converts the audio to mono 16 kHz MP3
3. Splits the audio into 5-minute segments
4. Sends each segment to Whisper on Cloudflare Workers AI
5. Combines the resulting text into one transcript

This fallback is slower and consumes more Workers AI usage.

### 4. Split the Transcript

Long transcripts are split into chunks of approximately `CHUNK_CHARS` characters.

This prevents the entire transcript from exceeding the model's input limits.

### 5. Summarize

Each transcript chunk is sent to the configured Llama model with the system prompt defined in `settings.py`.

If multiple chunks exist, their summaries are combined and summarized again to produce one final summary.

### 6. Print the Result

The final summary is printed directly to the terminal.

## Project Structure

```text
youtube-video-summarizer/
│
├── summarize_video.py     # Main program
├── settings.py            # Configuration
├── .env                   # Cloudflare credentials
├── .gitignore
└── README.md
```

`main.py` can also be used instead of `summarize_video.py` if you prefer that filename.

## Requirements

* Python 3.10+
* Cloudflare account with Workers AI access
* YouTube video URL
* Internet connection

## Installation

Create and activate a virtual environment, then install the required packages:

```bash
pip install requests youtube-transcript-api yt-dlp imageio-ffmpeg python-dotenv
```

`imageio-ffmpeg` provides an FFmpeg binary, so FFmpeg does not need to be installed separately.

## Configuration

Create a `.env` file in the project directory:

```env
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_api_token
```

### Cloudflare Account ID

Your account ID can be found in the Cloudflare dashboard under **Workers & Pages**.

### Cloudflare API Token

Create an API token from:

**Cloudflare Dashboard → My Profile → API Tokens**

The token must have permission to use Workers AI.

### Protect Your Credentials

Never commit `.env` to GitHub.

Add this to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

## Configure the Video

Edit `settings.py`:

```python
YOUTUBE_URL = "https://www.youtube.com/watch?v=VIDEO_ID"
```

Then run:

```bash
python summarize_video.py
```

Or, if your file is named `main.py`:

```bash
python main.py
```

## Settings

The main configuration is stored in `settings.py`.

| Setting               | Default                              | Description                           |
| --------------------- | ------------------------------------ | ------------------------------------- |
| `YOUTUBE_URL`         | Placeholder                          | YouTube video to summarize            |
| `MODEL`               | `@cf/meta/llama-3.1-8b-instruct-fp8` | Llama model used for summarization    |
| `SYSTEM_PROMPT`       | Summary prompt                       | Controls the summary style            |
| `MAX_TOKENS`          | `512`                                | Maximum output tokens per summary     |
| `CHUNK_CHARS`         | `12000`                              | Approximate transcript size per chunk |
| `WHISPER_MODEL`       | `@cf/openai/whisper-large-v3-turbo`  | Whisper speech-to-text model          |
| `AUDIO_CHUNK_SECONDS` | `300`                                | Length of each audio segment          |

### Example Prompt

You can change the summary style through `SYSTEM_PROMPT`.

For example:

```python
SYSTEM_PROMPT = """
You summarize YouTube video transcripts clearly and concisely.
Focus on the main arguments, important facts, conclusions, and actionable points.
Use short sections and bullet points where appropriate.
"""
```

## Choosing a Model

Cloudflare Workers AI model availability and usage limits can change over time.

Example models:

| Model                                      | Quality   | Relative Usage |
| ------------------------------------------ | --------- | -------------- |
| `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Very high | Heavy          |
| `@cf/google/gemma-4-26b-a4b-it`            | Very good | Medium         |
| `@cf/meta/llama-3.1-8b-instruct-fp8`       | Good      | Light          |
| `@cf/meta/llama-3.2-3b-instruct`           | Decent    | Lightest       |

To change the summarization model, update `MODEL` in `settings.py`.

> Model availability, pricing, and usage limits can change. Check Cloudflare's current Workers AI model catalog and pricing before relying on a specific model.

## Why the Cloudflare REST API?

The project calls Workers AI directly through Cloudflare's REST API:

```text
https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/run/<model>
```

The project uses Python `requests` rather than the Cloudflare Python SDK.

This avoids issues encountered with model names containing `/`, such as:

```text
@cf/meta/llama-3.1-8b-instruct-fp8
```

## Troubleshooting

| Error / Problem                                         | Possible Cause / Solution                                                             |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `ValueError: Expected a non-empty value for account_id` | Check that `.env` exists, is named correctly, and contains `CLOUDFLARE_ACCOUNT_ID`    |
| `.env` values are not loaded                            | Make sure the file is `.env`, not `.env.txt`, and is located in the project directory |
| `Request failed (410) ... deprecated`                   | The selected model has been retired. Choose another supported model                   |
| `Request failed (400) ... max_tokens`                   | Reduce `MAX_TOKENS` according to the limit shown in the error                         |
| `No captions available`                                 | The video has no accessible captions, so the script will attempt Whisper              |
| `TranscriptsDisabled`                                   | YouTube has disabled or restricted transcript access                                  |
| `yt-dlp` download error                                 | Update with `pip install -U yt-dlp` and try again                                     |
| Whisper request fails                                   | Check the Cloudflare error message and verify the Whisper model/request format        |
| Long video takes a long time                            | Videos without captions require one Whisper request for every audio segment           |
| Poor summary                                            | Try a stronger summarization model or improve `SYSTEM_PROMPT`                         |
| Poor transcript                                         | Auto-generated captions or Whisper may contain transcription errors                   |

## Limitations

* Summary quality depends on the quality of the transcript.
* YouTube auto-generated captions may contain errors.
* Whisper transcription can be slower for long videos.
* Videos without speech cannot be meaningfully summarized.
* Some languages may produce lower-quality transcripts or summaries.
* YouTube may block or restrict `yt-dlp` downloads depending on the network, IP address, VPN, or video.
* Cloudflare Workers AI has usage limits and model availability can change.
* Long videos without captions consume significantly more AI resources because they require Whisper transcription.

## Legal / Usage Notice

Only process videos that you have the right to process.

This project does not provide permission to download, reproduce, or redistribute copyrighted content. Users are responsible for complying with:

* YouTube's Terms of Service
* Applicable copyright laws
* Cloudflare's terms and usage policies
* The rights of video creators and copyright holders

The summaries generated by this project are automated and may contain inaccuracies.
