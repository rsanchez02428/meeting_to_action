# ITERATION LOG

---

## Prompt Version Registry

### Extraction Prompts

#### v1 — Initial

No changes. Baseline prompt.

- Role prompting: Assigns persona of an expert executive assistant specialized in structured extraction from meeting transcripts.

- Task framing: Direct instruction to analyze a transcript and extract structured information.

- Input handling: Raw meeting transcript inserted via {transcript} placeholder (variable substitution).

- Output constraint: Strictly JSON only — no markdown, no explanation, no code fences

- Output schema: Predefined JSON structure with seven fields:
  - meeting_summary — 2–3 sentence executive summary of discussion and outcomes
  - key_topics — Topic name, 1–2 sentence summary, approximate time range
  - decisions — What was decided, context, who made or announced it
  - action_items — Task description, owner, deadline, priority (high/medium/low), context
  - open_questions — Unresolved questions, who raised them, why they matter
  - attendees_mentioned — List of names mentioned in the transcript
  - follow_up_meeting_needed — Boolean with reason if applicable

- Guardrails: Eight explicit rules constraining extraction behavior:
  - Grounding rule: only extract explicitly stated or strongly implied information
  - Anti-hallucination rule: do not invent, assume, or hallucinate
  - Classification rules: "I'll do X" → action item; "Can someone look into X?" → unassigned action item; "We should do X" → open question
  - Formatting rule: preserve deadline wording as-is, no date calculation
  - Priority heuristic: "high" for urgent/ASAP/critical/blocker, "medium" as default, "low" for nice-to-haves

- Few-shot example: One input-output pair (vendor selection scenario) demonstrating the full expected extraction format

#### v2

- **Role prompting reinforced** — Expanded the system persona to include ownership attribution accuracy and granularity, priming the model's behavior across all three failure modes observed in v1 (missed items, wrong owners, over-consolidation).

- **Recall-over-precision reframing** — Shifted the task instruction from "thorough but precise" to "exhaustive," explicitly biasing the model toward higher recall on action items at the acceptable cost of slight over-extraction.

- **Multi-step chain-of-thought for speaker diarization** — Added a four-step reasoning procedure the model must execute before extraction: detect turn boundaries, assign sequential participant labels, upgrade labels on named-entity resolution, and note inferred roles. Forces intermediate reasoning about speaker identity rather than relying on implicit inference.

- **Named-entity resolution rule** — When a name surfaces in the transcript as an address term (e.g., "Thanks, Carlos"), the model must propagate that name retroactively and forward across all label references — a consistency constraint on entity linking.

- **Structured output schema change (`participants`)** — Replaced the flat `attendees_mentioned` string array with a structured object array containing label, inferred role, and first utterance, giving the downstream verifier a speaker map to validate against.

- **Cross-field consistency constraint** — All attribution fields (`owner`, `made_by`, `raised_by`) now reference the same labeling system (name, Participant N, or Unassigned), eliminating label drift across output fields.

- **Hierarchical context grounding (Recap Rule)** — Introduced a precedence rule: when an explicit recap section exists in the transcript, its content is authoritative for owner, scope, and deadline. This gives the model a grounding hierarchy instead of treating all transcript segments equally.

- **Task decomposition instruction** — Added an explicit atomicity rule for action items with a worked few-shot example showing one spoken commitment decomposed into four independently checkable tasks. Establishes granularity expectations the single v1 example did not.

- **Classification boundary expansion (Decisions)** — Widened the decision taxonomy from implicit (only proactive choices demonstrated in the example) to explicit with five sub-types: active choices, constraint acceptances, process changes, postponements, and exclusions. Reduces under-classification caused by narrow few-shot anchoring.

- **Token-level fidelity constraint (Deadlines)** — Added a verbatim preservation rule for deadlines, preventing the model from normalizing or adding specificity (e.g., appending "AM"). Also introduced a grounding distinction: only timing language explicitly tied to an action verb counts as a deadline, not background temporal facts.

