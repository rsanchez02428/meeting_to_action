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

**Why:** Most early extraction errors came from the model imporving on
the source - adding structure or information that wasn't spoken. For an
extraction task, that's a bug, not a feature. The design principle is:
**extract what was said, don't clean it up.** Normalization, if wanted,
belongs in a later stage, not extraction.

### 3. Sub-task granularity is explicit

The extractor pulls each sub-task of a multi-step commitment seperately
rarher than collapsing them into one action item.

**Why:** 

---

## Component map
 
| Module | Role | Notes |
| --- | --- | --- |
| `src/transcriber.py` | Audio → text | Whisper API |
| `src/extractor.py` | Text → structured JSON | Claude (claude-sonnet-4-20250514). v2 is current best. |
| `src/verifier.py` | Quality checks | **Claude-only** (semantic). No Pydantic. v2 written, eval pending. |
| `src/integrations/slack_bot.py` | Slack delivery | Not started. |
| `src/integrations/notion_client.py` | Task push | Not started. |
| `src/api.py` | FastAPI endpoints | **Pydantic input validation lives here.** Endpoint not finished — confirm scaffolding (see Decision 2). |
| `prompts/` | Versioned prompts + `iteration_log.md` | The prompt-iteration history lives here. |
| `tests/test_extractor.py` | Extractor tests | ‹fill in coverage› |
| `samples/` | Sample audio for testing | ‹fill in what #1/#2/#3 are› |
| `outputs/` | Saved results | Currently holds partial verifier-v2 eval — mixed trust. |
 