# Spike Test Script: Safe Use of Oral Rehydration Salts (ORS)

| | |
|---|---|
| **Version** | v1 — **DRAFT, not yet approved** (revised after independent review, 2026-10-05) |
| **Implements** | `docs/SPIKE_PLAN.md` §2 (test material); Q17 proposed default (health topic) |
| **Language** | English source (to be localized into Tamil) |
| **Target length** | 90–120 s spoken |
| **Speaker** | Speaker A (requires signed `HL-SPIKE-CONSENT` v1, permission 3.0) |

## Content warning: health facts must be verified before recording

This is **test material** for measuring translation, speech and verification quality. It is not medical advice. Its health facts were drafted from general knowledge of WHO/UNICEF ORS guidance. **No one has checked them against the source yet**, so every claim in the fact table (§4) is **[UNVERIFIED]** until two team members have checked it, and a health professional too if one is reachable. If the clip is ever shown outside the team, it carries the on-screen note: *"Demonstration content. Follow the advice of your local health worker."*

---

## 1. Script (27 segments, 5 scenes)

Segment boundaries are the intended split points. Pause for **about half a second** between segments so the boundaries can be hand-marked. Read numbers exactly as written (for example, "50 to 100 millilitres").

### Scene 1: Why ORS matters
| Seg | Text |
|---|---|
| S01 | Diarrhoea makes a child lose water and salts quickly. |
| S02 | This is called dehydration, and it can be dangerous. |
| S03 | Oral rehydration salts, or ORS, replace what is lost. |

### Scene 2: Preparing ORS
| Seg | Text |
|---|---|
| S04 | Wash your hands with soap and water. |
| S05 | Take 1 litre of clean water. If unsure, boil and cool it. |
| S06 | Pour 1 sachet of ORS into the water. |
| S07 | Stir until the powder dissolves. |
| S08 | Do not add sugar or salt. |
| S09 | Do not use less water than the packet says. |
| S10 | Do not boil the solution after mixing. |
| S11 | Throw away any left after 24 hours. |

### Scene 3: How much to give
| Seg | Text |
|---|---|
| S12 | As a rule of thumb, give it slowly, in small sips. |
| S13 | Under 2 years, give 50 to 100 millilitres after each loose stool. |
| S14 | From 2 to 10 years, give 100 to 200 millilitres after each loose stool. |
| S15 | Older children and adults: as much as they want. |
| S16 | If the child vomits, wait 10 minutes, then give it more slowly. |
| S17 | Under 2 years, give a teaspoonful every 1 to 2 minutes. |
| S18 | Do not stop breastfeeding or feeding. |
| S19 | Do not give soft drinks or juice instead of ORS. |

### Scene 4: Zinc
| Seg | Text |
|---|---|
| S20 | Ask a health worker about zinc. |
| S21 | Zinc is given once a day for 10 to 14 days. |
| S22 | The dose is 20 milligrams a day, or 10 milligrams for babies under 6 months. |
| S23 | Finish the course, even after the diarrhoea stops. |

### Scene 5: Danger signs
| Seg | Text |
|---|---|
| S24 | See a health worker straight away for danger signs: |
| S25 | blood in the stool, repeated vomiting, or fever, |
| S26 | or if the child cannot drink or is very sleepy. |
| S27 | Do not wait for it to pass. Better safe than sorry. |

**Length [ESTIMATE]:** 251 words (counted with `wc -w`). Spoken numbers ("one hundred", "twenty-four") and "O-R-S" make the speech longer than the word count suggests. **Do a timed read-through before freezing v1.** If it runs over 120 s, drop S04 (it has no critical tokens), then shorten S15. Don't drop S03 (it defines ORS) or S27 (it carries an idiom and a negation).

### 1b. Calibration sentences (M2 practice, not rated, not recorded)

R1 and R2 use these for the 5 practice segments in `SPIKE_PLAN.md` M2, so the 27 rated segments stay untouched. They are text only.

| Cal | Text |
|---|---|
| C1 | Wash your hands before cooking and after using the toilet. |
| C2 | Do not leave cooked food uncovered. |
| C3 | Store drinking water in a clean container with a lid. |
| C4 | If you are not sure, ask a health worker. |
| C5 | Keep medicines out of reach of children under 5 years. |

---

## 2. Coverage against the spike-plan requirements

