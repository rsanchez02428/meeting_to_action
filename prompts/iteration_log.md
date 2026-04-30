# ITERATION LOG

---

## Prompt Version Registry

### Extraction Prompts

#### v1 — Initial

No changes. Baseline prompt.

#### v2

- **Speaker Attribution** — Added guidance for handling transcripts without speaker labels, including how to track turn boundaries and use role labels for unnamed speakers. Defaults to "Unassigned" when uncertain instead of guessing.
- **Recap Rule** — Added instruction to treat end-of-meeting recaps as authoritative for owner, scope, and deadline when they conflict with earlier statements.
- **Action Item Granularity** — Added rule to extract sub-tasks as separate items rather than consolidating them. Included a worked example showing one multi-step commitment producing multiple action items.
- **Broader Decision Definition** — Expanded what counts as a decision to include acceptances of constraints, process changes, postponements, and exclusions — not just proactive choices. Decisions that produce actions now appear in both lists.
- **Deadline Preservation** — Added rule to keep deadline wording exactly as spoken (no normalizing "1030" to "10:30 AM"). Clarified that deadlines must be tied to the action itself, not background facts about timing.
- **Commitment vs. Suggestion** — Added rule that statements of intent count as action items even if related work appears to be underway elsewhere.
- **New `source_quote` field** — Each action item now includes the exact phrase that established the commitment, giving the verifier something concrete to check against.
- **Attendees Updated** — Now includes role labels for unnamed speakers so the meeting leader appears even when never named by name.

#### v3

- **Sequential Speaker Identification** — Replaced the generic "Meeting leader" / "Unnamed participant" labels with a numbered system. The first person to speak is Participant 1, the second is Participant 2, and so on. Labels are assigned in order of first appearance regardless of role.
- **Name Upgrade Rule** — When a speaker is addressed by name later in the transcript, their Participant label gets replaced with the actual name across all references — retroactively and going forward.
- **New `participants` field** — Replaced the flat `attendees_mentioned` list with a structured array that captures each speaker's label, their role if evident from context, and their first utterance. Gives a quick way to verify the speaker map.
- **All attribution fields aligned** — `owner`, `made_by`, and `raised_by` descriptions updated to reference the labeling system consistently — name, Participant N, or Unassigned.
- **Example updated** — The Vendor B example now uses "Participant 1" for the unnamed speaker and includes a `participants` array, so the model sees the convention demonstrated.

---

### Verification Prompts

#### v1 — Initial

No changes. Baseline prompt.

#### v2

- **Replaced Python Placeholders** — Swapped `{json.dumps(extracted_data, indent=2)}` for clean `{TRANSCRIPT}` and `{EXTRACTED_JSON}` placeholders so the model isn't guessing at what's prompt versus data.
- **Five-Phase Methodology** — Added a structured walkthrough the verifier must follow: enumerate commitment markers, identify the recap, list decisions, list open questions, then compare. Converts an open-ended judgment task into a checklist and forces the verifier to use a different method than the extractor so blind spots don't propagate.
- **Owner Attribution Checks** — Added the same speaker-attribution rules used in the extractor, including the guardrail against defaulting to the named person when the unnamed speaker actually committed.
- **Deadline Checks** — Added two specific checks: verbatim preservation and the rule that deadlines must be tied to the action itself rather than pulled from background timing facts.
- **Narrow Hallucination Criterion** — Tightened the definition so items aren't removed just because work seems underway, redundant, or only loosely paraphrased. Added the principle that removing valid items is as harmful as adding invented ones.
- **Granularity Check** — Added instruction to verify each step of a multi-step commitment is captured separately, with examples of commonly missed sub-types (resourcing, scoping, deliverable, process-implementation).
- **New Phase-Output Fields** — Added `phase_1_commitments_found`, `phase_2_recap_items`, and `phase_3_decisions_found` so the verifier externalizes its scan. Gives you a debuggable artifact to inspect before looking at the final comparison.
- **New Traceability Fields** — Added `item_index` and `evidence` to accuracy checks, and `phase_detected_in` to missed items, so each finding can be traced back to a specific extracted item, transcript quote, and methodology phase.

#### v3

