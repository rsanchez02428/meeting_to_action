# ITERATION LOG

## extraction v1 (initial)(tested on transcript.json)

- RESULTS:
  - Captured 4/4 key topics
  - Captured 3/4 decisions. Missed decision to have teams share scanners until replacement and repairs occur.
  - Captured 9/12 action items. Missed action items to prioritize eight SKUs with highest movement for cycle count, to pull two team memebers after lunch for targeted cycle count and putting a mandatory stage and verification check in place before dispatch confirmation.
  - Captured 1/1 open questions.
- ERRORS:
  - Within the action items, for "notify dispatch about potential staging delays", the correct owner is Meeting Leader not Carlos.
  - Within the action items, for "Push IT to expedite remaining scanner repairs", the deadline says "Tomorrow afternoon" but should say "Not specified". Task was said to be completed soon.
  - Within action items, the breif floor team deadline was listed as 10:30 AM but the transcript says 10:30. No AM.

## verification v1 (initial)(tested on extraction.json)

- RESULTS:
  - Did not capture missed decision to have scanners shared by teams.
  - Missed "putting a manadatory stage and verification check in place before dispatch confirmation" action. Owner: Carlos, deadline: today, priority: high.
- ERRORS:
  - "Notify dispatch about potential staging delays". Owner is marked as Carlos but should be Meeting Leader.
  - "Push IT to expedite remaining scanner repairs". Was correct in extraction but was removed due to belief the task was already underway.

## extraction v2 (added: speaker attribution, recap rule, action item garnularity, decisions, deadline preservation, commitment vs. suggestion, source_quote field, attendees_mentioned updated)(tested on transcript.json)

- CHANGES:
  - Speaker Attribution - Added guidance for handling transcripts without speaker labels, including how to track turn boundaries and use role labels for unnamed speakers. Defaults to "Unassigned" when uncertain instead of guessing.
  - Recap Rule - Added instruction to treat end-of-meeting recaps as authoritative for owner, scope, and deadline when they conflict with earlier statements.
  - Action Item Granularity - Added rule to extract sub-tasks as separate items rather than consolidating them. Included a worked example showing one multi-step commitment producing multiple action items.
  - Broader Decision Definition — Expanded what counts as a decision to include acceptances of constraints, process changes, postponements, and exclusions — not just proactive choices. Decisions that produce actions now appear in both lists.
  - Deadline Preservation — Added rule to keep deadline wording exactly as spoken (no normalizing "1030" to "10:30 AM"). Clarified that deadlines must be tied to the action itself, not background facts about timing.
  - Commitment vs. Suggestion — Added rule that statements of intent count as action items even if related work appears to be underway elsewhere.
  - New source_quote field — Each action item now includes the exact phrase that established the commitment, giving the verifier something concrete to check against.
  - Attendees Updated — Now includes role labels for unnamed speakers so the meeting leader appears even when never named by name.
- RESULTS:
  - Captured 4/4 key topics
  - Captured 5/5 decisions. Sub-task disected into seperate items. All were captured. Including previously missed decision to have team share scanners.
  - Captured 13/13 action items. Captured previously missed action items to prioritize eight SKUs with highest movement for cycle count, to pull two team memebers after lunch for targeted cycle count and putting a mandatory stage and verification check in place before dispatch confirmation. Extra action item (previously identified 12) is from sub-task extraction.
  - Captured 1/1 open questions.

## verification v1 (tested on extraction_v2.json)

- RESULTS:
  - Accuracy checks = 3: Transcription errors - 'retain' to 'retrain', quote contains transcript error 'Pull to team members' should be 'Pull two team members'.
  - Missed items = 1: decision - Schedule follow-up meeting for Friday at 2 p.m. to review impact data.

## verification v2 (added: replaced python-flavored placeholders, five-phase methodology, owner attribution checks, deadline checks, narrow hallucination criterion, granularity check, phase_1_commitments_found, phase_2_recap_items, phase_3_decisions_found fields, item_index and evidence fields in accuracy checks, phase_detectin_in field in missed items.)

- CHANGES:
  - Replaced Python Placeholders — Swapped {json.dumps(extracted_data, indent=2)} for clean {TRANSCRIPT} and {EXTRACTED_JSON} placeholders so the model isn't guessing at what's prompt versus data.
  - Five-Phase Methodology — Added a structured walkthrough the verifier must follow: enumerate commitment markers, identify the recap, list decisions, list open questions, then compare. Converts an open-ended judgment task into a checklist and forces the verifier to use a different method than the extractor so blind spots don't propagate.
  - Owner Attribution Checks — Added the same speaker-attribution rules used in the extractor, including the guardrail against defaulting to the named person when the unnamed speaker actually committed.
  - Deadline Checks — Added two specific checks: verbatim preservation and the rule that deadlines must be tied to the action itself rather than pulled from background timing facts.
  - Narrow Hallucination Criterion — Tightened the definition so items aren't removed just because work seems underway, redundant, or only loosely paraphrased. Added the principle that removing valid items is as harmful as adding invented ones.
  - Granularity Check — Added instruction to verify each step of a multi-step commitment is captured separately, with examples of commonly missed sub-types (resourcing, scoping, deliverable, process-implementation).
  - New Phase-Output Fields — Added phase_1_commitments_found, phase_2_recap_items, and phase_3_decisions_found so the verifier externalizes its scan. Gives you a debuggable artifact to inspect before looking at the final comparison.
  - New Traceability Fields — Added item_index and evidence to accuracy checks, and phase_detected_in to missed items, so each finding can be traced back to a specific extracted item, transcript quote, and methodology phase.