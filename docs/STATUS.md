# Status - Meeting-to-Action Intelligence System

> **Overwrite this whole file each time I step away.** This is where the
> project is *right now*. History lives in `DEVLOG.md`; this is the "note
> to self before I close the laptop." If this file and the README
> diagree, trust this file.

**Last updated:** 2026-07-30

**Current phase:** Expand test samples.

---

## **One-paragraph catch-up**

Whisper transcription, extraction, and verification are built and running end to end, and the downstream pieces (FastAPI, Slack, Notion, Docker) are built too. Extraction v2 and verification v2 output outperform v1. Errors in v2 (cross-field attribution inconsistencies, and open questions over-extraction) are not severe enough to negatively impact work. Next steps is to increase sample size of audio meeting files that contains greater diversity (more meeting attendees, greater meeting minutes, meeting dominated by regular conversation, etc.) which can reveal underlying weaknesses in my prompts or/and pipeline.

---

## **What works (trust it)**

- **Whisper transcription** - stable, tested on 3 meeting types. No severe issues.

- **Extractor v2** - done and validated. This is the current best extraction prompt.

- **Verification chain (mechanics)** - runs end-to-end.

- **Prompt evaluation framework** - in progress. Next step is to evaluate v2's on new unseen meeting audio samples. Comparing extractor vs verifier accuracy, then against human output. Would like to find cheaper method for evaluation of output.

## **What's nearly done**

- **Verifier v2** - issues found with v2 are not severe enough to cause great confussion or negatively impact business workflow. Can be made better to produce 100% accuracy against human extraction.

## **Built**

FastAPI, Slack SDK, Notion API, and Docker are all in use.

- Slack bot integration (webhook → formatted channel post) - working end to end.

- Notion database push (action items → Notion tasks) - working end to end.

- FastAPI service wrapping the pipeline.

- Docker packaging

## **What's not started**

- End-to-end demo recording (Loom)

---

## **Where the transcriber, extractor, and verifier outputs are located**

- `outputs/` contain transcriber, extractor and verifier results under their respective folders.

- Design question still unresolved: **more complex eval prompt vs. more complex verifier prompt?**

---

## **Next 3 steps**

1. Expand test samples beyond 1-on-1s for broader evaluation.

2. Fix minor v2 errors: cross-field attribution inconsistency (Sample 1; error flows from extraction to verification), and open_questions over-extraction (Sample 3; verification issue)

3. Test for consistent output across samples.
