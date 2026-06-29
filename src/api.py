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