- **Commitment-language pattern matching expanded** — Added three new trigger patterns ("Alex, you'll do X," "We need to do X" + acceptance, intent despite in-progress work) to the classification rules that distinguish action items from open questions, broadening the model's extraction coverage.

- **Semantic similarity for priority classification** — Changed priority matching from exact keyword matching to "words or tone SIMILAR TO," allowing the model to use semantic proximity rather than string matching. Added "today," "immediately," and "starting now" as high-priority triggers.

- **Source-grounding field (`source_quote`)** — Each action item now requires the exact transcript phrase that establishes the commitment. Functions as an inline retrieval citation, giving both the verifier and human reviewer a grounding anchor per item.

- **Default value specification (`time_range`)** — Added an explicit fallback value ("N/A") to eliminate inconsistent handling of missing data across outputs.

- **Default value specification (`raised_by`)** — Changed from an implicit no-output behavior to an explicit "Unclear" default, reducing ambiguity in how the model handles unattributable open questions.

- **Few-shot example alignment** — Updated the single worked example to demonstrate the new labeling conventions (Participant 1 for unnamed speakers), the `source_quote` field, and the `participants` array, ensuring the example anchors the model on v2 behaviors rather than v1 patterns.

---

### Verification Prompts

#### v1 — Initial

No changes. Baseline prompt.

- Role prompting: Assigns persona of a meticulous quality assurance reviewer for meeting notes

- Task framing: Compare extracted data against original transcript and identify errors, omissions, or hallucinations

- Input handling: Two variable substitutions — original transcript via {TRANSCRIPT} and extracted output via {EXTRACTED_JSON}

- Output constraint: Strictly JSON only

- Output schema: Predefined JSON structure with five fields:
  - verification_status — "pass" or "needs_correction"
  - accuracy_checks — Field-level status (correct/incorrect/missing), issue description, correction
  - missed_items — Type (action_item/decision/open_question), content, supporting transcript quote
  - hallucination_flags — Which extracted item is unsupported, reason why
  - corrected_data — Full corrected version of the extraction with all fields

- Guardrails: Five check rules constraining verification behavior:
  - Evidence rule: every action item must have direct transcript evidence
  - Name grounding rule: every owner name must appear in the transcript
  - Decision grounding rule: every decision must be explicitly stated or clearly agreed upon
  - Completeness rule: check for missed commitments or assignments
  - Accuracy rule: verify summary does not overstate or misrepresent discussion

- Few-shot example: None (zero-shot)

#### v2

- **Role prompting intensified** — Strengthened the persona from "find any" to "find every… including small ones" and added an explicit anti-pattern instruction ("You will NOT simply re-read and trust your second impression"), priming the model against confirmation bias toward the extractor's output.

- **Forced chain-of-thought via six-phase methodology** — Replaced the open-ended "perform the following checks" with a mandatory six-phase sequential reasoning pipeline (verify participants → enumerate commitments → check recap → list decisions → list open questions → compare). This is a structured chain-of-thought that externalizes intermediate reasoning into inspectable output fields, preventing the verifier from sharing the extractor's attention pattern.

- **Upstream validation gate (Phase 0)** — Inserted a participant-identification verification phase before any content checks. Validates speaker ordering, named-entity resolution direction, label upgrades, role inference, speaker count, and first utterances. Catches entity-linking errors at the source before they cascade into downstream attribution mistakes.

- **Label convention alignment** — Updated all phase instructions to reference "name or Participant N label," synchronizing the verifier's entity-reference system with the extractor's, eliminating cross-prompt label mismatch.

- **Cross-field schema validation (Owner Attribution)** — Rewrote attribution checks to enforce referential integrity: every label used in any attribution field must exist in the `participants` array. Functions as a foreign-key constraint across the structured output.

