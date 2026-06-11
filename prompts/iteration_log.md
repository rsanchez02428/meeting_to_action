# ITERATION LOG

---

## Prompt Version Registry

### Extraction Prompts

#### v1 — Initial

No changes. Baseline prompt.

#### v2



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
  - Accuracy checks: 2
  - Missed items: 2
  - Hallucinations: 0
- **Corrections**
  - Missed:
    - Decisions:
      - Included "Conduct cycle count on affected SKUs to clean up discrepancies".
    - Action Items:
      - Included "Prioritize eight SKUs with the highest movement for cycle count".
  - Accuracy:
    - Action Items:
      - Caught the time inaccuracy for action item "Brief floor team and start moving overflow stock deadline". Deadline was listed as '10:30 AM' but transcript says 'by 1030'.
      - Captured missing details about action item "Run targeted cycle count". Was missing specific detail about 'two team members after lunch' and 'eight SKUs with highest movement'
- **Errors**
  - Missed:
    - Decisions:
      - Have scanning teams share devices until replacements and repairs come.
      - To use the next seven days to measure impact of changes.
  - Accucary:
    - Action Items:
      - "Notify dispatch about potential staging delays" should be assigned to Participant 1.
- **Notes**
  - The verifier has the same blind spots as the extractor. It reads the same unlabeled transcript with the same definition of "decision" and the same lack of guidance on speaker disambiguation. So when the extractor misattributes Carlos, the verifier reads the transcript the same way and confirms the misattribution. Verification only adds value when the verifier has a different methodology, not just a second pass.
  - The verifier has no systematic completeness method. It's asked to find missed items, but not told how. A more reliable approach: instruct the verifier to first enumerate every commitment marker in the transcript ("I'll", "I will", "we'll", "I want X by", "send me", "you'll"), then check each one against the extraction. This converts an open-ended judgment task into a checklist, which is much harder to fail at.
  - The verifier overcorrects. It removed the "Push IT to expedite scanner repairs" action in a previous test because it judged the work to be "already underway." The prompt's hallucination criterion is loose ("can't find the evidence"), and the model interpreted ambient progress as evidence of completion. Tighten this: "A statement of intent ('I'll push IT…') is an action item even if related work is described elsewhere as in progress. Only flag as hallucinated if no commitment language exists in the transcript."
  - No tie-breaking rule for the recap. When the transcript and the recap disagree on owner or scope, the verifier has no guidance. Adding a rule like "In meetings with an explicit action-item recap, the recap is authoritative for owner and scope" would have caught the Carlos/leader confusion automatically.
  - The verifier cannot seperate an accuracy check from a missing item when several action items are bundled together. For "Run targted cycle count", missed action items such as 'to pull two team members after lunch' and 'to prioritize the eight SKUs with the highest movement' were placed in the same action item along with "Run targeted cycle count" and were labeled an accuracy check. Should be corrected when sub-task extraction.

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
  - Accuracy checks: 1
  - Missed items: 0
  - Hallucinations: 0
- **Corrections**
  - N/A
- **Errors**
  - Missed:
    - Decisions:
      - Reframe usuage renewal slide to better explain March dip.
      - Update summary slide to say engagment was up, rentention was flat, and support sticked.
  - Acurracy:
    - Action Items:
      - Falsely corrected action item "Draft and send cover email to client" to "Handle cover email to client".
- **Notes**
  - The verifier missed the same two decisions the extractor missed (reframing the usage renewal slide, updating summary slide wording) because it has no structured method for finding decisions independently. It re-reads the transcript with the same general attention as the extractor, so shared blind spots carry through.
  - Both missed decisions are editorial agreements embedded in casual conversation — Alex proposes a change, the other speaker says "Agreed" or confirms. The verification prompt doesn't tell the model to scan for agreement markers ("Agreed," "Exactly," "Yeah, that feels right") as signals that a decision was made.
  - The verifier falsely corrected "Draft and send cover email to client" to "Handle cover email to client" because the transcript contains the word "handle" ("easier if I just handle it"). The model treated surface-level word matching as an accuracy correction, even though the original phrasing was more specific and actionable.
  - The verification prompt doesn't distinguish between preserving the meaning of an action versus matching exact transcript wording. This caused the verifier to downgrade a useful description into a vague one and call it a fix.
  - Without an enumeration phase (scanning every "I'll," "you'll," agreement marker, and recap statement), the verifier is just a second pass with the same methodology. Same method, same blind spots, same misses.

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
  - Accuracy checks: 4
  - Missed items: 0
  - Hallucinations: 0
- **Corrections**
  - Missed:
    - Decisions: N/A
    - Action Items: N/A
  - Accuracy:
    - Decisions: N/A
    - Action Items:
      - For "Update internal summary language to be more realistic about implementation risk", the owner was corrected to "Second Speaker".
      - For "Send email to Redwood to clarify support response times", the owner was corrected to "Second Speaker".
      - For "Forward updated version to finance once summary is revised", the owner was corrected to "First Speaker"
      - For "Send revised summary when completed", the owner was corrected to "Second Speaker".
- **Errors**
  - Missed:
    - Decisions:
      - Have internal summary say implemenatation rollout needs coordination from IT and Ops during first two weeks.
      - It was decided that the budget number was good.
    - Action Items:
      - N/A
  - Accuracy:
    - Decisions:
      - N/A
    - Action Items:
      - N/A
- **Notes**
  - The missed decision about the internal summary saying "implementation rollout needs coordination from IT and Ops during first two weeks" was already captured as an action item topic. The verifier saw the concept represented in the output and moved on without checking whether it also qualified as a decision. The prompt has no rule about items that belong in both categories. 
  - The missed decision about the budget number being acceptable ("This is still under the cap we discussed, so I think it's fine" / "Okay, good") is a confirmation, not a directional choice. The verification prompt's check rule says decisions must be "explicitly stated or clearly agreed upon" — which this one is — but the verifier applied the same narrow mental model of "decision" as the extractor. Without examples of what confirmations and acceptances look like as decisions, the rule alone doesn't change behavior.

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
