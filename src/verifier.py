""" 
verifier.py - Second-pass verification of extracted meeting data.

CONCEPT: This is the "editor" to the extractor's "writer." The extraction
prompt tries to find everything. The verification prompt checks: 
1. Are the action items actually stated in the transcript?
2. Are the owners correctly identified?
3. Are there action items we missed?
4. Is the summary accurate and complete?

This dual-pass approach catches errors that a single prompt misses.
It's the same principle as code review - the seconf pair of eyes 
catches what the first missed,
"""
import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def verify_extraction(transcript: str, extracted_data: dict) -> dict:
    """
    Verify and refine the extracted meeting data.

    CONCEPT: We give the verifier BOTH the original transcript AND
    the extraction. It acts as a fact-checker, comparing claims
    against source material.

    You never trust a single LLm call for important output.
    Always verify.
    """
    verification_prompt = f"""You are a meticulous quality assurance reviewer 
    for meeting notes. 
    Your job is to compare extracted meeting data against the original 
    transcript and find any errors, omissions, or hallucinations.

    ORIGINAL TRANSCRIPT:
    {transcript}

    EXTRACTED DATA:
    {json.dumps(extracted_data, indent=2)}

    Perform the following checks and return a JSON object:

    {{ 
      "verification_status": "pass" or "needs_correction",
      
      "accuracy_checks": [ 
      {{
        "field: "which field you checked",
        "status": "correct" or "incorrect" or "missing",
        "issue": "description of the problem (if any)",
        "correction": "what it should be (if incorrect)" 
      
      }}
      ],
          
      "missed_items": [ 
        {{ 
        "type": "action_item" or "decision" or "open_question",
        "content": "the item that was missed",
        "evidence": "quote from transcript that proves it"
        }}
      ],

      "hallucination_flags": [ 
        {{
          "field: "which extracted item is hallucinated",
          "reason": "why this wasn't actually in the transcript"
        }}
      ],

      "corrected_data": {{ 
        // The full corrected version of the extracted data
        // Include ALL fields, even unchanged ones
        // Apply all corrections and add missed items 
      }}
    }}

    CHECK RULES:
    1. Every action item must have direct evidence in the transcript. 
       If you can't find the evidence, flag it as a hallucination.
    2. Every owner name must appear in the transcript. 
    3. Every decision must be explicitly stated or clearly agreed upon. 
    4. Check if any commitment or assignment were missed by the extraction. 
    5. Verify the summary doesn't overstate or misrepresent what was discussed. 

    Respond with ONLY the JSON object."""

    response = client.messages.create( 
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0,
        messages=[{
            "role": "user", 
            "content": verification_prompt
        }]
    )

    raw_text = response.content[0].text

    # Reuse our robust JSON parser from extractor.py 
    from src.extractor import parse_llm_json
    verification_result = parse_llm_json(raw_text)

    return verification_result

def apply_corrections(original: dict, verification:dict) -> dict:
    """ 
    Merge the verification corrections into the original extraction.

    CONCEPT: If the verifier found issues, use its corrected_data.
    If it passed, use the original. This gives us a clean, verified
    final output.
    """
    if verification.get("verification_status") == "pass": 
        return original
    
    corrected = verification.get("corrected_data", original)

    # Log what changed
    changes = []
    for check in verification.get("accuracy_checks", []):
        if check.get("status") != "correct":
            changes.append(f" - {check['field']}: {check.get('issue', 
            'unknown issue')}")
        
        for missed in verification.get("missed_items", []):
            changes.append(f" - MISSED: {missed['type']} - {missed['content']}")

        for hallucination in verification.get("hallucination_flags", []):
            changes.append(f" - HALLUCINATIONL: {hallucination['field']} - {hallucination['reason']}")

        if changes:
            print("Verification found issues:")
            for change in changes:
                print(change)
    return corrected

# === TEST IT ===   # In the terminal, run: python -m src.verifier. This is due to src.extracor being imported. If we just run python src/verifier.py, it won't work because of the import statement. By running it as a module, we ensure the imports work correctly.
if __name__ == "__main__":
    # Load the transcript and extraction from the previous phases
    with open("outputs/transcript_2.json", "r") as f:
        transcript_data = json.load(f)
    with open("outputs/extraction_2.json", "r") as f:
        extraction_data = json.load(f)
    
    print("Verifying extraction...")
    verification = verify_extraction(transcript_data["text"], extraction_data)

    print(f"\nVerification status: {verification.get('verification_status')}")
    print(f"Accuracy checks: {len(verification.get("accuracy_checks", []))}")
    print(f"Missed items: {len(verification.get("missed_items", []))}")
    print(f"Hallucinations: {len(verification.get("hallucination_flags", []))}")

    # Apply corrections 
    final_data = apply_corrections(extraction_data, verification)

    with open("outputs/verified_extraction_2.json", "w") as f:
        json.dump(final_data, f, indent=2)
    
    print("\nFinal verified data saved to outputs/verified_extraction_2.json")