- **Grounding checks for deadlines** — Added two verification rules: token-level fidelity (deadline wording must match the transcript verbatim) and grounding validity (the deadline must be tied to the action, not extracted from a background temporal fact).

- **Hallucination guardrail recalibrated** — Narrowed the hallucination definition to require absence of commitment language, not just absence of a perfect quote. Explicitly prohibited removing items based on redundancy, overlap, or perceived in-progress status. Framed false negatives (removing valid items) as equally harmful to false positives (adding invented items), correcting a precision bias in v1.

- **Granularity validation with sub-type taxonomy** — Added a decomposition check requiring the verifier to confirm each step of a multi-step commitment is captured individually. Provided a taxonomy of commonly missed sub-types (resourcing, scoping, deliverable, process-implementation) as a retrieval cue for the model's attention.

- **Intermediate reasoning artifacts (Phase-Output Fields)** — Added `phase_1_commitments_found`, `phase_2_recap_items`, and `phase_3_decisions_found` to the output schema. These are chain-of-thought scratchpad fields that externalize the verifier's scan into structured, inspectable evidence before the final comparison phase.

- **Per-item traceability fields** — Added `item_index` and `evidence` to accuracy checks and `phase_detected_in` to missed items. Creates an audit trail linking each verification finding to a specific extracted item, transcript quote, and methodology phase.

- **New `phase_0_participant_check` output block** — Structured output capturing the verifier's per-participant assessment (ordering, name upgrade, role, first utterance) with issue descriptions, making the upstream validation gate's reasoning inspectable.

- **New `label_consistency_check` output block** — A dedicated referential-integrity report confirming all labels across attribution fields resolve to entries in the `participants` array, with specific inconsistencies surfaced.

- **New `item_content` field on hallucination flags** — Each flag now includes the content of the suspected item, making flags self-contained without requiring cross-reference to the extraction output.

- **Correction propagation rule** — Updated the `corrected_data` instruction to require that participant-identification fixes propagate to every attribution field throughout the output, enforcing consistency in the corrected structured output.

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
  - Topics discussed: 10
  - Decisions made: 9
  - Action items: 15
  - Open questions: 1
- **Errors**
  - "Notify dispatch that staging time may run slightly longer today" is listed as an action item with owner Carlos, but the same statement appears in decisions with made_by Participant 1, and v1's own ground-truth correction assigned this to Participant 1. The source_quote ("I'll notify dispatch that staging time may run slightly longer today.") is a first-person commitment made by the leader during the recap, so the owner should be Participant 1. The cross-field consistency constraint didn't catch it because owner and made_by were generated in separate fields without being reconciled against each other. Worth flagging despite the otherwise clean result.