| Requirement (`SPIKE_PLAN.md` §2) | Needed | In this script |
|---|---|---|
| Numbers | ≥ 10 | 1 (S05), 1 (S06), 24 (S11), 2, 50, 100 (S13), 2, 10, 100, 200 (S14), 10 (S16), 2, 1, 2 (S17), 10, 14 (S21), 20, 10, 6 (S22): **19 number tokens**, including 5 ranges |
| Units | ≥ 5 | litre, hours, years, millilitres, minutes, teaspoonful, days, milligrams, months: **9** |
| Glossary terms | ≥ 5 | diarrhoea, dehydration, oral rehydration salts / ORS, sachet, loose stool, zinc, health worker, breastfeeding, danger sign: **9** |
| Negated instructions | ≥ 5 | S08, S09, S10, S18, S19, S27: **6** |
| Idioms | ≥ 2 | "as a rule of thumb" (S12, on a non-dosing line), "better safe than sorry" (S27); "straight away" (S24) is a weaker third |

### 2b. Critical tokens (the M1 denominator) and normalisation, fixed in advance

- **Critical tokens:** the 19 number tokens above, the 9 units, the 9 glossary terms, and the frequency phrase **"once a day"** (S21).
- **Number words count as numbers.** "once" in "once a day" is a critical token; ADR 0008's digit rule does not apply to it, and a translation may render it in words.
- **Equivalent forms, all counted as correct:** `50` = `fifty`; `litre` = `liter` = `L`; `millilitres` = `milliliters` = `ml`; `milligrams` = `mg`; `ORS` = `O.R.S.` = `oral rehydration salts`; `diarrhoea` = `diarrhea`.

### 2c. Rating rules fixed in advance

- **S24–S26 are rated as one unit.** Tamil puts the verb at the end, so "see a health worker" may correctly move to S26. Segment boundaries count only against **omission** or **grammar** errors, never against word order across the three segments.
- All other segments are rated individually.

**Why these matter (risk notes for the raters):**
- **Ranges** (S13, S14, S17, S21) test whether both ends survive translation and speech.
- **Negations** (S08–S10, S18, S19, S27) are the reversal-risk segments. Dropping the "not" inverts a safety instruction, which is exactly what ADR 0008's AI flags must catch.
- **S22 has two doses and an age condition in one sentence.** It is the hardest segment for keeping each number attached to the right condition.
- **S13 and S17 both start "Under 2 years".** A translation must not merge or swap them.
- **"Loose stool", "sachet" and "teaspoonful"** have no single obvious everyday Tamil equivalent. They test glossary use against literal translation.

## 3. Reference and held-out clips (for IndicF5 and the similarity check)

Each consenting speaker records all three clips. The exact transcript is required, so read word for word.

| Clip | Text | Target length |
|---|---|---|
| English reference (cloning input) | "Good morning. I am reading this short passage slowly and clearly, so that the recording is clean, steady and easy to understand." | 8–11 s |
| Tamil reference (cloning input) | **To be written by R1**: native Tamil, general content, unrelated to the ORS script, about 18–22 words. The R1-written text is the transcript. | 8–11 s |
| Held-out clip (**never** used for cloning) | "The weather today is pleasant, and the market near our college is busy with people buying fresh vegetables and fruit." | 8–11 s |

- **Reference length:** F5-TTS-based models may clip long references. **IndicF5's recommended reference length is [UNVERIFIED]**, so check the model card before recording. If a clip gets clipped, it no longer matches its transcript.
- **The held-out clip is the "real voice" sample for the ECAPA similarity check (M4),** so similarity isn't inflated by comparing the clone with its own reference.
- **Speaker B must match Speaker A** in gender and rough age, and record in the same room with the same microphone. Otherwise the "B's clone" control becomes a trivial bar.
- Record on the consent form whether each speaker is a **native Tamil reader**. A non-native reading of the Tamil reference confounds the English-vs-Tamil-reference comparison.

## 4. Fact table: verify before recording

**Sources to check against:** WHO, *The treatment of diarrhoea: a manual for physicians and other senior health workers* (4th revision, 2005), especially Treatment Plan A; and the WHO/UNICEF joint statement on low-osmolarity ORS and zinc (2004). Check the current versions, and any Indian national (MoHFW) guidance the team prefers. Record the **page or section** and **who checked**: two members, independently.

