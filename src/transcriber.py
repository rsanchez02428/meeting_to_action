""" 
transciber.py - Converts meeting audio to text using OpenAI Whisper API.

CONCEPT: This module handles the first step of our pipeline:
Audio File -> Text Transcript

The Whisper API accepts an audio file and resturns text. We can also 
request timestamps and speaker segemetnts to make the transcript
more useful for downstream processing.
"""

import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

# Initialize OpenAI client
# This creates a reusable connection to OpenAI's servers
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(file_path: str, language: str = None) -> dict:
    """
    Transcribe an audio file using OpenAI's Whisper API.
    
    Parameters:
    -----------
    file_path : str
        Path to the audio file (mp3, wav, m4a, mp4, webm)
    language : str, optional
        ISO 639-1 language code (e.g., "en" for English).
        If None, Whisper auto-detects the language.
    
    Returns:
    --------
    dict with keys:
        - text: Full transcript as a string
        - segments: List of timed segments (if using verbose_json)
        - language: Detected language code
    
    LEARNING NOTE:
    The 'response_format' parameter controls what Whisper returns:
    - "text" → Just the raw text string
    - "json" → Text + language
    - "verbose_json" → Text + language + word-level timestamps + segments
    
    We use "verbose_json" because we want the segments — they help us
    identify where different topics were discussed in the meeting.
    """
    
    # Validate the file exists and is a supported format
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    supported_formats = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".mpeg",
                         ".mpga"}
    if path.suffix.lower() not in supported_formats: 
        raise ValueError(f"Unsupported audio format: {path.suffix}. Use: {supported_formats}")
    
    # Check file size (Whisper API limit is 25MB)
    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb > 25:
        raise ValueError(f"File is {file_size_mb:.1f}MB. Whisper limit is 25MB. "
                         "Split the file first (see split_audio function)."
                         )
    
    # Make the API call
    # 'rb' means 'read binary' - audio files are binary data, not text
    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",      # Currently the only Whisper model available
            file=audio_file,
            response_format="verbose_json",     # Get segments and timestamps
            language=language,    # None = auto-detect language
            timestamp_granularities=["segment"] # Get segment-level timestamps
        )

    return {
        "text": response.text,
        "segments": [
            {
                "start": seg.start,     # Start time in seconds
                "end": seg.end,     # End time in seconds
                "text": seg.text.strip()    # The spoken text in this segment
            }
            for seg in (response.segments or [])
        ],
        "language": response.language
    }

def split_audio(file_path: str, chunk_minutes: int = 10) -> list[str]:
    """
    Split a large audio file into smaller chunks for Whisper.
    
    CONCEPT: If your meeting recording is longer than 25MB, you need
    to split it. This uses pydub (pip install pydub), which also
    requires ffmpeg to be installed on your system.
    
    Install ffmpeg:
    - Mac: brew install ffmpeg
    - Ubuntu: sudo apt install ffmpeg
    - Windows: download from ffmpeg.org and add to PATH
    """
    try: 
        from pydub import AudioSegment
    except ImportError:
        raise ImportError("Install pydub: pip install pydub (also need ffmpeg)")
    
    audio = AudioSegment.from_file(file_path)
    chunk_ms = chunk_minutes * 60 * 1000  # Convert minutes to milliseconds

    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]
        chunk_path = f"outputs/chunk_{i}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunks.append(chunk_path)
    
    return chunks

def transcribe_long_audio(file_path:str) -> dict:
    """
    Handle audio files of any length by splitting and recombining.
    
    CONCEPT: This is a common pattern in AI engineering — when an API
    has input size limits, you split the input, process each piece,
    and stitch the results back together. The tricky part is handling
    the boundaries (a sentence might get cut in half between chunks).
    """
    path = Path(file_path)
    file_size_mb = path.stat().st_size / (1024 * 1024)

    if file_size_mb <= 25:
        return transcribe_audio(file_path)
    
    print(f"File is {file_size_mb:.1f}MB, splitting into chunks...")
    chunk_paths = split_audio(file_path)

    all_text = []
    all_segments = []
    time_offset = 0     # Track cumulative time across chunks

    for chunk_path in chunk_paths:
        result = transcribe_audio(chunk_path)
        all_text.append(result["text"])

        # Adjust segment timestamps to be relative to the full recording
        for seg in result["segments"]:
            seg["start"] += time_offset
            seg["end"] += time_offset
            all_segments.append(seg)
            
        # Update offset for next chunk
        if result["segments"]:
            time_offset = result["segments"][-1]["end"]
        
        # Clean up chunk file
        os.remove(chunk_path)
    
    return {
        "text": " ".join(all_text),
        "segments": all_segments,
        "language": "en"
    }

# === TEST IT ===
if __name__ == "__main__":
    """
    LEARNING NOTE: This block only runs when you run this file direclty
    (python src/transciber.py), not when it's imported by another file.

    To test: Get a sample audio file. You can:
    1. Record a 2-minute fake meeting on your phone with a freind. 
    Make sure to include:
        - A decision
        - Action items
        - An open question
    2. Use a podcast clip: Download any 5-minute podcast segment as an mp3.
    3. Text-to-speech: Use a TTS tool (like https://ttsmp3.com/) to generate a sample audio file from text.

    Save it to samples/test_meeting.mp3
    """
    import json

    result = transcribe_audio("samples/test_meeting_3.m4a")

    print(f"Language detected: {result['language']}")
    print(f"Total segments: {len(result['segments'])}")
    print(f"\n--- TRANSCRIPT ---\n")
    print(result["text"][:500])  # Print first 500 chars

    # Save full result for the next phase
    with open("outputs/transcript_3.json", "w") as f:
        json.dump(result, f, indent=2)

    print("\nSaved to outputs/transcript_3.json")