- **Notes**
  - `(NEED - accidently put notes from Sample 2 Extraction v2 here.)`

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
  - Accuracy checks: 11
  - Missed items: 3
  - Hallucinations: 0
  - Verification found issues:
    - action_items[3].task: The task description says 'during peak hours' but the recap in the transcript says 'during pick hours'. More importantly, the source_quote for this item is 'Second, you'll create a pick only lane during pick hours.' — the transcript's recap uses 'pick hours' not 'peak hours'. While 'peak hours' is used earlier in the conversation and is the intended meaning, the task description and source_quote are inconsistent with each other. The task description is the more accurate representation of intent, but the source_quote accurately reflects the recap wording.
    - action_items[5].source_quote: The source_quote reads 'Third, you'll retain the temp workers before they go back to independent tasks.' The transcript word is 'retain' (likely a transcription error for 'retrain'), and the task description correctly says 'refresher training'. The source_quote is faithful to the transcript. However, the task description says 'Conduct refresher training for temp workers on scan confirmation and pallet labeling before they return to independent picking' — this is accurate in meaning. No extraction error; the source_quote faithfully reproduces the transcript.
    - decisions[2].decision: The decision 'Temp workers must complete refresher training on scanning and labeling before returning to independent picking tasks' is attributed to 'made_by: Participant 1'. This is correct. However, the decision description omits the specific condition stated in the transcript: 'remove the temp workers from independent picking UNTIL they complete refresher training'. The extraction captures this correctly in the decision text. No issue.
    - decisions — missing decision about prioritizing eight SKUs: The decision to prioritize the eight highest-movement SKUs for the cycle count is captured in action_items but is missing from the decisions array. Carlos proposed it and Participant 1 agreed ('Good'), making it a confirmed decision.
    - action_items[7].task: The task says 'Pull two team members after lunch' but the transcript says 'Pull to team members after lunch' — 'to' is likely a transcription error for 'two'. The extraction correctly interprets this as 'two team members', which is the accurate meaning. This is correct.
    - action_items[10].owner: The task 'Notify dispatch that staging time may run slightly longer today' is assigned to Carlos. This is correct — Carlos explicitly said 'I'll notify dispatch that staging time may run slightly longer today.' However, action_items[11] assigns 'Coordinate with dispatch to make carriers aware of possible short staging delays' to Participant 1. These are two separate but related actions: Carlos notifies dispatch about staging delays, and Participant 1 coordinates with dispatch to notify carriers. Both are correctly attributed.
    - action_items[13].owner: The task 'Monitor shipping accuracy and picking speed data over the next seven days' is assigned to 'Unassigned'. In the transcript, Participant 1 proposes this and Carlos agrees ('Exactly'), and then Participant 1 says 'Let's use the next seven days to measure the impact of this changes.' This is a joint commitment with no specific individual assigned. 'Unassigned' is a reasonable label, but it could also be attributed to both participants. This is acceptable.
    - action_items[14].owner: The task 'Review performance numbers and decide whether to pursue a larger warehouse layout redesign' is assigned to Participant 1 with deadline 'Friday at 2 p.m.' This is a joint meeting/review, not solely Participant 1's task. The transcript says 'we'll meet again Friday at 2 p.m.' — both participants are expected to attend and review. Assigning solely to Participant 1 is a minor inaccuracy.
    - key_topics[3].summary: The summary says 'a driver arriving to find a missing pallet and a misplaced pallet'. The transcript says 'one pallet was missing and other was in the wrong and another one was in the wrong loading bay.' This suggests two pallets were in the wrong loading bay (or one missing and one in wrong bay). The extraction's summary is consistent with the transcript's meaning. However, the transcript also mentions 'The truck left with a partial load' — this detail is captured. No significant error.
    - open_questions[0].raised_by: The open question is attributed as raised_by 'Participant 1'. In the transcript, Participant 1 raises it first ('Are there are this warehouse issues temporary...') but Carlos also contributes to framing it ('I think that's the bigger question'). Attributing solely to Participant 1 is acceptable but slightly incomplete. Not a significant error.
    - MISSED: decision - Prioritize the eight highest-movement SKUs for the cycle count to get the clearest picture fastest
    - MISSED: decision - If shipping accuracy and picking speed improve over the next week, the problem was mostly execution; if not, a more serious layout redesign may be needed — agreed as the evaluation framework
    - MISSED: action_item - Carlos to get started with the floor team immediately after the meeting (general implementation start, distinct from the specific briefing task)
- **Corrections**
  - Caught 3 missed items that v1 verification missed entirely:
    - Decision: Prioritize the eight highest-movement SKUs for cycle count (dual-category: already in action_items but missing from decisions)
    - Decision: Evaluation framework: if shipping accuracy and picking speed improve, the problem was execution; if not, a layout redesign may be needed
    -Action item: Carlos to get started with the floor team immediately after the meeting (general implementation start, distinct from the specific briefing task)
  - Correctly identified action_items[14] as a minor inaccuracy. The Friday review meeting is joint ("we'll meet again") but was attributed solely to Participant 1
  - Correctly handled transcription artifacts without treating them as extraction errors: "retain" -> "retrain" (source_quote faithful to transcript, task description faithful to meaning), "to" -> "two" (extraction correctly interpreted as "two team members")
  - Correctly noted the "pick hours" vs "peak hours" inconsistency between action_items[3] task description and its source_quote
- **Errors**
  - Did not flag the cross-field inconsistency between decisions[8] (made_by: Participant 1 for "Notify dispatch that staging time may run slightly longer today during stabilization") and action_items[10] (owner: Carlos for the same dispatch notification task). Regardless of which attribution is correct (Participant 1 is the owner), the same task cannot be attributed to two different people across the two arrays without being flagged.
- **Notes**
  - The six-phase methodology is producing materially better results than v1. v1 verification caught 2 items; v2 caught 3, and the types of catches are more sophisticated. A dual-category miss (SKU prioritization as both decision and action item) and an evaluation-framework decision that v1's open-ended methodology would not have surfaced.
  - Zero false removals. The recalibrated hallucination criterion prevented the overcorrection pattern seen in v1 verification, where "Push IT to expedite scanner repairs" was incorrectly removed because the work seemed underway. All 15 extraction action items were preserved.
  - The granularity check had less surface area to work with because extraction v2 already decomposed most sub-tasks. The one missed action (Carlos getting started immediately) is an extremely fine-grained "general start" that is arguably a duplicate of the briefing task rather than a distinct independently checkable item.
  - The "notify dispatch" attribution is the hardest remaining error class. Without speaker labels in the transcript, both interpretations are defensible. This is a speaker-diarization ambiguity that prompting alone may not fully resolve.

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
  - Topics discussed: 7
  - Decisions made: 7
  - Action items: 6
  - Open questions: 1
- **Errors**
  - Missattributed decision [1] to Participant 1 rather than to Alex(made_by: Participant 1 for "Rewrite the summary slide first bullet to say engagement was up, retention..." ). Error most likely due to aligning decisions with the individual agreeing rather than to the individual proposing.
- **Notes**
  - Both v1-missed editorial decisions are recovered: "Add a note under the usage/renewal chart to explain the March dip" and "Rewrite the summary slide first bullet… replacing the vague word 'mixed.'" The expanded taxonomy now treats mutual agreement on a small change as a decision instead of background chatter.
  - The v1 merge is fixed: "tighten wording" and "rewrite bullets" are now two distinct action items.
  - Attribution is clean throughout. Alex owns the editing/handoff tasks, Participant 1 owns the final read, the send, and the email. No owner corrections appear needed, unlike v1.
  - source_quote is doing useful double duty as a Whisper-error surface. "I think we should just say engagement was up, retention was flat, and support sticked in crescent" preserves the garbled ASR ("support sticked in crescent") verbatim while the decision text correctly resolves it to "support tickets increased." Same with Alex's first_utterance "Pretty good, as you retired." This ties directly to the Whisper-1 notes. The field now pinpoints exactly where the 5–10s of ASR misalignment landed, which gives the verifier and a human reviewer a precise place to look.
  - Same decision/action overlap pattern as Sample 1: the noon handoff is both a decision ("Alex will send the revised deck back…") and an action item ("Send the revised deck back to Participant 1," owner Alex).

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
  - Accuracy checks: 13
  - Missed items: 1
  - Hallucinations: 0
  - Verification found issues:
    - decisions[0].made_by: The decision to add a note under the chart was proposed by Alex ('I want to take note under the chart to explain what happened more directly'), not Participant 1. The extractor attributed it to 'Alex' which is correct. Wait — re-reading: the extractor says made_by: 'Alex'. That is correct. No error here.
    - decisions[1].made_by: The decision to rewrite the summary bullet was proposed by Alex ('I think we should just say engagement was up, retention was flat, and support sticked in crescent') and agreed to by Participant 1 ('Agreed'). The extractor attributes this to 'Participant 1', but it was Alex who proposed the specific language. The decision should be attributed to Alex, or jointly, but the proposal originated with Alex.
    - decisions[3].made_by: The decision to leave out the benchmark comparison was proposed by Participant 1 ('I think so... adding another chart now feels like the kind of chart we regret immediately') and agreed to by Alex ('Yeah, I'm with you'). The extractor attributes this to 'Participant 1', which is correct.
    - decisions[4].made_by: The decision about how to handle the support ticket increase in the deck was a joint discussion. Participant 1 said 'I'd be careful on the deck' and Alex said 'Same, that's what's been bothering me.' Then Participant 1 articulated the approach ('acknowledge it, don't over-commit on the cause') and Alex agreed ('Yeah, that feels right'). The extractor attributes this to 'Participant 1', which is the most defensible attribution. This is acceptable.
    - decisions[6].made_by: The decision that Alex will send the revised deck back around noon was directed by Participant 1 ('send it back to me around noon') and accepted by Alex ('Works for me'). The extractor attributes this decision to 'Participant 1', which is correct as Participant 1 set the deadline and Alex accepted it.
    - action_items[1].source_quote: The source quote provided is 'I think we should just say engagement was up, retention was flat, and support sticked in crescent' — this is the garbled transcript text. The extracted summary says 'support tickets increased' but the transcript says 'support sticked in crescent' (garbled audio). The extraction correctly interprets the meaning, but the source_quote should reflect the actual transcript text, which it does. However, the extracted task description says 'support tickets increased' while the transcript says 'support sticked in crescent'. The interpretation is reasonable given context, but reviewers should note the transcript is garbled here.
    - key_topics[2].summary: The summary states 'support tickets increased' as the agreed replacement language. The transcript says 'support sticked in crescent' which is garbled, but the prior context about 'support ticket increase' supports this interpretation. However, the extraction presents this as a clean, confirmed phrase when the transcript is actually garbled at this point. This is a minor interpretation issue, not a fabrication.
    - open_questions[0].raised_by: The open question about the support ticket cause was raised by Participant 1 ('do we want to stay in the deck that is probably tied to onboarding changes or leave that for the discussion on Tuesday?'). The extractor attributes it to 'Participant 1', which is correct.
    - decisions[1].made_by: Attributed to 'Participant 1' but the specific language replacement was proposed by Alex. Participant 1 agreed. Should be 'Alex'.
    - MISSED: decision - The summary slide needs one more pass — agreed that it needs revision (this is the framing decision that precedes the bullet rewrite decision, confirming the summary slide as a whole needs work, not just the first bullet)
- **Corrections**
  - Correctly identified decisions[1].made_by as an attribution error — Alex proposed the specific replacement language ("engagement was up, retention was flat, support tickets increased"), and Participant 1 agreed with "Agreed." The made_by should be Alex, not Participant 1. Phase 1 commitment enumeration traced the "I think we should just say..." marker to Alex, catching what v1's open-ended methodology missed.
  - Caught 1 missed decision: the summary slide needing one more pass. A general revision agreement that precedes the specific bullet rewrite, treated as a separate framing decision.
  - Correctly handled garbled ASR throughout without false corrections. Recognized that source_quotes faithfully reproduce transcript wording ("support sticked in crescent") while task descriptions correctly resolve intended meaning ("support tickets increased"). No action items falsely corrected due to ASR artifacts.
- **Errors**
  - The missed decision ("summary slide needs one more pass") is borderline. It's the general acknowledgment that directly sets up decisions[1] (the specific bullet rewrite). Whether this is a distinct decision or just the conversational lead-in to the rewrite agreement is debatable. Logging it is reasonable, but it may represent over-counting rather than a genuine omission.
- **Notes**
  - Zero false corrections. A direct improvement over v1 verification, which downgraded "Draft and send cover email" to "Handle cover email" through surface word matching. The structured methodology prevented this behavior even without the explicit accuracy correction rule from the revised prompt.
  - The depth of analysis increased substantially: v1 verification produced 1 accuracy check, 0 missed items, and 1 false correction. v2 produced 13 accuracy checks, 1 missed item, and 0 false corrections. The six-phase methodology is generating far more thorough coverage.
  - Phase 1 commitment marker enumeration is the mechanism that caught the decisions[1].made_by error. By listing every "I think we should..." and "I'll..." marker with speaker attribution before comparing against the extraction, the verifier independently traced the proposal to Alex rather than trusting the extractor's attribution.
  - The ASR handling pattern is consistent with Sample 1: source_quotes surface exactly where transcript garbling occurs ("support sticked in crescent," "Pretty good, as you retired"), giving both the verifier and a human reviewer precise locations to check. The verifier correctly distinguished between faithful transcript reproduction and meaning-level accuracy without conflating the two.
  - The one genuinely new catch (decisions[1].made_by) is a "who proposed vs. who approved" distinction. The extraction prompt doesn't specify whether made_by should track the proposer or the approver. This ambiguity hasn't caused problems elsewhere but surfaced here because Alex proposed and Participant 1 approved. Worth considering whether made_by should be clarified in a future extraction prompt iteration.

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
  - Topics discussed: 5
  - Decisions made: 6
  - Action items: 5
  - Open questions: 3
- **Errors**
  - open_questions jumped 0 to 3. Only "What exactly does Redwood mean by 'priority response'?" is clearly a posed, unresolved question — it's the basis for the email action item. The other two, "Will finance have a significant negative reaction to the budget number?" and "Will Redwood come back with anything unexpected or problematic…?",  read as anticipated risks/uncertainties rather than questions actually raised. Acceptable for now but somthing worth flagging.
- **Notes**
  - "Update the internal summary…" carries deadline "next week, next hour," faithfully copied from a the source_quote ("I can get the summary updated next week, next hour"). Correct behavior under verbatim preservation, but the deadline is internally inconsistent and should be resolved. This is something best left for clarification betweem meeting attendies to not miss align in correct future deadlines.
  - Both v1-missed decisions are recovered: "Revise the internal summary to explicitly state… IT and OPS coordination…" and "Budget number is acceptable and within the previously discussed cap" (a confirmation/acceptance decision the expanded taxonomy now catches).
  - The IT/OPS coordination item correctly appears as both a decision and an action item ("Update the internal summary…"). This is the precise dual-category case the v1 verifier flagged as having no rule. v2 now represents it in both fields rather than picking one.
  - Owner attribution is correct without verifier intervention: summary update and Redwood email to Participant 2; forward to finance to Participant 1.
  - Net pattern across v2: the recall bias clearly fixed v1's under-extraction of decisions and action items, but Sample 3 shows it can overshoot specifically on open_questions. Consider a v3 tightening rule scoped to open_questions only.

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
  - Accuracy checks: 14
  - Missed items: 3
  - Hallucinations: 0
  - Verification found issues:
    - decisions[0].made_by: Decision to move forward with Redwood was jointly reached, not made solely by Participant 1
    - decisions[1].made_by: The proposal to revise the summary language came from Participant 2, not Participant 1
    - decisions[2].made_by: The request to send Redwood a support clarification email was raised by Participant 2, not Participant 1
    - decisions[3].made_by: Decision not to involve OPS yet was proposed by Participant 1 but agreed jointly; attributing solely to Participant 1 is a minor inaccuracy
    - decisions[5].made_by: Adding OPS at kickoff was agreed jointly, not decided by Participant 2 alone
    - action_items[0].deadline: The deadline 'next week, next hour' is a verbatim transcription of a speech disfluency. The extraction correctly preserves it verbatim per methodology, but the source_quote is truncated — it omits 'and send the email right after', which is part of the same utterance and relevant to the sequencing of action items.
    - action_items[1].priority: The support clarification email is listed as 'medium' priority, but it is a prerequisite for moving forward with the vendor and is sequenced immediately after the summary update. It should be 'high' priority, consistent with the urgency expressed in the transcript.
    - open_questions[1].raised_by: The question about finance's reaction was raised by Participant 1 ('Are you still good with the budget number, or is finance going to have a dramatic reaction to this?'), not Participant 1 asking about their own reaction. The raised_by is correctly Participant 1, but the context says 'Finance approval is a prerequisite for moving forward' — this is accurate. No error in raised_by, but the context slightly overstates certainty; finance was described as unlikely to block it.
    - open_questions[2].raised_by: The question about whether Redwood will come back with something unexpected was raised in the context of Participant 1's statement ('Then unless they come back with something weird on support, I don't see a reason not to move ahead'), making it Participant 1 who raised this concern, not Participant 1 — wait, the extraction says Participant 1, which is correct.
    - action_items[0].source_quote: Source quote is truncated. The full utterance includes the sequencing of the email send: 'I can get the summary updated next week, next hour, and send the email right after'
    - participants[0].role_if_known: Describing Participant 1 as 'Decision-maker / likely manager or senior stakeholder' overstates the evidence. Both participants appear to be peers. Participant 1 forwards to finance but this does not establish seniority.
    - MISSED: decision - Agreed not to delay further — both participants confirmed another week would not change the decision and further delay only creates more meetings
    - MISSED: decision - Redwood selected over three other evaluated vendors based on clarity and cost
    - MISSED: open_question - Whether the next-quarter go-live target is achievable given current timing
