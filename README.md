# Meeting-to-Action Intelligence System

> **Status: In Progress** · Deploying to cloud, expanding test coverage
> Last updated: [June 29, 2026]

An AI system that transcribes meetings, extracts structured action items 
with assigned owners and deadlines, and delivers them to Slack/Notion — 
turning talk into tracked work.

## The Problem

Teams discuss, decide, and then forget because nobody captures
the commitments in a structured, trackable format.

## The Solution

Audio Recording → Whisper Transcription → LLM Extraction →
Verification Chain → Slack/Notion Delivery

## Architecture

```
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
│   ├── digest.py           # Addition: Weekly summary
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
```

## Current Progress

| Phase | Status | Notes |
|-------|--------|-------|
| Whisper transcription pipeline | ✅ Complete | Tested on 3 meeting types |
| Structured extraction prompt | ✅ Complete | v2 tested across 3 samples |
| Verification chain | ✅ Complete | v2 tested across 3 samples |
| Prompt evaluation framework | ✅ Complete | Manual review against ground truth |
| Slack integration | ✅ Complete | |
| Notion integration | ✅ Complete | |
| FastAPI endpoint | ✅ Complete | |
| Docker deployment | ✅ Complete | |
| Cloud deployment | 🔄 In Progress | Evaluating Railway, Render, and Fly.io |
| End-to-end demo recording | Not started | |

## Prompt Engineering Results

### Extraction Prompt

Tested across 3 transcript types: warehouse operations 1-on-1, client dashboard review, and vendor proposal discussion.
 
| Version | Sample | Action Items | Decisions | Key Errors |
|---------|--------|-------------|-----------|------------|
| v1 | 1 (warehouse ops) | 9 found, 3 missed | 3 found, 2 missed | Wrong owner, fabricated deadline, added "AM" |
| v1 | 2 (dashboard review) | 4 found, 0 missed | 3 found, 2 missed | Merged sub-tasks, missed editorial decisions |
| v1 | 3 (vendor proposal) | 4 found, 0 missed | 2 found, 2 missed | Missed confirmation and content-agreement decisions |
| v2 | 1 (warehouse ops) | 15 found | 9 found | 1 cross-field attribution inconsistency |
| v2 | 2 (dashboard review) | 6 found | 7 found | 0 |
| v2 | 3 (vendor proposal) | 5 found | 6 found | Open questions over-extracted (2 of 3 borderline) |
 
**What drove the improvement (v1 → v2):**
 
1. **Speaker identification system** — v1 had no guidance for unlabeled transcripts, causing owner misattribution. v2 adds a four-step diarization procedure (detect turn boundaries, assign sequential labels, upgrade on name resolution, note roles) that the model executes before extracting any content.
2. **Sub-task granularity rule** — v1 consolidated multi-step commitments into single items, missing 3 action items in Sample 1 alone. v2 requires atomic extraction with a worked example decomposing one commitment into four tasks, plus a taxonomy of commonly missed sub-types (resourcing, scoping, deliverable, process-implementation).
3. **Broader decision taxonomy** — v1 only captured proactive choices. v2 defines eight decision types: active choices, constraint acceptances, process changes, postponements, exclusions, confirmations/affirmations, editorial/content agreements, and timebound commitments. This recovered all 6 missed decisions across the 3 samples.
4. **Recap rule** — When a meeting ends with an explicit action-item recap, the recap is authoritative for owner, scope, and deadline. This resolved the owner-attribution dispute in Sample 1 where both speakers committed to dispatch-related tasks.
5. **Deadline preservation** — v1 normalized "1030" to "10:30 AM." v2 requires verbatim wording and distinguishes between deadlines tied to actions and background timing facts.
6. **Source-quote traceability** — Each action item now includes the transcript phrase that establishes the commitment, giving the verifier a concrete anchor and surfacing ASR errors for human review.

### Verification Prompt

| Version | Sample | Accuracy Checks | Missed Items Caught | False Corrections |
|---------|--------|-----------------|--------------------|--------------------|
| v1 | 1 (warehouse ops) | 2 | 2 of 5 | 1 (removed valid item as "already underway") |
| v1 | 2 (dashboard review) | 1 | 0 of 2 | 1 (downgraded "draft and send" to "handle") |
| v1 | 3 (vendor proposal) | 4 | 0 of 2 | 0 |
| v2 | 1 (warehouse ops) | 11 | 3 | 0 |
| v2 | 2 (dashboard review) | 13 | 1 | 0 |
| v2 | 3 (vendor proposal) | 14 | 3 | 0 |