- **New Phase 0 — Verify Participant Identification** — Inserted before all other phases. Checks speaker ordering, name upgrades, name direction (who is addressing whom), role accuracy, speaker count, and first utterances. Catches identity errors before they cascade into owner attribution.
- **Speaker references updated throughout** — Phases 1 and 2 now use "name or Participant N label" instead of the old generic "name or role label" to match the extractor's convention.
- **Owner Attribution Checks rewritten** — Rules now reference the Participant N system and include a new consistency rule: every label used in `owner`, `made_by`, or `raised_by` must appear in the `participants` array.
- **New `phase_0_participant_check` in output** — Captures the verifier's assessment of each identified participant — ordering, name upgrade, role, and first utterance — with issue descriptions for anything wrong.
- **New `label_consistency_check` in output** — A dedicated block confirming all labels used across attribution fields exist in the `participants` array, with specific inconsistencies listed if any are found.
- **`corrected_data` note updated** — If participant identification was wrong, corrections must fix the `participants` array and propagate the fix to every attribution field throughout the output.

---

## Test Results

### Sample 1

#### Extraction v1

- **Results**
  - Topics: 4/4
  - Decisions: 3/4 — Missed decision to have teams share scanners until replacement and repairs occur.
  - Actions: 9/12 — Missed action items to prioritize eight SKUs with highest movement for cycle count, to pull two team members after lunch for targeted cycle count, and to put a mandatory stage and verification check in place before dispatch confirmation.
  - Open questions: 1/1
- **Errors**
  - `action_items`: For "notify dispatch about potential staging delays", correct owner is Meeting Leader, not Carlos.
  - `action_items`: For "Push IT to expedite remaining scanner repairs", deadline says "Tomorrow afternoon" but should say "Not specified". Task was said to be completed soon.
  - `action_items`: Brief floor team deadline listed as "10:30 AM" but transcript says "1030".

---

#### Extraction v2