- **Corrections**
  - Corrected made_by attribution across 5 decisions — shifting single-speaker attributions to "Both / Joint" where the transcript shows mutual agreement, and correctly identifying Participant 2 as the proposer for the summary revision and support email decisions.
  - Correctly identified action_items[1].priority as too low — the support clarification email is a prerequisite for moving forward with Redwood, warranting high priority rather than medium.
- **Errors**
  - Did not flag the open_questions over-extraction. The user's extraction v2 notes identified open_questions[1] ("Will finance have a significant negative reaction?") and open_questions[2] ("Will Redwood come back with anything unexpected?") as "anticipated risks/uncertainties rather than questions actually raised." The verifier validated all three without flagging the borderline items and then added a 4th similar item (go-live target), compounding the over-extraction pattern rather than catching it.
- **Notes**
  - The 3 missed items include 2 decisions not in the original extraction. "Redwood selected over three vendors" is an evaluation-outcome decision; "Agreed not to delay further" is a confirmation decision. Both fall within v2's expanded taxonomy, suggesting Phase 3 is catching types the extractor under-indexes on. 
  - The open_questions over-extraction is the one area where v2 verification makes things worse rather than better. The hallucination criterion ("when in doubt, KEEP the item") works well for action items and decisions where a false negative has operational cost, but creates over-counting for open questions where the standard should arguably be tighter.
  - The "next week, next hour" deadline was correctly handled throughout — both the extractor and verifier preserved it verbatim as a speech disfluency rather than normalizing or flagging it as an error. This is consistent with the deadline preservation rule working as designed.
  - This is the sample where the peer dynamic is most evident. Both speakers propose, both agree, both take tasks. The verifier correctly identified this by challenging the "manager/senior stakeholder" role description, unlike Samples 1 and 2 where one speaker clearly directs the other.
  
## Whisper-1 Notes

- Good with removing background noise and not altering transcript extraction.
- Good with individuals with accents. From a 5-minute recording, approximately 5–10 seconds of audio-to-text will be misaligned. **Important:** These can be the most critical 5–10 seconds misinterpreted. *(Findings from Sample 2)*
- Does not include laughing or non-word language/sounds. *(Findings from Sample 3)*