**What drove the improvement (v1 → v2):**

1. **Six-phase methodology** — v1 used open-ended checks that shared the extractor's blind spots. v2 forces a structurally different scan: verify participants → enumerate commitment markers → check recap → list decisions → list open questions → compare. The different methodology catches what the extractor's attention pattern misses.
2. **Narrowed hallucination criterion** — v1 removed a valid action item because the work "seemed already underway." v2 defines hallucination strictly as absence of commitment language and explicitly prohibits removing items based on redundancy, overlap, or perceived progress. Zero false removals across all v2 tests.
3. **Phase-output traceability** — v2 externalizes intermediate reasoning (`phase_1_commitments_found`, `phase_2_recap_items`, `phase_3_decisions_found`) into inspectable fields, making the verifier's scan debuggable before looking at the final comparison.
**Key learning:** v1 verification shared blind spots with the extractor — both missed the same items because they used the same scanning approach. v2 forces a structurally different method so the verifier catches what the extractor's pattern of attention is likely to miss.

**Known remaining gaps:** The verifier shares a recall bias with the extractor on open questions, validating borderline items and adding more (Sample 3). Speaker attribution in unlabeled transcripts remains the hardest error class — upstream speaker diarization in the audio pipeline would eliminate it.

→ Full iteration log with all changes documented: [`prompts/iteration_log.md`](prompts/iteration_log.md)


## Sample Output

**Input:** 12-minute standup transcript (anonymized)

**Output:**
```json
{
  "meeting_summary": "Participant 1 and Carlos conducted an operational review of warehouse issues including congestion, inventory mismatches, scanner outages, and temp worker errors...",
  "decisions": [
    {
      "decision": "Re-slot overflow inventory out of zones B and C immediately",
      "context": "Overflow near picking lines causing forklift-picker traffic conflicts",
      "made_by": "Participant 1"
    }
  ],
  "action_items": [
    {
      "task": "Move overflow inventory out of zones B and C",
      "owner": "Carlos",
      "deadline": "today",
      "priority": "high",
      "context": "Immediate fix to reduce warehouse congestion",
      "source_quote": "First, you'll move overflow inventory out of zones B and C today."
    }
  ],
  "participants": [
    {
      "label": "Participant 1",
      "role_if_known": "Manager / decision-maker",
      "first_utterance": "Thank you for joining me, Carlos."
    },
    {
      "label": "Carlos",
      "role_if_known": "Warehouse operations lead",
      "first_utterance": "The biggest issue is congestion in the warehouse..."
    }
  ]
}
```

## Whisper-1 Observations

- Handles background noise and accented speech well.
- Approximately 5–10 seconds of misaligned audio-to-text per 5-minute recording. These can land on critical moments (action items, names, deadlines).
- Does not transcribe laughter or non-verbal sounds.
- The `source_quote` field in extraction v2 surfaces exactly where ASR errors occurred, giving reviewers a precise location to check.

## What's Next

- [ ] Expand test samples beyond 1-on-1s for broader evaluation
- [ ] Fix minor v2 errors: cross-field attribution inconsistency (Sample 1), open_questions over-extraction (Sample 3), made_by proposer-vs-approver ambiguity (Sample 2)
- [ ] Test for consistent output across samples.
- [ ] Cost optimization: token-reduced prompt versions (v2-lite), cross-version combination testing (e.g., extraction v2 + verification v1-lite), model-tier comparison (Sonnet vs. Haiku for verification)
- [ ] Model lifecycle management: automated detection and fallback when the active API model is deprecated or retired (e.g., claude-sonnet-4-20250514 → claude-sonnet-4-6), to avoid pipeline downtime without manual intervention
- [ ] Cloud deployment (Railway, Render, or Fly.io)
- [ ] End-to-end demo recording (Loom)

## Tech Stack

- **Transcription:** OpenAI Whisper API
- **Extraction:** Anthropic Claude API (claude-sonnet-4-6)
- **Verification:** Anthropic Claude API (claude-sonnet-4-6 for semantic verification) + Pydantic (schema validation for FastAPI)
- **Orchestration:** Python 3.13
- **Delivery:** Slack SDK, Notion API
- **API:** FastAPI + Uvicorn
- **Deployment:** Docker
