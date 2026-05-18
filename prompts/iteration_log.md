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
  - Topics discussed: 4
  - Decisions made: 3
  - Action items: 9
  - Open questions: 1
- **Errors**
  - Missed:
    - Decisions:
      - Have scanning teams share devices until replacements and repairs come.
      - To use the next seven days to measure impact of changes.
    - Action Items:
      - To pull two team members after lunch for targeted cycle count.
  - Accuracy:
    - Action Items:
      - "Notify dispatch about potential staging delays" should be assigned to Participant 1.
      - "Brief floor team..." should have a deadline of 10:30, not 10:30 AM.
  - Hallucinations:
    - N/A
- **Notes**
  - The v1 output merged multiple action items into a single action item.
  - Some repitions in action items.
  - In sample, both speakers attributed "Notify dispatch about potential staging delays" to themselves. In recap of assigments, leader assigns assignment to themselves. Proritize recap and identify leader tonage.
  - Model does not capture acceptances or fallback plans as decisions. Reason for miss of "teams will have to share devices...Fine."
  - Prompt does not say anything about preserving exact wording. Reason for "1030" -> "10:30 AM".

---

#### Extraction v2

- **Results**
- **Errors**
- **Notes**

---

#### Extraction v3

- **Results**
- **Errors**
- **Notes**

---

#### Verification v1 on Extraction v1

- **Results**
  - Accuracy checks:
  - Missed items:
  - Hallucinations:
- **Corrections**
- **Errors**
- **Notes**

---

#### Verification v2 on Extraction v2

- **Results**
- **Corrections**
- **Errors**
- **Notes**

---

#### Verification v3 on Extraction v3

- **Results**
- **Corrections**
- **Errors**
- **Notes**

---

### Sample 2

#### Extraction v1

- **Results**
  - Topics discussed: 3
  - Decisions made: 3
  - Action items: 4
  - Open questions: 0
- **Errors**
  - Missed:
    - Decisions:
      - Reframe usuage renewal slide to better explain March dip.
      - Update summary slide to say engagment was up, rentention was flat, and support sticked.
    - Action Items:
      - N/A
  - Accuracy:
    - N/A
  - Halluciniations:
    - N/A
- **Notes**
  - The v1 output merged "tighten wording on the trend slide" and "rewrite the summary bullets" into a single action item.
  - The v1 prompt's definition of "decision" is limited to big directional choices, and these feel more like editorial agreements. The model read them as just conversation about what to fix rather than decisions that were made. The prompt has no guidance for recognizing that mutual agreement on a specific change counts as a decision even when it's small.

---

#### Extraction v2

- **Results**
  - Topics discussed:
  - Decisions made:
  - Action items:
  - Open questions:
- **Errors**
- **Notes**

---

#### Extraction v3

- **Results**
  - Topics discussed:
  - Decisions made:
  - Action items:
  - Open questions:
- **Errors**
- **Notes**

---

#### Verification v1 on Extraction v1

- **Results**
  - Accuracy checks:
  - Missed items:
  - Hallucinations:
- **Corrections**
- **Errors**
- **Notes**

---

#### Verification v2 on Extraction v2

- **Results**
  - Accuracy checks:
  - Missed items:
  - Hallucinations:
- **Corrections**
- **Errors**
- **Notes**

---

#### Verification v3 on Extraction v3

- **Results**
  - Accuracy checks:
  - Missed items:
  - Hallucinations:
- **Corrections**
- **Errors**
- **Notes**

---

### Sample 3

#### Extraction v1

- **Results**
  - Topics discussed: 3
  - Decisions made: 2
  - Action items: 4
  - Open questions: 0
- **Errors**
  - Missed:
    - Decisions:
      - Have internal summary say implemenatation rollout needs coordination from IT and Ops during first two weeks.
      - It was decided that the budget number was good.
    - Action Items:
      - N/A
  - Accuracy:
    - N/A
  - Halluciniations:
    - N/A
- **Notes**
  - "Have internal summary say implementation rollout needs coordination from IT and Ops during first two weeks" — The model categorized this as an action item (update internal summary language) rather than also recognizing it as a decision. The transcript shows a proposal ("I think we should just say it needs coordination from IT and OPS during the first two weeks") followed by explicit agreement ("Agreed"). That's a decision about what the document should say, not just a task to edit it. The v1 prompt has no guidance that an agreed-upon content change counts as a decision, and its example only shows high-level strategic decisions, so the model filed this under "summary revision" and moved on.
  - "Budget number is good" — This is a confirmation decision, not a directional one. One speaker asks "Are you still good with the budget number?" and the other confirms it's under the cap they discussed. The v1 prompt's example and framing orient the model toward decisions that change something ("go with Vendor B"), not decisions that affirm the status quo. 

---

#### Extraction v2

- **Results**
- **Errors**
- **Notes**

---

#### Extraction v3

- **Results**
- **Errors**
- **Notes**

---

#### Verification v1 on Extraction v1

- **Results**
  - Accuracy checks:
  - Missed items:
  - Hallucinations:
- **Corrections**
- **Errors**
- **Notes**

---

#### Verification v2 on Extraction v2

- **Results**
  - Accuracy checks:
  - Missed items:
  - Hallucinations:
- **Corrections**
- **Errors**
- **Notes**

---

#### Verification v3 on Extraction v3

- **Results**
  - Accuracy checks:
  - Missed items:
  - Hallucinations:
- **Corrections**
- **Errors**
- **Notes**

---

## Whisper-1 Notes

- Good with removing background noise and not altering transcript extraction.
- Good with individuals with accents. From a 5-minute recording, approximately 5–10 seconds of audio-to-text will be misaligned. **Important:** These can be the most critical 5–10 seconds misinterpreted. *(Findings from Sample 2)*
- Does not include laughing or non-word language/sounds. *(Findings from Sample 3)*
