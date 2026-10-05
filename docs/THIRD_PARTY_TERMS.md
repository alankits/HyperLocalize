# Third-Party Models, Services and Their Terms

| | |
|---|---|
| **Date checked** | 2026-10-05 |
| **Budget rule (Q4, revised)** | **Zero spend.** Free tiers and open-source models only. No GPU on the laptop; Kaggle Notebooks (free, about 30 GPU hours/week) may be used for GPU-heavy steps. |
| **Status** | Reference document. Terms change, so re-check before the final evaluation. |

Facts were checked against the official pages listed. Anything not confirmed on an official page is marked **[UNVERIFIED]**.

## 1. Data-use warnings that must be disclosed

| Service | What happens to submitted data | Consequence for HyperLocalize |
|---|---|---|
| **Gemini API, free tier ("Unpaid Services")** | Google "uses the content you submit to the Services and any generated responses to provide, improve, and develop Google products and services and machine learning technologies". "Human reviewers may read, annotate, and process your API input and output." The terms say: **"Do not submit sensitive, confidential, or personal information to the Unpaid Services."** You must be 18 or older. | Only **team-authored, scripted, non-personal text** (segment text, glossary, audience profile) is sent. **Never audio**, never real third-party content, and never anything a speaker said that wasn't in the script. The consent form names Google and states that the text may be used for training and seen by human reviewers. [Gemini API terms](https://ai.google.dev/gemini-api/terms), [pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| **Groq, free plan** | Groq states it doesn't use inputs or outputs for training. They may be stored for 30 days unless Zero Data Retention is enabled [whether ZDR is available on the free plan is UNVERIFIED]. | ZDR is turned on. **Source audio is sent only with `external_transcription` consent (ADR 0006 CP0)**; local faster-whisper is the default. LLM text calls carry script text only. [Your data](https://console.groq.com/docs/your-data) |
| **Kaggle Notebooks** | Inputs (reference voice clip, texts) are uploaded as **private datasets**; outputs are stored as kernel output. GPU and internet need a **phone-verified account**. | Kaggle is named as a processor in the consent form. Datasets and kernels are deleted after import and on revocation (`kaggle datasets delete`, `kaggle kernels delete`). **There is no cancel command for a running kernel.** [kernels CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md), [datasets CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/datasets.md) |
| **ElevenLabs, free plan** (**dropped after review**; kept here for reference) | The free plan has **no commercial licence**. Published content must be attributed ("elevenlabs.io" or "11.ai" in the title). Instant Voice Cloning is **not** on the free plan. A data-use opt-out toggle exists. | Stock voice only, academic non-commercial use, attribution in the export manifest and demo credits. [Publishing](https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform), [pricing](https://elevenlabs.io/pricing) |

**Account status (reported by the user, 2026-10-05):**
- **Groq:** Zero Data Retention for Inference APIs is available and enabled on the team's free account. That settles the free-plan question in the table above **for inference APIs**. Whether it also covers the **speech-to-text (audio transcription) endpoint** is **[UNVERIFIED]**. Before any audio is sent, record evidence: the date, and a screenshot kept outside git. Until then, no audio goes to Groq.
- **Gemini:** API key created on a project with no Cloud Billing. The key goes in `.env` (git-ignored) and is never shared in chat or docs.
- **Kaggle:** account phone-verified.

## 2. Model licences

| Model | Use in HyperLocalize | Licence as stated | Notes |
|---|---|---|---|
| **IndicF5** (AI4Bharat) | Tamil voice cloning (`CLONED_VOICE`) | Hugging Face model card: **MIT**. Gated (you must agree to share contact details). | **Treated as non-commercial / research use only** (your instruction). The licence position is unclear: the GitHub repo shows **no licence file**, and IndicF5 builds on F5-TTS, whose official pretrained weights are **CC-BY-NC-4.0** (trained on the Emilia dataset). Whether that restriction carries over hasn't been established, so we take the conservative reading. Model card condition: "you agree to only clone voices for which you have explicit permission." Needs reference audio **and its transcript**. Output 24 kHz. [model card](https://huggingface.co/ai4bharat/IndicF5), [repo](https://github.com/AI4Bharat/IndicF5), [F5-TTS](https://huggingface.co/SWivid/F5-TTS) |
| **MMS-TTS Tamil** (`facebook/mms-tts-tam`) | Fast stock Tamil voice on CPU | **CC-BY-NC-4.0** | Non-commercial. VITS, 36.3M parameters, single speaker, no cloning. Needs a fixed seed for repeatable output. [model card](https://huggingface.co/facebook/mms-tts-tam) |
| **Indic Parler-TTS** (AI4Bharat) | Stock Tamil voice with named speakers ("Jaya", "Kavitha") | **Apache-2.0**. Gated. | 0.9B parameters; CPU speed is unmeasured. [model card](https://huggingface.co/ai4bharat/indic-parler-tts) |
| **IndicTrans2 En→Indic distilled 200M** | Context-free baseline (T0) and last-resort translation fallback | **MIT**. Gated. | Needs `IndicTransToolkit`; Tamil = `tam_Taml`. [model card](https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M) |
| **faster-whisper** | Local CPU transcription fallback | **MIT** (repository) | Supports int8 on CPU and word timestamps. The Whisper model weights are a separate artefact [UNVERIFIED in this session]. [repo](https://github.com/SYSTRAN/faster-whisper) |
| **ECAPA-TDNN speaker embedding** (e.g. SpeechBrain `spkrec-ecapa-voxceleb`) | Spike only: speaker-similarity check (M4), run locally; embeddings deleted after scoring | **[UNVERIFIED]**: check the model card before use | Not part of the app. Its training data (VoxCeleb) has its own terms [UNVERIFIED]. |
| Groq-hosted LLMs (production models `llama-3.3-70b-versatile`, `openai/gpt-oss-120b`; preview models not used) | Translation and meaning-check alternative | Groq service terms; model licences [UNVERIFIED] | Tamil quality is measured in the spike. [models](https://console.groq.com/docs/models) |

**Overall consequence:** several components are **non-commercial** (IndicF5 by our conservative reading, and MMS-TTS). HyperLocalize as built is an **academic, non-commercial demonstrator**. Commercial use would need different components. This is stated in the README, the export manifest and the viva.

## 3. Excluded because they conflict with zero spend

| Service | Why excluded |
|---|---|
| Google Cloud Text-to-Speech and Cloud Translation | Even the free tier needs a **billing account with a payment method**, and usage over the free quota is charged automatically. That's a real risk of spending under a zero-budget rule. [free features](https://docs.cloud.google.com/free/docs/free-cloud-features) |
| ElevenLabs Instant Voice Cloning | Paid plans only (Starter and up) |
| Claude API | Only a small one-off free credit; ongoing use is paid |
| Sarvam APIs | ₹100 one-off signup credits only; its privacy policy and Trust Center conflict on training use |
| Google Instant Custom Voice, Azure Personal Voice | Restricted access (allowlist or approval) |
