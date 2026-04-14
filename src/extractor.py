""" 
extractor.py - Extracts structured meeting data using Claude API.

CONCEPT: This is where prompt engineeing becomes real engineering.
I amd building a reliable system that:
1. Loads a prompt template
2. Injects the transcript
3. Calls the Claude API
4. Parses and validates the JSON response
5. Handles errors gracefully

KEY LEARNING: The difference between a demo and production code is
error handling. LLMs sometimes return invalid JSON, forget fields, 
or hallucinate. We need to catch all of that.
"""

import os
import json
import re
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts/ directory.

    CONCEPT: Storing prompts in seperate files (not inline in code) is
    a best practice because:
    1. You can version control prompt changes independently
    2. Non-engineers can review and edit prompts
    3. You can A/B test different prompt versions easily
    4. It keeps your code clean and readable
    """
    prompt_path = Path("prompts") / prompt_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()

def extract_meeting_data(transcript: str, prompt_version: str = "extraction_v1.txt") -> dict:
    """
    Extract structured data from a meeting transcript using Claude.
    
    Parameters:
    -----------
    transcript: str
        The full text transcript from Whisper
    prompt_version: str
        Which prompt template to use (enables A/B testing)
    
    Returns:
    --------
    dict: Parsed meeting data with all extracted fields

    CONCEPT: API Parameters Explained
    ----------------------------------
    model: Which Claude model to use. "claude-sonnet-4-2025514" is
    recommended - 
        it's fast, capable, and cheaper than Opus for this task.
    
    max_tokens: Maximum number of tokens (rouphly words) in the response.
                A 1-hour meeting might generate ~ 2000 tokens of structured 
                output.
                Set this higher than you expect to need.
    
    temperature: Controls randomness. Range is 0-1.
                    0 = most deterministic (same input -> same output)
                    1 = most creative/ random
                    For extraction tasks, use 0 - we want consistency, not 
                    creativity.

    messages: The conversation format. Each message has a role and content.
                "user" = your input. "assistant" = the model's response.
    """

    # Load and fill the prompt template
    prompt_template = load_prompt(prompt_version)
    full_prompt = prompt_template.replace("{transcript}", transcript)

    # Call the Claude API
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0, 
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ]
    )

    # Extract the text content from Claude's response
    # The response object has a 'content' list with text blocks
    raw_text = response.content[0].text

    # Parse the JSON response
    parsed = parse_llm_json(raw_text)

    # Validate required fields exist
    validated = validate_extraction(parsed)

    return validated

def parse_llm_json(raw_text: str) -> dict:
    """
    Safely parse JSON from LLM output, handling common issues.
    
    CONCEPT: LLMs don't always return perfect JSON. Common problems:
    1. They wrap it in ```json ... ``` markdown code fences
    2. They add a preamble like "Here's the extracted data:"
    3. They use single quotes instead of double quotes
    4. They include trailing commas (invalid JSON)
    5. They return "None" instead of null

    A robust parser handles all  of these. This is the kind of detail 
    seperates production code from tutorial code.
    """

    text = raw_text.strip()

    # Remove markcode code fences if present
    if text.startswith("```"):
        # Find the first newline after ``` (skips ```json)
        first_newline = text.index("\n")
        # Find the closing ```
        last_fence = text.rfind("```")
        text = text[first_newline + 1: last_fence].strip()
    
    # Try to find JSON object in the text (in case of preamble)
    if not text.startswith("{"):
        start = text.find("{")
        if start == -1:
            raise ValueError(f"No JSOn object found in response: {text[:200]}")
        # Find the matching closing brace 
        end = text.rfind("}") + 1
        text = text[start:end]
    
    # Fix trailing commas before } or ] (invalid JSON but common LLM output)
    text = re.sub(r',\s*([}\]])', r'\1', text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON from LLM response.\n"
            f"Error: {e}\n"
            f"Raw text (first 500 chars): {raw_text[:500]}"
        )

def validate_extraction(data: dict) -> dict:
    """
    Validate that all required fields exist and have correct types.

    CONCEPT: Defensive programming. Even if the LLM returns valid JSON,
    it might be missing fields we need, or have wrong types. We check 
    everythign and provide defaults where safe to do so.

    This is critical production skill - the AI is your "junior 
    employee" and you need to check its work.
    """

    # Define required fields and their expected types
    required_fields = {
        "meeting_summary": str,
        "key_topics": list,
        "decisions": list,
        "action_items": list, 
        "open_questions": list,
        "attendees_mentioned": list
    }

    for field, expected_type in required_fields.items():
        if field not in data:
            # Provide safe defaults rather than crashing
            if expected_type == str:
                data[field] = "Not available"
            elif expected_type == list:
                data[field] = []
            elif expected_type == bool:
                data[field] = False
        elif not isinstance(data[field], expected_type):
            raise ValueError(
                f"Field '{field}' should be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )
    
    # Validate each action item has required sub-fields
    for i, item in enumerate(data.get("action_items", [])):
        if "task" not in item:
            raise ValueError(f"Action item {i} missing 'task' field")
        # Apply defaults for optional sub-fields
        item.setdefault("owner", "Unassigned")
        item.setdefault("deadline", "Not specified")
        item.setdefault("priority", "medium")
        item.setdefault("context", "")
    
    return data


# === TEST IT ===
if __name__ == "__main__":
    # Load the transcript from Phase 2
    transcript_path = "outputs/transcript_3.json"

    if not Path(transcript_path).exists():
        # Use a sample transcript for testing
        sample_transcript = """ 
        Alright everyone, let's get started. So first up, the Q3 marketing 
        campaign. We've been going back and forth on this, but I think we 
        should go with the social media first approach. The data from last 
        quarter shows 3x better engagement on Instagram compared to email.
        
        Mike, can you put together the social media content calendar by 
        next Monday? We need to start posting by the 15th. This is our 
        top priority for the quarter.
        
        Also, Sarah, the analytics dashboard is still showing stale data. 
        Can you look into why the pipeline is broken? It's not urgent 
        but we need it fixed before the board meeting on March 30th.
        
        One thing we still need to figure out — should we hire a 
        freelance designer or try to do the creative in-house? Lisa, 
        do you have any sense of the budget implications? Let's discuss 
        that in our next meeting.
        
        Oh, and good news — the client approved the Phase 2 proposal. 
        We're officially green-lit for the expansion. Budget is confirmed 
        at $150K.
        
        I think that's everything. Let's reconvene Thursday to review 
        Mike's content calendar. Thanks everyone.
        """
    else:
        with open(transcript_path) as f:
            data = json.load(f)
        sample_transcript = data["text"]

    print("Extracting meeting data...")
    result = extract_meeting_data(sample_transcript)

    print("\n=== EXTRACTED DATA ===\n")
    print(json.dumps(result, indent=2))

    # Save for the next phase
    with open("outputs/extraction_3.json", "w") as f:
        json.dump(result, f, indent=2)

    print("\nSaved to outputs/extraction_3.json")
    
    # Print a quick summary
    print(f"\n--- QUICK STATS ---")
    print(f"Topics discussed: {len(result.get('key_topics', []))}")
    print(f"Decisions made: {len(result.get('decisions', []))}")
    print(f"Action items: {len(result.get('action_items', []))}")
    print(f"Open questions: {len(result.get('open_questions', []))}")