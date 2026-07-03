import os
import subprocess
import tempfile
import math
import shutil
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import AsyncGroq
from backend.config import PROJECT_ROOT, MAX_CHUNK_MB, MAX_WORKERS, AUDIO_MODEL
from backend.utils.retry import async_llm_retry, llm_retry

client = AsyncGroq()


def split_audio_ffmpeg(audio_path: str, target_chunk_mb: int = MAX_CHUNK_MB):
    """Split large audio files into chunks using ffmpeg."""
    path = Path(audio_path)
    size_mb = path.stat().st_size / (1024 * 1024)

    if size_mb <= target_chunk_mb:
        return [str(path)], None      # consistent tuple return

    duration_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]
    duration = float(subprocess.check_output(duration_cmd).decode().strip())
    num_chunks = math.ceil(size_mb / target_chunk_mb)
    chunk_duration = duration / num_chunks
    temp_dir = tempfile.mkdtemp()
    chunk_paths = []

    for i in range(num_chunks):
        start_time = i * chunk_duration
        output_file = os.path.join(temp_dir, f"chunk_{i}.mp3")
        cmd = [
            "ffmpeg", "-y", "-i", str(path),
            "-ss", str(start_time),
            "-t", str(chunk_duration),
            output_file
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        chunk_paths.append(output_file)

    return chunk_paths, temp_dir


# ---------------------------------
# Retryable internal calls
# ---------------------------------

async def _transcribe_single(path: Path) -> str:
    """Single file async transcription with retry."""
    async def _invoke():
        with open(path, "rb") as f:
            result = await client.audio.transcriptions.create(
                file=f,
                model=AUDIO_MODEL
            )
        return result.text

    return await async_llm_retry(_invoke)


# Sync version kept for ThreadPoolExecutor chunks
@llm_retry
def _transcribe_chunk_sync(chunk_path: str) -> tuple[int, str]:
    """Sync chunk transcription with retry — runs inside ThreadPoolExecutor."""
    import groq
    sync_client = groq.Groq()
    with open(chunk_path, "rb") as f:
        result = sync_client.audio.transcriptions.create(
            file=f,
            model=AUDIO_MODEL
        )
    chunk_num = int(Path(chunk_path).stem.split("_")[-1])
    return chunk_num, result.text


# ---------------------------------
# Main function
# ---------------------------------

async def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe audio using Groq Whisper.
    Automatically chunks large audio files and
    transcribes chunks in parallel.
    """
    temp_dir = None

    try:
        path = Path(audio_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path = path.resolve()

        if not path.exists():
            return {"success": False, "error": f"Audio file not found: {path}"}

        size_mb = path.stat().st_size / (1024 * 1024)

        # ----------------------------
        # Small File — fully async
        # ----------------------------
        if size_mb <= MAX_CHUNK_MB:
            transcript = await _transcribe_single(path)
            return {
                "success": True,
                "file_path": str(path),
                "num_chunks": 1,
                "transcript": transcript
            }

        # ----------------------------
        # Large File — chunk in thread pool
        # ----------------------------
        chunk_paths, temp_dir = await asyncio.to_thread(split_audio_ffmpeg, str(path))
        transcripts = {}

        # ThreadPoolExecutor for chunks — sync Groq client per thread
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(chunk_paths))) as executor:
            futures = {
                executor.submit(_transcribe_chunk_sync, chunk): chunk
                for chunk in chunk_paths
            }
            for future in as_completed(futures):
                try:
                    chunk_id, text = future.result()
                    transcripts[chunk_id] = text
                except Exception as e:
                    chunk_path = futures[future]
                    chunk_num = int(Path(chunk_path).stem.split("_")[-1])
                    transcripts[chunk_num] = f"[chunk transcription failed: {str(e)}]"

        merged_transcript = "\n".join(
            transcripts[i] for i in sorted(transcripts.keys())
        )

        return {
            "success": True,
            "file_path": str(path),
            "num_chunks": len(chunk_paths),
            "transcript": merged_transcript
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)