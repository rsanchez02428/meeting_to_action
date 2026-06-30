""" 
api.py - FastAPI endpoints for the Meeting-to-Action system.

CONCEPT: FastAPI is a Python web framework. It lets you define 
URL endpoints (like /transcribe and /analyze) that accept requests
and return responses. It's the industry standard for Python APIs.

Key FastAPI concepts:
- @app.post("/path") defines an endpoint that accepts POST requests
- Pydantic models (BaseModel) validate incoming data automatically
- UploadFile handles file uploads (like audio files)
- BackgroundTasks let you run slow operations without blocking
"""

import os
import json
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException,BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from src.transcriber import transcribe_audio, transcribe_long_audio
from src.extractor import extract_meeting_data
from src.verifier import verify_extraction, apply_corrections
from src.integrations.slack_bot import send_to_slack
from src.integrations.notion_client import push_action_items

# Create the FastAPI app
app = FastAPI(
    title="Meeting-to-Action Intelligence System",
    description="Upload a meeting recording -> Get structured action items",
    version="1.0.0"
)

# === Pydantic Models ===
# These define the shape of your request/response data.
# FastAPI uses them for automatic validation and documentation.

class AnalysisOptions(BaseModel):
    """Options the user can set when submitting a meeting."""
    slack_channel: Optional[str] = None     # If set, sends results to this Slack channel
    push_to_notion: bool = False            # If True, creates Notion tasks
    language: Optional[str] = None          # ISO language code for transcription


class MeetingResult(BaseModel):
    """The full result returned to the user."""
    transcript: str
    meeting_summary: str
    decisions: list
    action_items: list 
    open_questions: list
    attendees_mentioned: list
    verification_status: str 
    slack_sent: bool=False
    notion_tasks_created: int=0


# === Endpoits ===

@app.get("/")
def root():
    """Health check endpoint. Useful for monitoring."""
    return {"status": "running", "service": "Meeting-to-Action Intelligence System"}


@app.post("/analyze", response_model=MeetingResult)
async def analyze_meeting(
    audio_file: UploadFile = File(...),
    slack_channel: Optional[str] = None,
    push_to_notion: bool = False,
    language: Optional[str] = None
):
    """ 
    Full pipeline: Audio -> Transcript -> Extraction -> Verification -> Delivery

    This single endpoint orchestrates the entire system. Upload an audio
    file and get back structured meeting intelligence.

    CONCEPT: This is the "orchestrator" pattern. One endpoint coordinates
    multiple interal services (transcription, extraction, verification,
    delivery). Each service is independent and testable on its own, 
    but this endpoint ties them together into a complete workflow.
    """

    # Validate file type
    allowed_types = {"audio/mpeg", "audio/wav", "audio/mp4", "audio/webm",
                     "audio/x-m4a"}
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {audio_file.content_type}. "
                   f"Supported: mp3, wav, mp4, webm, m4a"
        )
    
    # Save uploaded file to a temporary location
    # CONCEPT: UploadFile gives us a file-like object in memory.
    # Whisper API needs an actual file on disk, so we save it temporarily.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        content = await audio_file.read()
        tmp.write(content)
        temp_path = tmp.name

    try:
        # Step 1: Transcribe
        print("Step 1: Transcribing audio...")
        transcript_data = transcribe_audio(temp_path)
        transcript = transcript_data["text"]

        # Step 2: Extract structured data
        print("Step 2: Extracting meeting data...")
        extraction = extract_meeting_data(transcript)

        # Step 3: Verify
        print("Step 3: Verifying extraction...")
        verification = verify_extraction(transcript, extraction)
        final_data = apply_corrections(extraction, verification)

        # Step 4: Deliver (optional)
        slack_sent = False
        notion_count = 0

        if slack_channel:
            print(f"Step 4a: Sending to Slack #{slack_channel}...")
            slack_sent = send_to_slack(slack_channel, final_data)

        if push_to_notion:
            print("Step 4b: Pushing to Notion...")
            results = push_action_items(final_data)
            notion_count = len(results)

        # Build response
        return MeetingResult(
            transcript=transcript,
            meeting_summary=final_data.get("meeting_summary", ""),
            decisions=final_data.get("decisions", []),
            action_items=final_data.get("action_items", []),
            open_questions=final_data.get("open_questions", []),
            attendees_mentioned=final_data.get("attendees_mentioned", []),
            verification_status=verification.get("verification_status", "unknown"),
            slack_sent=slack_sent,
            notion_tasks_created=notion_count
        )
    
    finally:
        # Always clean up the temp file
        os.unlink(temp_path)

@app.post("/analyze-text")
async def analyze_text(transcript: str, slack_channel: Optional[str]=None):
    """ 
    Analyze a pre-existing transcript (skip the transcription step).
    Useful for testing or when you already have a transcript.
    """
    extraction = extract_meeting_data(transcript)
    verification = verify_extraction(transcript, extraction)
    final_data = apply_corrections(extraction, verification)

    slack_sent = False
    if slack_channel:
        slack_sent = send_to_slack(slack_channel, final_data)

    return {
         "data": final_data,
         "verification_check": verification.get("verification_status"),
         "slack_sent": slack_sent
    }