- **Results**
  - Topics: 4/4
  - Decisions: 5/5 — Sub-tasks dissected into separate items. All captured, including previously missed decision to have teams share scanners.
  - Actions: 13/13 — All previously missed action items captured. Extra item (vs. v1's 12) is from sub-task extraction.
  - Open questions: 1/1

---

#### Extraction v3

- **Results**
  - Topics: 4/4
  - Decisions: 5/5
  - Actions: 12/12
  - Open questions: 1/1
- **Notes**
  - Action item "pull two team members after lunch for cycle count" is included in the context of action item "Run targeted cycle count on affected SKUs". Considered correct to eliminate duplication.

---

#### Verification v1 on Extraction v1

- **Results**
  - Did not capture missed decision to have scanners shared by teams.
  - Missed action item "putting a mandatory stage and verification check in place before dispatch confirmation" (Owner: Carlos, Deadline: today, Priority: high).
- **Errors**
  - `action_items`: "Notify dispatch about potential staging delays" — owner marked as Carlos, should be Meeting Leader.
  - `action_items`: "Push IT to expedite remaining scanner repairs" — correct in extraction but removed due to belief the task was already underway.

---

#### Verification v3 on Extraction v3

- **Results** — *Pending*
- **Corrections** — *Pending*
- **Errors** — *Pending*
- **Notes** — *Pending*

---

### Sample 2

#### Extraction v1

- **Results**
  - Topics: 4/4 (shows 3 due to ungranular prompt)
  - Decisions: 3/3
  - Actions: 5/5 (shows 4 due to ungranular prompt)
  - Open questions: 0/0
- **Errors**
  - Does not include meeting leader in `attendees_mentioned`.

---

#### Extraction v2

- **Results**
  - Topics: 4/4
  - Decisions: 3/3
  - Actions: 5/5
  - Open questions: 0/0

---

#### Verification v1 on Extraction v1

- **Results**
  - Accuracy checks: 3
  - Missed items: 0
  - Hallucinations: 1
- **Errors**
  - Accuracy checks:
    - Due to the "other speaker" declining to have Alex draft the cover email, it was marked as a false action item.
    - The meeting with the client was marked as a follow-up meeting. Requires proper definition of what constitutes a follow-up meeting.
  - Hallucinations:
    - The task to draft the cover email by the "other speaker" was marked as a hallucination due to the rejection of Alex completing the task. May reflect unrecognized human intent behind the rejection.
- **Notes**
  - Hallucination and accuracy checks stem from "Meeting leader" not being mentioned in the transcript. Verifier expects unnamed speakers to be referenced as "other speaker".

---

#### Verification v2 on Extraction v2

- **Results**
  - Accuracy checks: 1
  - Missed items: 1
  - Hallucinations: 0
- **Correct**
  - Accuracy check corrections: 1
    - `key_topics`: Topic says "Usage renewal chart concerns" but transcript refers to "usage renewal" as a slide, not specifically a chart.
  - Missed item corrections: 1
    - `open_question`: Root cause of support ticket increase — whether it's tied to onboarding changes. A decision was made on how to move forward but the question itself was never answered.

---

#### Extraction v3

- *Pending*

---

#### Verification v3 on Extraction v3

- *Pending*

---

### Sample 3

#### Extraction v1

- **Results**
  - Topics: 3/3
  - Decisions: 2/2
  - Actions: 3/4
  - Open questions: 0/0
- **Errors**
  - Missed action item: send revised email to other participant when completed.
  - For action items "Update internal summary language..." and "Send email to Redwood...", owner was set to "First speaker" (meeting leader) rather than "Second speaker". Second speaker was not mentioned by name.
  - For action item "Forward updated version to finance...", owner was set to "Second speaker" when it should be "First speaker" (meeting leader).

---

#### Extraction v2

- **Results**
  - Topics: 3/3
  - Decisions: 3/3 (1 more than v1 due to v2's granularity)
  - Actions: 4/4
  - Open questions: 1/0
- **Errors**
  - The open question captured was answered within the meeting; should be null.
- **Notes**
  - Action item owners are, similar to extraction v1, swapped (e.g., action item 1's owner should be "Unnamed participant 2", not 1).
  - For action item "Forward updated version to finance...", not specific on what is being discussed (what needs to be updated?).
  - For action item "Send revised summary...", not specific to whom the revised summary is meant to be sent.
  - When extracting unnamed participants, the order of identification is not orderly.
  - The first person who speaks should be identified as "Unnamed participant 1".
  - `key_topic` "Implement coordination requirements" in extraction v2 is the same as "internal summary revision" and "Ops team involvement timing" in extraction v1. v2 simply provides a broader summary.

---

#### Verification v1 on Extraction v1

- **Results**
  - Accuracy checks: 4
  - Missed items: 0
  - Hallucinations: 0
- **Correct**
  - Accuracy check corrections: 4
    - `action_item`: Task says "First speaker" will update summary, but transcript shows second speaker will do it.
    - `action_item`: Task says "First speaker" will send email, but transcript shows second speaker will do it.
    - `action_item`: Task says "Second speaker" will forward to finance, but transcript shows first speaker will do it.
    - `action_item`: Transcript specifies "next hour" as deadline.
- **Errors**
  - Did not capture missed action item to send revised email to other participant when completed.

---

#### Verification v2 on Extraction v2

- **Results**
  - Accuracy checks: 2
  - Missed items: 0
  - Hallucinations: 0
- **Correct**
  - Accurately corrected the open question to null after extractor v2 extracted a question that was answered within the meeting.
  - Accurately corrected the owner of action item "Send email to Redwood..." from "Unnamed participant 1" to "Unnamed participant 2".
- **Errors**
  - Did not correct owners of action items "Update internal summary..." and "Send revised summary when completed" to "Unnamed participant 2".
  - Did not correct owner of action item "Forward updated version to finance..." to "Unnamed participant 1".
- **Notes**
  - Need to identify participants.

---

#### Extraction v3

- *Pending*

---

#### Verification v3 on Extraction v3

- *Pending*

---

## Whisper-1 Notes

- Good with removing background noise and not altering transcript extraction.
- Good with individuals with accents. From a 5-minute recording, approximately 5–10 seconds of audio-to-text will be misaligned. **Important:** These can be the most critical 5–10 seconds misinterpreted. *(Findings from Sample 2)*
- Does not include laughing or non-word language/sounds. *(Findings from Sample 3)*