| Seg | Claim | Status | Source page | Checked by |
|---|---|---|---|---|
| S05–S06 | 1 standard sachet in 1 litre of clean water | [UNVERIFIED]. Smaller packs (e.g. 200 ml) may exist; confirm which pack the script describes. S09 covers this with "what the packet says". | | |
| S08 | Do not add sugar or salt | [UNVERIFIED] | | |
| S10 | Do not boil after mixing | [UNVERIFIED] | | |
| S11 | Discard after 24 hours | [UNVERIFIED] | | |
| S13 | Under 2 years: 50–100 ml after each loose stool | [UNVERIFIED] | | |
| S14 | 2 to 10 years: 100–200 ml after each loose stool | [UNVERIFIED] | | |
| S15 | Older children and adults: as much as wanted | [UNVERIFIED] | | |
| S16 | Vomiting: wait 10 minutes, then continue more slowly | [UNVERIFIED] | | |
| S17 | Under 2 years: a teaspoonful every 1–2 minutes | [UNVERIFIED]. *Changed after review: the earlier draft said "a spoonful every 2–3 minutes", which the reviewer believes is wrong.* | | |
| S18 | Continue breastfeeding and feeding | [UNVERIFIED] | | |
| S19 | Soft drinks or juice are not substitutes | [UNVERIFIED] | | |
| S21–S22 | Zinc for 10–14 days; 20 mg/day, 10 mg/day under 6 months | [UNVERIFIED] | | |
| S23 | Complete the zinc course after the diarrhoea stops | [UNVERIFIED] | | |
| S24–S26 | Danger signs: blood in stool, repeated vomiting, fever, cannot drink, very sleepy | [UNVERIFIED]. The list is deliberately short, not complete. *Changed from "high fever" to "fever" pending the check.* | | |

If a claim is wrong, fix the script **before** R1 writes the reference translation. Editing afterwards invalidates the reference.

## 5. Recording instructions

1. **Prerequisite:** the speaker has signed `HL-SPIKE-CONSENT` v1, with at least permission 3.0.
2. **Record on the team laptop if you can.** If you use a phone: switch on **airplane mode** and turn **off cloud backup** (Google Photos, iCloud, recorder-app sync) **before** recording.
3. Use a quiet room, with no fan, music or echo. Hold the microphone about 20–30 cm from the mouth. Use the same room and microphone for every speaker.
4. Record **WAV**, or the phone's highest-quality setting. The spike converts to 16 kHz mono itself, so don't convert by hand.
5. Read the 27 segments in order, with about a half-second pause between segments. **If you stumble, re-record the whole take.** If a stumble is kept, the reference transcript must include it word for word.
6. File names: `speakerA_testclip_v1.wav`; `speakerX_ref_en.wav`, `speakerX_ref_ta.wav` and `speakerX_heldout_en.wav` for X = A and B.
7. **Transfer by cable or USB directly to the laptop,** then **delete the phone copy** and log the deletion. Do not send the files through WhatsApp, email or cloud drives. If that becomes unavoidable, write it in the external-upload log (`SPIKE_PLAN.md` §2, data handling).
8. Store the files in the spike media folder **outside the git repository and outside any cloud-synced folder.** Never commit them.
9. Note the measured clip duration in the spike log.

## 6. Cloned-voice inputs (fixed; the consent form refers to this section)

The cloned voice (IndicF5) **only ever synthesises human-written, rater-checked Tamil text.** Machine translations are never spoken in a speaker's cloned voice.

| Used in | Input text |
|---|---|
| M4 (TTS quality, similarity), M6 (speed), M9 (revocation test) | **R1's reference translation, checked by R2,** of these 10 segments: **S05, S08, S11, S13, S14, S16, S17, S21, S22, S27** (chosen for their numbers, units and negations) |
| M4 critical-content pronunciation | The same 10 segments in two versions: numbers as **digits** and numbers as **Tamil words** (both written by R1) |

Stock voices (MMS-TTS, Indic Parler-TTS) may also synthesise machine output, because they use no one's identity.

## 7. Who does what next

| Step | Who |
|---|---|
| Verify §4 against the WHO source (two members, independently); fix the script if needed | Team |
| Timed read-through; trim per §1 if over 120 s | Speaker A |
| Approve this script (freeze v1) | You |
| Write the Tamil reference-clip text, and the digit and word versions in §6 | R1 |
| Sign consent, then record the test clip, reference clips and held-out clips | Speakers A and B |
| Write the reference transcript (verbatim) and hand-mark segment boundaries | Team |
| Write the reference translation, **before seeing any system output** | R1, checked by R2 |
| Build the glossary (accepted Tamil inflected forms) and the unit lexicon | R1, R2 |
| Write the seeded-error set, **after the check rules are frozen** | R2 only |
