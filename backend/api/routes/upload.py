from typing import Annotated
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.api.schemas import UploadResponse
from backend.config import PROJECT_ROOT
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from backend.api.dependencies import get_current_user

router=APIRouter()

UPLOAD_DIR=PROJECT_ROOT/"data"/"uploads"
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)

UPLOAD_MAX_AGE_HOURS = 24

# ---------------------------------
# Allowed file types and size limit
# ---------------------------------

ALLOWED_EXTENSIONS = {
    ".pdf", ".mp3", ".wav", ".m4a",
    ".jpg", ".jpeg", ".png"
}

MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ---------------------------------
# Helpers
# ---------------------------------

def validate_file(file:UploadFile)->None:
    suffix=Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{suffix}' not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )

def safe_filename(original:str)->str:
    """
    Generate a unique filename to prevent collisions and strip any path components from the original name.
    """
    suffix=Path(original).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


async def cleanup_old_uploads():
    """
    Delete uploaded files older than UPLOAD_MAX_AGE_HOURS.
    Called once at startup and can be scheduled as a background task.
    """
    now = datetime.now(timezone.utc)
    deleted = 0

    for file_path in UPLOAD_DIR.iterdir():
        if not file_path.is_file():
            continue
        age_hours = (now.timestamp() - file_path.stat().st_mtime) / 3600
        if age_hours > UPLOAD_MAX_AGE_HOURS:
            file_path.unlink(missing_ok=True)
            deleted += 1

    if deleted:
        print(f"[cleanup] Deleted {deleted} expired upload(s).")

# ---------------------------------
# Routes
# ---------------------------------

@router.post("/upload",response_model=UploadResponse)
async def upload_files(
    files: Annotated[list[UploadFile], File(description="Upload one or more files")],
    current_user: dict = Depends(get_current_user)
):
    """
    Upload one or more files.
    Returns saved file paths for use in /chat requests.
    """
    if not files:
        raise HTTPException(status_code=400,detail="No files provided.")

    if len(files)>10:
        raise HTTPException(status_code=400,detail="Maximum 10 files per upload.")

    saved_paths=[]
    saved_names=[]

    for file in files:

        # validate extension
        validate_file(file)

        # read and validate size
        contents=await file.read()

        if len(contents)>MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' exceeds {MAX_FILE_SIZE_BYTES}MB limit."
            )
        
        # save with unique name to prevent collisions
        unique_name=safe_filename(file.filename)
        save_path=UPLOAD_DIR/unique_name

        save_path.write_bytes(contents)

        saved_paths.append(str(save_path))
        saved_names.append(file.filename)

    return UploadResponse(
        file_paths=saved_paths,
        file_names=saved_names,
        count=len(saved_paths)
    )