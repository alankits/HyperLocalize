# Test datasets: short English speech videos for localization testing

Twelve real English health-information videos with people speaking, each **under 5 minutes**. Use them to test the
workflow end to end (upload → transcription → translation to Tamil → preview → review → export) through the UI.

Downloaded 2026-10-22 from Wikimedia Commons. They are **not** the spike test clip. The spike clip is the scripted, consented
ORS recording described in `docs/SPIKE_PLAN.md` §2 and `docs/spike/TEST_SCRIPT.md`.

## How to use

1. Start the app, create a project (English → Tamil), and drag a `NN_name/NN_name.webm` file into the upload.
2. Use **`SUBTITLES_ONLY`** or **`STOCK_VOICE`** mode only. **Never use `CLONED_VOICE` with these clips**: the speakers have
   not consented to HyperLocalize using their voice or likeness (ADR 0006, CLAUDE.md §5). Public domain covers the
   copyright, not consent to clone a person's voice.
3. Where a clip has `NN_name.en.srt`, it is the **human-made English subtitle track** from Commons. Use it as the reference
   transcript when you check transcription quality.
4. `NN_name.whisper-small.txt` is a **machine transcript** (faster-whisper `small`, CPU, int8, VAD on). It is a draft
   that shows the clip contains speech. **It is not ground truth.**

Video files (`*.webm`) are git-ignored (199 MB in total). The README, `manifest.json`, `.srt` and `.txt` files are tracked.

## The clips

All twelve passed HyperLocalize's own upload check (`media_tools.validate_source`, 5-minute limit) on 2026-10-22.
"Speech" is the seconds of speech that Whisper's voice-activity filter kept.

| # | Folder | Length | Size | Video | Speech style | Speech | Words (ASR) | English subtitles | Licence |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `01_handwashing_sf_health_dept_en` | 58.4 s | 5.5 MB | 1280×960 VP8 | one narrator, step-by-step instructions | 58.0 s | 155 | no | CC BY 3.0 |
| 02 | `02_nida_why_teens_attracted_to_vaping` | 122.1 s | 21.8 MB | 1920×1080 VP9 | expert interview, **accented English** | 116.1 s | 280 | **yes** | Public domain |
| 03 | `03_cdc_clean_hands_prevent_flu` | 63.1 s | 10.6 MB | 480×360 VP8 | one speaker giving hygiene instructions ("20 seconds") | 59.1 s | 184 | no | Public domain |
| 04 | `04_doctor_hpv_vaccine_safety_talking_head` | 107.8 s | 25.3 MB | 1280×720 VP8 | **single talking head** (doctor) | 91.6 s | 222 | no | Public domain |
| 05 | `05_what_to_expect_child_vaccinated` | 69.2 s | 13.2 MB | 1920×1080 VP9 | narrated animation, symptoms and numbers | 67.7 s | 192 | no | Public domain |
| 06 | `06_nida_anyone_can_become_addicted` | 120.2 s | 10.2 MB | 1920×1080 VP8 | narrator, explainer | 100.3 s | 232 | **yes** | Public domain |
| 07 | `07_cdc_traumatic_brain_injury_kids` | 135.5 s | 10.5 MB | 1920×1080 VP9 | narrator, medical terms | 118.6 s | 256 | **yes** | Public domain |
| 08 | `08_nei_myopia_eye_development` | 78.9 s | 3.4 MB | 1920×1080 **AV1** | narrator, medical terms | 76.7 s | 172 | **yes** | Public domain |
| 09 | `09_nibib_how_ultrasound_works` | 100.7 s | 8.9 MB | 1920×1080 VP9 | narrator, technical terms | 86.8 s | 207 | **yes** | Public domain |
| 10 | `10_fauci_qa_jj_vaccine_pause_dialogue` | 136.1 s | 27.4 MB | 1920×1080 VP8 | **two-person Q&A dialogue** | 123.9 s | 271 | no | Public domain |
| 11 | `11_cdc_cholera_response_haiti` | 169.1 s | 21.2 MB | 640×352 VP8 | field report (speaker count not checked); **mentions oral rehydration solution / ORS sachets** | 157.2 s | 382 | no | Public domain |
| 12 | `12_cdc_fight_germs_wash_hands` | 180.3 s | 41.0 MB | 1280×720 VP8 | narrated demonstration: steps and numbers ("25 times every hour", "20 seconds"); the longest clip | 161.9 s | 376 | no | Public domain |

Total: 22.4 minutes, 199 MB.

