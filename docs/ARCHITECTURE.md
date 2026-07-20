# Architecture - Meeting-to-Action Intelligence System

> The shape of the system and the reasoning behind it. When I come back and think
> "why did I build it this way instead of the obvious way?", the answer is here. The
> README says what the pipeline is; this says why.

## The pipeline

```
Audio -> Whisper transcription -> Claude extraction -> Verification chain -> Slack / Notion delivery
```

Each stage is a seperate module with a clean handoff, rather than one
large prompt that does everything at once.

### Why seperate stages instead of one big prompt

- **Different stages fail differently and need different fixes**. Transcription errors are audio
 problems; extraction errors are reasioning/ schema problems; verification errors are judgement
 problems. Keeping them seperate means I can fix one without
 destabilizing the others.
- **The verifier only works if it's independent of the extractor**. That independence is
 impossible if they're the same prompt.
- **Testability**. I can evaluate the extractor in isolation against aknown transcript,
 which is exactly what the prompt-eval phase depends on.

---

## Key decisions

### 1. Verifier uses a structually different method from the extractor

The verifier is not just "the extractor, but stricter". It reads the
transcript with a deliberately different method - a five-phase scan
(enumerate commitment markers -> identify recap -> list decisions ->
list open questions -> compare against extractor output).

**Why:** In v1, the verifier shared blind spots with the extractor.
Both missed the *same* items because they scanned the transcript the same
way. A checker that thinks like the thing it's checking can't catch that
thing's mistakes. The only way the verifier adds value is by having a different pattern of attention.

**Consequence / warning to future-me:** If I'm ever tempted to simplify
the verifier by reusing the extractor's approach "to keep them
consistent" - that consistency *is the bug*. Their divergence is the
feature.

### 2. Extraction prioritizes fidelity over tidiness

The extraction prompt (v2) is built to preserve the transcript exactly - keep
spoken deadline wording ("1030", not normalized to "10:30 AM"),
distinguish commitments from suggestions, attacg a `source_quote`.

**Why:** Most early extraction errors came from the model improving on
the source - adding structure or information that wasn't spoken. For an
extraction task, that's a bug, not a feature. The design principle is:
**extract what was said, don't clean it up.** Normalization, if wanted,
belongs in a later stage, not extraction.

### 3. Sub-task granularity is explicit

The extractor pulls each sub-task of a multi-step commitment seperately
rather than collapsing them into one action item.

**Why:** Best approach for task tracking and management. Without specifically
demanding sub-task granularity, multi-step commitments are bunched together
in one action item rather than each task being treated as independent. 

---

## Component map
 
| Module | Role | Notes |
| --- | --- | --- |
| `src/transcriber.py` | Audio → text | Whisper API |
| `src/extractor.py` | Text → structured JSON | Started with claude-sonnet-4-20250514 (Retired). Replaced with claude-sonnet-4-6. v2 is current best. |
| `src/verifier.py` | Quality checks | Started with claude-sonnet-4-20250514 (Retired). Replaced with claude-sonnet-4-6. v2 is current best. |
| `src/integrations/slack_bot.py` | Slack delivery | Message containing meeting information sent to Slack channel through Slacks API. |
| `src/integrations/notion_client.py` | Task push | Action items logged in a Notion database through Notions REST API. |
| `src/api.py` | FastAPI endpoints | Pydantic input validation lives here. |
| `prompts/` | Versioned prompts + `iteration_log.md` | The prompt-iteration history lives here. |
| `samples/` | Sample audio for testing | Sample #1: Warehouse issues, two meeting attendees, 9:00 minutes long, information easily identifiable given language. Sample #2: Client dashboard review, two meeting attendees, 5:26 minutes long, echoes natural human discourse, 1 attendee with an accent. Sample #3: Vendor proposal review, two meeting attendees, 6:14 minutes long, echos natural human discourse, disruptions in meeting. |
| `outputs/` | Saved results | Holds output from transcriber, extractor, and verification steps in pipeline respectively. |

---

## Output schema

```json
{
    "meeting_summary": "...",
    "key_topics": [ 
        {
            "topic": "...",
            "summary": "...", 
            "time_range": "..." 
        }
    ], 
    "decisions": [
        { 
            "decision": "...",
            "context": "...",
            "made_by": "..."
        }
    ], 
    "action_items": [ 
        { 
            "task": "...",
            "owner": "...",
            "deadline": "...", 
            "priority": "...",
            "context": "..."
        }
    ],
    "open_questions": [
        { 
            "questions": "...",
            "raised_by": "...",
            "context": "..."
        }
    ], 
    "attendies_mentioned": ["..."],
    "follow_up_meeting_needed": true/false, 
    "follow_up_reason": "..."
}
```

--- 

## Tech stack

- **Transcription:** OpenAI Whisper API
- **Extraction:** Anthropic Claude API (claude-sonnet-4-6)
- **Verification:** Anthropic Claude API (claude-sonnet-4-6)
- 