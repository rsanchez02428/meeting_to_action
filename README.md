# Meeting-to-Action Intelligence System

> **Status: In Progress** · Prompt testing & evaluation phase
> Last updated: [April 16, 2026]

An AI system that transcribes meetings, extracts structured action items 
with assigned owners and deadlines, and delivers them to Slack/Notion — 
turning talk into tracked work.

## The Problem

Teams discuss, decide, and then forget — because nobody captures
the commitments in a structured, trackable format.

## The Solution

Audio Recording → Whisper Transcription → Claude Extraction →
Verification Chain → Slack/Notion Delivery

## Architecture

meeting-to-action/
├── .env
├── .gitattributes
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── transcriber.py      # Phase 2: Audio → Text
│   ├── extractor.py        # Phase 3: Text → Structured Data
│   ├── verifier.py         # Phase 4: Quality checks
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── slack_bot.py    # Phase 5: Slack delivery
│   │   └── notion_client.py # Phase 5: Task management
│   └── api.py              # Phase 6: FastAPI endpoints
├── prompts/
│   ├── extraction_v1.txt
|   ├── extraction_v2.txt
|   ├── iteration_log.md
|   ├── verification_v1.txt
│   └── verification_v2.txt
├── tests/
│   └── test_extractor.py
├── samples/                 # Sample audio files for testing
├── outputs/                 # Where results get saved
└── Dockerfile               # Phase 7: Containerization

## Current Progress

| Phase | Status | Notes |
|-------|--------|-------|
| Whisper transcription pipeline | ✅ Complete | Tested on 3 meeting types |
| Structured extraction prompt | ✅ Complete | v2 is current best |
| Verification chain | ✅ Complete | Cross-checks owners + deadlines |
| Prompt evaluation framework | 🟡 In Progress | Comparing accuracy between extraction and verification, than against human output |
| Slack integration | ⬜ Not started | |
| Notion integration | ⬜ Not started | |
| FastAPI endpoint | ⬜ Not started | |
| Docker deployment | ⬜ Not started | |

## Prompt Engineering Results

### Extraction Prompt

| Version | Key Changes | Action Items | Decisions | Errors |
|---------|------------|-------------|-----------|--------|
| v1 | Initial | 9/12 (75%) | 3/4 (75%) | 3 (wrong owner, fabricated deadline, time format) |
| v2 | + Speaker attribution, recap rule, sub-task granularity, source_quote field, commitment vs. suggestion distinction, deadline preservation | 13/13 (100%) | 5/5 (100%) | 0 |

**Biggest improvement (v1 → v2):** Three changes drove the jump from 75% to 100%:

1. **Sub-task granularity rule** — v1 consolidated multi-step commitments into single items, missing 3 action items. v2 extracts each sub-task separately.
2. **Broader decision definition** — v1 only captured proactive choices. v2 also captures accepted constraints and process changes, catching the missed "share scanners across teams" decision.
3. **Deadline preservation** — v1 normalized "1030" to "10:30 AM" (adding information not in the transcript). v2 keeps exact wording as spoken.

### Verification Prompt

| Version | Key Changes | Missed Items Caught | False Removals |
|---------|------------|-------------------|----------------|
| v1 | Initial verification pass | 1/4 missed items found | 1 (removed valid item because "task already underway") |
| v2 | + Five-phase methodology, narrow hallucination criterion, owner attribution checks, granularity check, phase-output traceability fields | Testing in progress | — |

**Key learning:** v1 verification shared blind spots with the extractor —
both missed the same items because they used the same scanning approach.
v2 forces a structurally different method (enumerate commitment markers →
identify recap → list decisions → list open questions → compare) so the
verifier catches what the extractor's pattern of attention is likely to miss.

→ Full iteration log with all changes documented: [`prompts/iteration_log.md`](prompts/iteration_log.md)

## Sample Output

**Input:** 12-minute standup transcript (anonymized)

**Output:**
``````json
{
  "meeting_type": "daily_standup",
  "date": "2026-04-10",
  "duration_minutes": 12,
  "action_items": [
    {
      "task": "Update the staging environment with new API endpoints",
      "owner": "Alex",
      "deadline": "2026-04-11",
      "priority": "high",
      "context": "Blocking QA testing for sprint 14"
    },
    {
      "task": "Schedule design review for checkout flow redesign",
      "owner": "Maria",
      "deadline": "2026-04-12",
      "priority": "medium",
      "context": "Needs PM sign-off before development starts"
    }
  ],
  "decisions": [
    "Team agreed to postpone the database migration to sprint 15"
  ],
  "open_questions": [
    "Who will own the customer onboarding metrics dashboard?"
  ]
}
``````

## What I'm Working On Now

- Evaluating prompts on 3 meeting types (1-on-1s).
- Investigating whether more complex evaluation prompt is needed vs more complex
  verifier prompt.
- Testing evaluation v1 and v2 on samples #2 and #3. 
  - Findings would help identify uncaptured edge cases and 
    indicate if updated prompt versions are needed.
- Based on version results for extractor and verifier, versions of best extractor and
  verifier prompts would be created that utilize less tokens to reduce cost.
- Various versions of extractor and verifier prompts would be tested with each other
  to see which give the best results with minimized cost (based off of token usage).

## What's Next

- [ ] Slack bot integration (webhook → channel post with formatted summary)
- [ ] Notion database push (action items as Notion tasks with properties)
- [ ] FastAPI microservice wrapping the full pipeline
- [ ] Docker packaging for deployment
- [ ] End-to-end demo recording (Loom)

## Tech Stack

- **Transcription:** OpenAI Whisper API
- **Extraction:** Anthropic Claude API (claude-sonnet-4-20250514)
- **Verification:** Pydantic (schema validation) + Claude (semantic verification)
- **Orchestration:** Python 3.11
- **Planned:** FastAPI, Slack SDK, Notion API, Docker
