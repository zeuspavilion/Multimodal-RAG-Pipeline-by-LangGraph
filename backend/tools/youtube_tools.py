from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from backend.utils.retry import async_api_retry
import asyncio


# ---------------------------------
# Retryable internal calls
# ---------------------------------

async def _list_transcripts(ytt_api: YouTubeTranscriptApi, video_id: str):
    """List transcripts — offloaded to thread with retry."""
    async def _invoke():
        return await asyncio.to_thread(ytt_api.list, video_id)
    return await async_api_retry(_invoke)


async def _fetch_transcript(selected):
    """Fetch selected transcript — offloaded to thread with retry."""
    async def _invoke():
        return await asyncio.to_thread(selected.fetch)
    return await async_api_retry(_invoke)


# ---------------------------------
# Function
# ---------------------------------

async def youtube_transcript_tool(video_id: str) -> dict:
    """Fetch transcript from a YouTube video."""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = await _list_transcripts(ytt_api, video_id)

        selected = None
        for transcript in transcript_list:
            if transcript.language_code == "en":
                selected = transcript
                break

        if not selected:
            selected = next(iter(transcript_list))

        fetched = await _fetch_transcript(selected)

        transcript_text = " ".join(
            item["text"]
            for item in fetched.to_raw_data()
        )

        return {
            "success": True,
            "video_id": video_id,
            "language": selected.language_code,
            "transcript": transcript_text
        }

    except TranscriptsDisabled:
        return {
            "success": False,
            "error": "No captions available for this video"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def extract_video_id(url: str) -> str | None:
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    parsed = urlparse(url)
    return parse_qs(parsed.query).get("v", [None])[0]