### Good first picks
- **Closest to the demo scenario:** 11 (ORS, cholera) and 01 / 12 (handwashing instructions).
- **One face, one voice (for scene and preview review):** 04.
- **Dialogue (segmentation stress test):** 10 (a Q&A, by its title; speaker turns not checked).
- **Numbers and step-by-step instructions (the digit and negation checks):** 01, 03, 05, 12.
- **Measuring ASR against a human reference:** 02, 06, 07, 08, 09 (they have `.en.srt`).
- **ASR stress test:** 02. The accented speaker made Whisper `small` write "The APing" for "Vaping" in its first sentence.
- **Low resolution:** 03 (480×360) and 11 (640×352).
- **AV1 codec:** 08. The app accepts AV1, but rendering needs an ffmpeg build that can decode it. Not yet tested through rendering.
- **Human reference translations in other languages:** 01. San Francisco also published the same video in Spanish, Mandarin,
  Cantonese, Filipino, Russian, Vietnamese and Arabic on Commons. **There is no Tamil version.**

## Sources and attribution

Full URLs, authors, SHA-1 (as published by Commons) and SHA-256 are in `manifest.json`.

| # | Commons page | Author / credit |
|---|---|---|
| 01 | [20200303 - SFGovTV - SFDPH WASH HANDS ENGLISH.webm](https://commons.wikimedia.org/wiki/File:20200303_-_SFGovTV_-_SFDPH_WASH_HANDS_ENGLISH.webm) | San Francisco Government Television (CC BY 3.0: attribution required) |
| 02 | [Why Teens are Attracted to Vaping.webm](https://commons.wikimedia.org/wiki/File:Why_Teens_are_Attracted_to_Vaping.webm) | National Institute on Drug Abuse (NIDA/NIH) |
| 03 | [Clean Hands Help Prevent the Flu.webm](https://commons.wikimedia.org/wiki/File:Clean_Hands_Help_Prevent_the_Flu.webm) | Centers for Disease Control and Prevention |
| 04 | [Addressing Parents’ Safety Concerns around HPV Vaccine- Dr. Alix Casler.webm](https://commons.wikimedia.org/wiki/File:Addressing_Parents%E2%80%99_Safety_Concerns_around_HPV_Vaccine-_Dr._Alix_Casler.webm) | Centers for Disease Control and Prevention |
| 05 | [What to expect when your child is vaccinated - How Vaccines Work.webm](https://commons.wikimedia.org/wiki/File:What_to_expect_when_your_child_is_vaccinated_-_How_Vaccines_Work.webm) | Centers for Disease Control and Prevention |
| 06 | [Anyone Can Become Addicted to Drugs.webm](https://commons.wikimedia.org/wiki/File:Anyone_Can_Become_Addicted_to_Drugs.webm) | National Institute on Drug Abuse (NIDA/NIH) |
| 07 | [Traumatic Brain Injury (TBI) in Kids.webm](https://commons.wikimedia.org/wiki/File:Traumatic_Brain_Injury_(TBI)_in_Kids.webm) | NIH |
| 08 | [Myopia and Eye Development.webm](https://commons.wikimedia.org/wiki/File:Myopia_and_Eye_Development.webm) | National Eye Institute, NIH |
| 09 | [How Ultrasound Imaging Works (Sonography).webm](https://commons.wikimedia.org/wiki/File:How_Ultrasound_Imaging_Works_(Sonography).webm) | NIBIB (NIH) |
| 10 | [Dr. Fauci Answers Questions About the J&J Vaccine Pause.webm](https://commons.wikimedia.org/wiki/File:Dr._Fauci_Answers_Questions_About_the_J%26J_Vaccine_Pause.webm) | The White House |
| 11 | [CDC Responds to Cholera in Haiti.webm](https://commons.wikimedia.org/wiki/File:CDC_Responds_to_Cholera_in_Haiti.webm) | Centers for Disease Control and Prevention |
| 12 | [Fight Germs. Wash Your Hands!.webm](https://commons.wikimedia.org/wiki/File:Fight_Germs._Wash_Your_Hands!.webm) | Centers for Disease Control and Prevention |

"Public domain" is the licence Commons records for these files (works of the US federal government). Health content can
date. Treat these as **test material for the workflow, not as current medical advice**.

## What was verified (2026-10-22)

- **Integrity:** every file's SHA-1 matches the SHA-1 that Commons publishes for it.
- **Upload compatibility:** all 12 pass `media_tools.validate_source` (container, codecs, audio stream present, ≤ 5 min).
- **Speech present:** faster-whisper `small` detected English (probability 0.98–1.00) with 155–382 words per clip.
- **Not verified:** a full run through the app (analysis, translation, rendering, export) on these clips. Nothing about
  translation quality has been measured.

## Candidates rejected

- *What You Need To Know About Handwashing* (CDC): the audio track is silent (−91 dB).
- *Gear Up for Food Safety* (USDA): music only, no speech.
- Wikipedia "VideoWiki" medical videos: the narration is synthetic text-to-speech, not real speech.
- *ASL Video Series* clips: sign language, no speech.
