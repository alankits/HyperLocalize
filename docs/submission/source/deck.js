// Builds the HyperLocalize project presentation (.pptx) as a structured deck.
// Facts come from docs/STATUS.md, ARCHITECTURE.md, EVALUATION.md, the ADRs, the clip 01 trial record
// and the test run of 2026-10-22.
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const S = process.argv[2];
const OUT = process.argv[3];

const THEME = {
  name: "HyperLocalize",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F1E", lt1: "FFFFFF", dk2: "0F3B3A", lt2: "EDF3F1",
    accent1: "1F6F6B", accent2: "D99A00", accent3: "B8533A", accent4: "5B8E7D",
    accent5: "7F8C89", accent6: "2F4858", hlink: "1F6F6B", folHlink: "5B8E7D",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.title = "HyperLocalize: Project Presentation";
pres.author = "[STUDENT NAME]";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.4, fontSize: 54, bold: true, color: C.background1, fontFace: THEME.headFontFace, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.55, w: 11.7, h: 0.8, fontSize: 24, color: C.accent2, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.7, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.13, h: 0.85, fontSize: 32, bold: true, color: C.text2, fontFace: THEME.headFontFace, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "HyperLocalize · Context-Aware Identity-Preserving Video Localization", options: { x: 0.6, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 12.23, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent5, align: "right" },
});

// ---------- helpers ----------
async function icon(name, hex, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color: "#" + hex, size: px }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 });
function card(slide, x, y, w, h, name, fill = C.background2) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.12, objectName: name });
}
async function iconCircle(slide, x, y, d, name, bg = C.accent1, fg = HEX.lt1, objName = "icon") {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg, width: 0 }, objectName: objName + " circle" });
  const pad = d * 0.24;
  slide.addImage({ data: await icon(name, fg), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad, objectName: objName });
}
const txt = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, valign: "top", fontSize: 16, color: C.text1, ...o });
const bullets = (items, o = {}) => items.map((t, i) => ({ text: t, options: { bullet: { indent: 18 }, breakLine: i < items.length - 1, paraSpaceAfter: 6, ...o } }));
function content(title, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}

(async () => {
  // ===== Section: Introduction =====
  pres.addSection({ title: "Introduction" });
  {
    const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
    s.addText("HyperLocalize", { placeholder: "title" });
    s.addText("Context-Aware Identity-Preserving Video Localization", { placeholder: "body" });
    txt(s, [
      { text: "[STUDENT NAME]  ·  [REGISTER NUMBER]", options: { breakLine: true, bold: true } },
      { text: "Guide: [GUIDE NAME], [DESIGNATION]", options: { breakLine: true } },
      { text: "[DEPARTMENT OF CSE]  ·  [COLLEGE NAME]  ·  [MONTH YEAR]" },
    ], { x: 0.8, y: 5.3, w: 11.7, h: 1.2, fontSize: 18, color: C.background2, objectName: "presenter details" });
    s.addNotes("Introduce yourself and the project. HyperLocalize is a controlled workflow for localizing video, so that important information can cross language barriers without trusting AI output blindly. Replace the bracketed placeholders with your details before presenting.");
  }
  {
    const s = content("Automatic dubbing treats AI output as final", "Introduction");
    const items = [
      ["FaTriangleExclamation", "Trust", "A dropped \"not\" or a changed number (2 sachets → 5) can reverse a health message, and nobody is asked to check."],
      ["FaUserShield", "Identity", "Voice cloning can copy a real speaker. Consent is at best a one-time tick box, and revoking it rarely stops work in progress."],
      ["FaFileShield", "Accountability", "The output file carries no record of who reviewed it, which models made it, or which consent applied."],
    ];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.14;
      card(s, x, 1.55, 3.85, 4.2, `problem card ${i + 1}`);
      await iconCircle(s, x + 0.35, 1.9, 0.9, items[i][0], C.accent3, HEX.lt1, `problem icon ${i + 1}`);
      txt(s, items[i][1], { x: x + 0.35, y: 3.0, w: 3.15, h: 0.5, fontSize: 22, bold: true, color: C.text2, objectName: `problem title ${i + 1}` });
      txt(s, items[i][2], { x: x + 0.35, y: 3.6, w: 3.15, h: 2.0, fontSize: 16, objectName: `problem text ${i + 1}` });
    }
    txt(s, "Problem: build a localization workflow where AI output is only a draft, critical content is checked, a human approves every scene, identity is used only under valid consent, and every action is auditable.",
      { x: 0.6, y: 6.0, w: 12.13, h: 0.8, fontSize: 16, italic: true, color: C.accent1, objectName: "problem statement" });
    s.addNotes("Video carries public information in health, food, water and energy, but mostly in a few languages. ASR to MT to TTS pipelines make dubbing easy, but they create three problems: trust in critical facts, identity and consent when a voice is reproduced, and accountability for what was approved. The italic line is our problem statement.");
  }
  {
    const s = content("A controlled workflow, not an autonomous pipeline", "Introduction");
    card(s, 0.6, 1.5, 5.9, 5.2, "is card");
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.83, y: 1.5, w: 5.9, h: 5.2, fill: { color: C.background1 }, line: { color: C.accent5, width: 1 }, rectRadius: 0.12, objectName: "is not outline" });
    await iconCircle(s, 0.95, 1.8, 0.7, "FaCircleCheck", C.accent1, HEX.lt1, "is icon");
    await iconCircle(s, 7.18, 1.8, 0.7, "FaBan", C.accent5, HEX.lt1, "is not icon");
    txt(s, "HyperLocalize is", { x: 1.85, y: 1.9, w: 4.4, h: 0.5, fontSize: 22, bold: true, color: C.text2, objectName: "is heading" });
    txt(s, "HyperLocalize is not", { x: 8.08, y: 1.9, w: 4.4, h: 0.5, fontSize: 22, bold: true, color: C.text2, objectName: "is not heading" });
    txt(s, bullets([
      "A general, context-aware video localization workflow",
      "An information-access layer for important video information (health, food, water, energy)",
      "Human-reviewed: AI output is always a draft",
      "Consent-governed for any use of a speaker's identity",
      "Traceable: every governance action is audited",
    ]), { x: 0.95, y: 2.8, w: 5.3, h: 3.7, fontSize: 17, objectName: "is list" });
    txt(s, bullets([
      "A health, ORS or Tamil-only app (that is the demo scenario)",
      "A voice-cloning product",
      "A competitor on raw dubbing quality",
      "A fully autonomous pipeline",
      "A solution to physical problems in any domain",
      "Described as \"secure\", \"compliant\" or \"production-ready\"",
    ]), { x: 7.18, y: 2.8, w: 5.3, h: 3.7, fontSize: 17, objectName: "is not list" });
    s.addNotes("Positioning matters for the viva. The product is a general localization workflow. English to Tamil health information is only the current demo scenario. We make no security or compliance claims.");
  }
  {
    const s = content("Objectives", "Introduction");
    const obj = [
      ["FaLanguage", "Context-aware drafts", "Localize each line with its neighbours, speaker, audience, glossary and timing budget"],
      ["FaListCheck", "Critical-content checks", "Numbers, units, glossary, structure and overrun checks block approval"],
      ["FaRotate", "Scene-level regeneration", "Redo one problematic scene without touching the rest"],
      ["FaUserShield", "Enforced consent", "Backend gate at every stage; revocation stops running jobs"],
      ["FaClipboardCheck", "Approval and export gates", "Frozen snapshot, separation of duties, MOCK never exported"],
      ["FaHashtag", "Auditable evidence", "Hash-chained audit log; chain head inside every export"],
    ];
    for (let i = 0; i < 6; i++) {
      const col = i % 3, row = Math.floor(i / 3);
      const x = 0.6 + col * 4.14, y = 1.5 + row * 2.6;
      card(s, x, y, 3.85, 2.35, `objective card ${i + 1}`);
      await iconCircle(s, x + 0.3, y + 0.3, 0.7, obj[i][0], C.accent1, HEX.lt1, `objective icon ${i + 1}`);
      txt(s, obj[i][1], { x: x + 1.15, y: y + 0.38, w: 2.55, h: 0.6, fontSize: 18, bold: true, color: C.text2, valign: "middle", objectName: `objective title ${i + 1}` });
      txt(s, obj[i][2], { x: x + 0.3, y: y + 1.15, w: 3.3, h: 1.1, fontSize: 15, objectName: `objective text ${i + 1}` });
    }
    s.addNotes("Six objectives, each mapped to a use case. Also a constraint: zero rupee budget, so every AI stage is behind an interface and can run on free or local models.");
  }

  // ===== Section: Design =====
  pres.addSection({ title: "Design" });
  {
    const s = content("The workflow: AI drafts, humans decide", "Design");
    const steps = ["Create project", "Upload & analyze video", "Context-aware localization", "Generate preview", "Human review", "Regenerate scene (if needed)", "Approve", "Export package"];
    const human = new Set([4, 6]);
    for (let i = 0; i < 8; i++) {
      const row = Math.floor(i / 4), col = i % 4;
      const x = 0.6 + col * 3.1, y = 1.8 + row * 2.3;
      const fill = human.has(i) ? C.accent2 : C.accent1;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.6, h: 1.5, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.12, shadow: shadow(), objectName: `step ${i + 1}` });
      txt(s, [{ text: String(i + 1), options: { fontSize: 28, bold: true, breakLine: true } }, { text: steps[i], options: { fontSize: 16, bold: true } }],
        { x: x + 0.2, y: y + 0.15, w: 2.2, h: 1.25, color: human.has(i) ? C.text1 : C.background1, objectName: `step text ${i + 1}` });
      if (col < 3) s.addShape(pres.shapes.CHEVRON, { x: x + 2.72, y: y + 0.55, w: 0.26, h: 0.4, fill: { color: C.accent5 }, line: { color: C.accent5, width: 0 }, objectName: `arrow ${i + 1}` });
    }
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.25, w: 0.35, h: 0.35, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 }, rectRadius: 0.05, objectName: "legend human" });
    txt(s, "Human governance steps: only a person can accept, approve or export", { x: 1.1, y: 6.25, w: 6, h: 0.35, fontSize: 14, valign: "middle", objectName: "legend human text" });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.4, y: 6.25, w: 0.35, h: 0.35, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, rectRadius: 0.05, objectName: "legend system" });
    txt(s, "Asynchronous jobs: never block a web request", { x: 7.9, y: 6.25, w: 4.8, h: 0.35, fontSize: 14, valign: "middle", objectName: "legend system text" });
    s.addNotes("This is the confirmed workflow. Teal steps run as background jobs with explicit states. The two marigold steps are human gates: the reviewer accepts scenes, and a manager approves. Regeneration loops back for one scene only.");
  }
  {
    const s = content("Six actors, nine use cases", "Design");
    s.addImage({ path: path.join(S, "uml", "usecase.png"), x: 0.6, y: 1.35, w: 5.4 * 2352 / 2415, h: 5.4, objectName: "use case diagram" });
    const actors = [
      ["Localization Manager", "Creates projects, approves, exports"],
      ["Reviewer / Linguist", "Edits, overrides with reasons, regenerates, accepts scenes"],
      ["Media Operator", "Uploads video, links speakers, watches jobs"],
      ["Speaker / Identity Owner", "Grants, narrows, revokes or withdraws consent"],
      ["Administrator", "Users, provider chains, policies, quota limits (cannot grant consent)"],
      ["Auditor / Faculty Evaluator", "Inspects audit trail, verifies the hash chain"],
    ];
    actors.forEach(([a, d], i) => {
      const y = 1.5 + i * 0.88;
      card(s, 6.6, y, 6.13, 0.75, `actor card ${i + 1}`);
      txt(s, [{ text: a, options: { bold: true, color: C.text2, breakLine: true } }, { text: d, options: { fontSize: 14 } }], { x: 6.8, y: y + 0.08, w: 5.8, h: 0.62, fontSize: 16, objectName: `actor ${i + 1}` });
    });
    s.addNotes("The use-case diagram is drawn from the implemented code. Record Consent is an included sub-use case. Note separation of roles: the Administrator cannot grant consent on behalf of a speaker; a test proves it.");
  }
  {
    const s = content("Architecture: a modular monolith", "Design");
    s.addImage({ path: path.join(S, "uml", "components.png"), x: 0.6, y: 1.45, w: 8.0, h: 8.0 * 1092 / 2352, objectName: "component diagram" });
    const pts = [
      ["FaServer", "Web never blocks", "Long work becomes jobs in a hand-written PostgreSQL queue (SKIP LOCKED)"],
      ["FaGears", "Killable inference", "Models run in a subprocess the worker can kill on revocation"],
      ["FaLayerGroup", "9 Django apps", "Apps call each other only through services.py; no signals"],
    ];
    for (let i = 0; i < 3; i++) {
      const y = 1.45 + i * 1.75;
      await iconCircle(s, 8.95, y, 0.65, pts[i][0], C.accent1, HEX.lt1, `arch icon ${i + 1}`);
      txt(s, [{ text: pts[i][1], options: { bold: true, color: C.text2, fontSize: 18, breakLine: true } }, { text: pts[i][2], options: { fontSize: 15 } }], { x: 9.75, y, w: 2.98, h: 1.6, objectName: `arch point ${i + 1}` });
    }
    txt(s, "Why not microservices? One developer, a laptop demo and a ₹0 budget; database locks give consent the guarantees it needs (ADR 0001).", { x: 0.6, y: 5.6, w: 8.0, h: 0.9, fontSize: 15, italic: true, color: C.accent1, objectName: "arch rationale" });
    s.addNotes("One codebase, one database, a web process and worker processes with lanes. The identity app is the only consent decider and the audit app is the only audit writer. Every major choice is an ADR; 22 exist.");
  }
  {
    const s = content("Technology stack (₹0 budget)", "Design");
    const stack = [
      ["FaPython", "Django 6.1.1", "Backend, no REST framework"],
      ["FaDatabase", "PostgreSQL 17", "Data, job queue, audit triggers"],
      ["FaCode", "Templates + htmx", "Server-rendered pages per role"],
      ["FaFilm", "ffmpeg / ffprobe", "Validation, shot cuts, mixing"],
      ["FaMicrophone", "faster-whisper small", "English ASR on CPU (candidate)"],
      ["FaLanguage", "Gemini free tier", "Context-aware translation (candidate)"],
      ["FaWaveSquare", "MMS-TTS Tamil", "Stock voice on CPU (non-commercial licence)"],
      ["FaDocker", "Docker Compose", "Files written; not yet run"],
    ];
    for (let i = 0; i < 8; i++) {
      const col = i % 4, row = Math.floor(i / 4);
      const x = 0.6 + col * 3.1, y = 1.6 + row * 2.55;
      card(s, x, y, 2.85, 2.25, `stack card ${i + 1}`);
      await iconCircle(s, x + 0.3, y + 0.3, 0.7, stack[i][0], i >= 4 && i <= 6 ? C.accent2 : C.accent1, HEX.lt1, `stack icon ${i + 1}`);
      txt(s, stack[i][1], { x: x + 0.3, y: y + 1.12, w: 2.4, h: 0.45, fontSize: 18, bold: true, color: C.text2, objectName: `stack name ${i + 1}` });
      txt(s, stack[i][2], { x: x + 0.3, y: y + 1.55, w: 2.4, h: 0.6, fontSize: 14, objectName: `stack role ${i + 1}` });
    }
    txt(s, "Marigold = AI candidates behind provider interfaces; final choices wait for the measured evaluation (spike).", { x: 0.6, y: 6.55, w: 12.13, h: 0.35, fontSize: 14, italic: true, color: C.accent5, objectName: "stack note" });
    s.addNotes("Everything runs on one laptop: i5-13450HX, 14 GiB RAM, Ubuntu. The three AI providers are candidates, not final choices. Voice cloning is still a mock. Docker files exist but have not been run because Docker is not installed.");
  }

  // ===== Section: Implementation =====
  pres.addSection({ title: "Implementation" });
  {
    const s = content("Context-aware localization", "Implementation");
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 2.65, y: 3.2, w: 2.9, h: 1.4, fill: { color: C.text2 }, line: { color: C.text2, width: 0 }, rectRadius: 0.12, shadow: shadow(), objectName: "draft box" });
    txt(s, [{ text: "Segment draft", options: { bold: true, fontSize: 20, breakLine: true } }, { text: "subtitle + speakable speech + rationale", options: { fontSize: 13 } }], { x: 2.8, y: 3.35, w: 2.6, h: 1.1, color: C.background1, align: "center", valign: "middle", objectName: "draft text" });
    const chips = [
      ["2 neighbouring lines each side", 0.6, 1.5], ["Speaker", 3.0, 1.5], ["Audience profile", 5.4, 1.5],
      ["Glossary", 0.6, 5.5], ["Length budget (11 chars/s)", 3.0, 5.5], ["Reviewer instruction", 5.4, 5.5],
    ];
    chips.forEach(([t, x, y], i) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.2, h: 0.8, fill: { color: C.background2 }, line: { color: C.accent1, width: 1 }, rectRadius: 0.3, objectName: `context chip ${i + 1}` });
      txt(s, t, { x: x + 0.1, y, w: 2.0, h: 0.8, fontSize: 14, align: "center", valign: "middle", color: C.text2, objectName: `context chip text ${i + 1}` });
      const top = y < 3;
      s.addShape(pres.shapes.LINE, { x: Math.min(x + 1.1, 4.1), y: top ? y + 0.8 : 4.6, w: Math.max(Math.abs(x + 1.1 - 4.1), 0.001), h: top ? 3.2 - (y + 0.8) : y - 4.6, flipH: x + 1.1 > 4.1, flipV: !top, line: { color: C.accent5, width: 1.25 }, objectName: `context link ${i + 1}` });
    });
    card(s, 8.3, 1.5, 4.43, 4.8, "batching card");
    txt(s, "Quota-safe by design", { x: 8.6, y: 1.75, w: 3.9, h: 0.5, fontSize: 20, bold: true, color: C.text2, objectName: "batching title" });
    txt(s, bullets([
      "Free tier: about 20 requests / day / model (measured)",
      "Whole clip in 1 request, meaning check in 1 more (was ~16 for clip 01)",
      "Provider fails → scenes stay PENDING, \"Translation pending\" + Retry",
      "Never silently fills in MOCK text",
      "Every draft records its context, adapter, model and prompt version",
    ]), { x: 8.6, y: 2.4, w: 3.9, h: 3.8, fontSize: 15, objectName: "batching list" });
    txt(s, "Visual context is not used yet. Whether context improves quality is NOT MEASURED.", { x: 0.6, y: 6.55, w: 12.13, h: 0.35, fontSize: 14, italic: true, color: C.accent3, objectName: "context caveat" });
    s.addNotes("Each segment is sent with its context. The length budget comes from the stock voice's measured speaking rate. The prompt tells the model never to drop a number, unit, negation, warning or instruction to fit. Be honest in the viva: we have not yet measured whether context helps; that is the planned ablation.");
  }
  {
    const s = content("Critical-content checks block approval", "Implementation");
    const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.accent1 } } });
    const rows = [
      [hdr("Check"), hdr("What it catches"), hdr("Effect")],
      ["Numbers", "Changed or missing numbers; Tamil digits and number words 0–100", "FAIL / UNVERIFIABLE"],
      ["Units", "Missing or changed units; declared conversions", "FAIL / UNVERIFIABLE"],
      ["Glossary", "Key terms not using an accepted target form (prefix match for inflections)", "No forms → UNVERIFIABLE, never PASS"],
      ["Structure", "Empty, untranslated, mostly Latin script, over reading budget", "FAIL"],
      ["Speech overrun", "Line still too long at the 1.2× speed-up cap", "FAIL: \"shorten the speech\""],
      ["AI meaning flag", "Possible meaning reversal, e.g. a dropped \"not\"", "Needs acknowledgement"],
    ];
    s.addTable(rows, { x: 0.6, y: 1.5, w: 12.13, colW: [2.3, 6.63, 3.2], fontSize: 15, color: C.text1, border: { type: "solid", pt: 0.75, color: "C9D6D3" }, fill: { color: C.background1 }, rowH: 0.62, valign: "middle", margin: [4, 8, 4, 8], objectName: "checks table" });
    await iconCircle(s, 0.6, 6.05, 0.6, "FaLock", C.accent3, HEX.lt1, "checks icon");
    txt(s, "A FAIL or UNVERIFIABLE result blocks approval until the text is fixed or a reviewer overrides it with a written, audited reason. Known gap: numbers are compared as counts, not positions.", { x: 1.4, y: 6.0, w: 11.33, h: 0.75, fontSize: 15, valign: "middle", objectName: "checks note" });
    s.addNotes("Rules are explainable and deterministic, so they are the gate. AI only flags, and a flag is never called verification. Unverifiable is fail-safe: if the system can't prove a term is right, a person must confirm it. Known limitation: swapping 2 tablets 3 times to 3 tablets 2 times still passes the count-based number check.");
  }
  {
    const s = content("Consent is enforced in the backend", "Implementation");
    card(s, 0.6, 1.5, 5.6, 5.25, "gate card");
    txt(s, "Identity use is allowed only if", { x: 0.9, y: 1.7, w: 5.0, h: 0.5, fontSize: 20, bold: true, color: C.text2, objectName: "gate title" });
    txt(s, bullets([
      "the owner has not withdrawn",
      "project consent is ACTIVE, unexpired, covers the use and language",
      "it sits within an ACTIVE standing consent for this purpose",
      "the job is not flagged for cancellation",
      "re-checked at every stage boundary (checkpoints CP1–CP10), under a row lock on save",
      "only the owner can grant; an Administrator's grant is refused",
    ]), { x: 0.9, y: 2.35, w: 5.0, h: 4.2, fontSize: 15, objectName: "gate list" });
    txt(s, "On revocation", { x: 6.6, y: 1.5, w: 6.1, h: 0.5, fontSize: 20, bold: true, color: C.text2, objectName: "cascade title" });
    const cascade = ["Running job: worker polls every ~1 s and kills the subprocess", "Scenes → NEEDS_REGENERATION; render jobs cancelled", "This owner's audio quarantined, then purged", "Only approvals and exports with this voice invalidated", "Stock-voice fallback queued; must be reviewed again"];
    for (let i = 0; i < cascade.length; i++) {
      const y = 2.1 + i * 0.82;
      s.addShape(pres.shapes.OVAL, { x: 6.6, y: y + 0.08, w: 0.5, h: 0.5, fill: { color: C.accent3 }, line: { color: C.accent3, width: 0 }, objectName: `cascade num ${i + 1}` });
      txt(s, String(i + 1), { x: 6.6, y: y + 0.08, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle", objectName: `cascade num text ${i + 1}` });
      txt(s, cascade[i], { x: 7.3, y, w: 5.43, h: 0.66, fontSize: 15, valign: "middle", objectName: `cascade step ${i + 1}` });
    }
    txt(s, [{ text: "< 8 s", options: { fontSize: 30, bold: true, color: C.accent3 } }, { text: "   mid-job stop test bound (actual stop time not recorded)", options: { fontSize: 14, color: C.accent5 } }], { x: 6.6, y: 6.2, w: 6.13, h: 0.55, valign: "middle", objectName: "stop stat" });
    s.addNotes("Consent is safety-critical, so a UI check is not enough. The gate is one function, identity.services.evaluate, re-run at every stage boundary. Revocation is one transaction plus a kill of the running inference subprocess. Exports already downloaded cannot be recalled, and the system says so honestly.");
  }
  {
    const s = content("Three gates before anything leaves the system", "Implementation");
    const cols = [
      ["FaMagnifyingGlass", "Review", ["Edits create new HUMAN versions", "Override only with a written reason", "AI flags need acknowledgement", "Accept only with no open checks and a current preview", "Regenerate one scene, with an instruction"]],
      ["FaClipboardCheck", "Approve", ["Every scene accepted", "No blocking checks on latest versions", "Consent CP8 passes", "Separation of duties: approver did not edit", "Freezes an immutable snapshot"]],
      ["FaFileExport", "Export", ["Refused if any artefact is MOCK", "Refused if quarantined or CP9 fails", "MP4 + SRT + VTT (tagged Tamil)", "script.json, quality_report.json", "evidence_manifest.json with chain head"]],
    ];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.14;
      card(s, x, 1.5, 3.85, 4.4, `gate col ${i + 1}`);
      await iconCircle(s, x + 0.3, 1.8, 0.75, cols[i][0], i === 1 ? C.accent2 : C.accent1, HEX.lt1, `gate icon ${i + 1}`);
      txt(s, cols[i][1], { x: x + 1.25, y: 1.85, w: 2.4, h: 0.65, fontSize: 24, bold: true, color: C.text2, valign: "middle", objectName: `gate col title ${i + 1}` });
      txt(s, bullets(cols[i][2]), { x: x + 0.3, y: 2.8, w: 3.3, h: 3.0, fontSize: 15, objectName: `gate col list ${i + 1}` });
    }
    txt(s, "Any edit, regeneration or revocation after approval invalidates it. Exports already downloaded cannot be recalled, and the system says so.", { x: 0.6, y: 6.15, w: 12.13, h: 0.6, fontSize: 15, italic: true, color: C.accent1, objectName: "gates note" });
    s.addNotes("Any change after approval invalidates it. The export refusal of MOCK output is a hard rule, which is what keeps placeholder output from ever being presented as real. Since 22 October a project rule also says the AI assistant used in development never reviews, approves or exports.");
  }
  {
    const s = content("Audit: an append-only hash chain", "Implementation");
    const labels = ["CONSENT_GRANTED", "SCENE_ACCEPTED", "APPROVED", "EXPORT_CREATED"];
    for (let i = 0; i < 4; i++) {
      const x = 0.6 + i * 3.1;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.7, w: 2.6, h: 1.45, fill: { color: C.background2 }, line: { color: C.accent1, width: 1.5 }, rectRadius: 0.1, objectName: `block ${i + 1}` });
      txt(s, [{ text: `#${i + 41}  ${labels[i]}`, options: { bold: true, color: C.text2, fontSize: 14, breakLine: true } }, { text: "who · what · when · project · scene · consent version", options: { fontSize: 12, breakLine: true } }, { text: `prev: ${["9f2c…", "a71e…", "3b08…", "e5d4…"][i]}`, options: { fontSize: 12, color: C.accent1 } }],
        { x: x + 0.15, y: 1.85, w: 2.3, h: 1.2, objectName: `block text ${i + 1}` });
      if (i < 3) s.addShape(pres.shapes.LINE, { x: x + 2.6, y: 2.42, w: 0.5, h: 0, line: { color: C.accent1, width: 2, endArrowType: "triangle" }, objectName: `chain link ${i + 1}` });
    }
    txt(s, "Illustrative records; hash values shortened", { x: 0.6, y: 3.3, w: 6, h: 0.3, fontSize: 11, italic: true, color: C.accent5, objectName: "illustration note" });
    card(s, 0.6, 3.95, 12.13, 0.9, "formula card", C.text2);
    txt(s, "hash = SHA-256( prev_hash + canonical_json(record) )", { x: 0.9, y: 3.95, w: 11.5, h: 0.9, fontSize: 24, bold: true, color: C.background1, fontFace: "Courier New", valign: "middle", objectName: "formula" });
    txt(s, bullets([
      "One writer (audit.services.record); appends serialised by locking one chain-head row",
      "PostgreSQL triggers reject UPDATE, DELETE and TRUNCATE",
      "verify_audit_chain recomputes every hash; each export manifest carries the chain head",
    ]), { x: 0.6, y: 5.2, w: 8.2, h: 1.5, fontSize: 16, objectName: "audit list" });
    txt(s, [{ text: "Tamper-evident,", options: { breakLine: true } }, { text: "not tamper-proof" }], { x: 9.1, y: 5.25, w: 3.63, h: 1.2, fontSize: 24, bold: true, italic: true, color: C.accent3, align: "right", objectName: "audit claim" });
    s.addNotes("Each record includes the previous hash, so changing any old record breaks every later hash. Someone with full database rights could rebuild the whole chain, which is why we copy the head into every exported package and why we say tamper-evident, never tamper-proof.");
  }
  {
    const s = content("Data model: 28 classes in 9 apps", "Implementation");
    s.addImage({ path: path.join(S, "uml", "er_core.png"), x: 0.6, y: 1.35, w: 8.1, h: 8.1 * 2823 / 4152, objectName: "er diagram" });
    txt(s, "Key invariants", { x: 9.1, y: 1.5, w: 3.63, h: 0.5, fontSize: 20, bold: true, color: C.text2, objectName: "invariants title" });
    txt(s, bullets([
      "Translations, consent versions and audit records are append-only",
      "An Approval stores a snapshot of exact version ids",
      "Every AI artefact records adapter, model, prompt version and is_mock",
      "The full class diagram is generated from the Django models",
    ]), { x: 9.1, y: 2.1, w: 3.63, h: 4.6, fontSize: 15, objectName: "invariants list" });
    s.addNotes("This is the core of ADR 0014. The full generated class diagram is in the report appendix and in docs/uml. Versioning is what makes stale previews and invalid approvals detectable.");
  }
  {
    const s = content("One page per role", "Implementation");
    s.addImage({ path: path.join(S, "shots", "wide-05-reviewer-scene-review.png"), x: 0.6, y: 1.45, w: 5.9, h: 5.9 * 768 / 1366, objectName: "reviewer screenshot" });
    s.addImage({ path: path.join(S, "shots", "wide-06-identity-owner-consent.png"), x: 6.83, y: 1.45, w: 5.9, h: 5.9 * 768 / 1366, objectName: "consent screenshot" });
    txt(s, "Reviewer: preview, per-line checks, override with reason, regenerate this scene only", { x: 0.6, y: 4.95, w: 5.9, h: 0.7, fontSize: 14, color: C.text2, objectName: "reviewer caption" });
    txt(s, "Speaker / Identity Owner: standing and project consent, reference clip, revoke, withdraw", { x: 6.83, y: 4.95, w: 5.9, h: 0.7, fontSize: 14, color: C.text2, objectName: "consent caption" });
    txt(s, "Screenshots from a seeded test database (2026-10-12). The purple banner and MOCK badges are deliberate: placeholder output is always labelled.", { x: 0.6, y: 6.0, w: 12.13, h: 0.6, fontSize: 14, italic: true, color: C.accent5, objectName: "shots note" });
    s.addNotes("Server-rendered pages with htmx. Eight role pages were checked in headless Chromium. If time allows, switch to the live demo here: upload, analysis, review page, then revoke consent and show the fallback.");
  }

  // ===== Section: Results =====
  pres.addSection({ title: "Results" });
  {
    const s = content("Testing: negative-first, all measured", "Results");
    const stats = [["210", "tests passed", "2 optional real-model tests skipped · 125 s · 2026-10-22"], ["15/15", "end-to-end HTTP steps", "live server + worker · 2026-10-06"], ["11", "black-box tests passed", "equivalence partitions + boundary values"], ["1 + 6", "review findings fixed", "1 blocker, 6 majors in consent and audit code"]];
    for (let i = 0; i < 4; i++) {
      const x = 0.6 + i * 3.1;
      card(s, x, 1.5, 2.85, 2.7, `stat card ${i + 1}`);
      txt(s, stats[i][0], { x: x + 0.25, y: 1.7, w: 2.4, h: 1.0, fontSize: 48, bold: true, color: C.accent1, fontFace: THEME.headFontFace, objectName: `stat value ${i + 1}` });
      txt(s, stats[i][1], { x: x + 0.25, y: 2.7, w: 2.4, h: 0.45, fontSize: 17, bold: true, color: C.text2, objectName: `stat label ${i + 1}` });
      txt(s, stats[i][2], { x: x + 0.25, y: 3.2, w: 2.4, h: 0.9, fontSize: 13, color: C.accent5, objectName: `stat detail ${i + 1}` });
    }
    txt(s, "What the tests prove", { x: 0.6, y: 4.5, w: 6, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: "proves title" });
    txt(s, bullets([
      "Every tested denied consent state is refused; a real subprocess is killed mid-job",
      "0 bypasses of the review and approval gates in the tested cases; MOCK never exportable",
      "Audit edits rejected by the database; tampering detected by the verifier",
    ]), { x: 0.6, y: 5.0, w: 7.6, h: 1.8, fontSize: 15, objectName: "proves list" });
    txt(s, "Not tested yet", { x: 8.6, y: 4.5, w: 4.13, h: 0.45, fontSize: 20, bold: true, color: C.accent3, objectName: "not tested title" });
    txt(s, bullets(["Real models at evaluation scale", "Docker images", "Browser form submission", "Performance and load"]), { x: 8.6, y: 5.0, w: 4.13, h: 1.8, fontSize: 15, objectName: "not tested list" });
    s.addNotes("Tests run on real PostgreSQL and real ffmpeg with mock AI providers. Consent tests were written negative-first. The black-box suite uses equivalence partitioning and boundary value analysis: for a one-second line the budget is 28 characters, so 28 passes and 29 fails.");
  }
  {
    const s = content("First real clip: a trial that found real problems", "Results");
    const r = [1.78, 1.70, 1.28, 0.98, 1.48, 0.95, 1.17, 1.34, 1.77, 1.38, 1.40, 2.02, 1.22, 1.39];
    const labels = r.map((_, i) => String(i + 1));
    s.addChart([
      { type: pres.charts.BAR, data: [{ name: "Speech ÷ slot length", labels, values: r }], options: { chartColors: [HEX.accent1], barGapWidthPct: 60 } },
      { type: pres.charts.LINE, data: [{ name: "Fits (1.0)", labels, values: r.map(() => 1) }], options: { chartColors: [HEX.accent3], lineSize: 2, lineDataSymbol: "none", lineDash: "dash" } },
    ], {
      x: 0.6, y: 1.4, w: 7.6, h: 5.0, barDir: "col",
      showTitle: true, title: "Tamil speech length ÷ time slot, per line (clip 01)", titleFontSize: 14, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
      catAxisTitle: "Line", showCatAxisTitle: true, catAxisTitleFontSize: 12, catAxisTitleColor: HEX.accent5,
      catAxisLabelColor: HEX.accent5, valAxisLabelColor: HEX.accent5, catAxisLabelFontSize: 12, valAxisLabelFontSize: 12,
      catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valAxisMinVal: 0, valAxisMaxVal: 2.25, valAxisMajorUnit: 0.5,
      valGridLine: { color: "E3E9E7", size: 0.75 }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: HEX.dk1, legendFontFace: "+mn-lt",
      objectName: "timing chart",
    });
    const facts = [["14 / 14", "lines translated by Gemini (after HTTP 429 and 503 fallbacks)"], ["2 / 14", "lines fitted their slot: 79.1 s of speech for 58.0 s"], ["0.16", "back-transcription CER (intelligibility PROXY, not a listening test)"]];
    facts.forEach(([v, d], i) => {
      const y = 1.5 + i * 1.45;
      txt(s, v, { x: 8.6, y, w: 4.13, h: 0.65, fontSize: 32, bold: true, color: i === 1 ? C.accent3 : C.accent1, fontFace: THEME.headFontFace, objectName: `trial value ${i + 1}` });
      txt(s, d, { x: 8.6, y: y + 0.65, w: 4.13, h: 0.7, fontSize: 14, objectName: `trial detail ${i + 1}` });
    });
    card(s, 8.6, 5.9, 4.13, 0.85, "caveat card");
    txt(s, "MEASURED on n = 1 public clip (58 s, CC BY 3.0). Directional, not a quality evaluation.", { x: 8.75, y: 5.9, w: 3.85, h: 0.85, fontSize: 13, italic: true, valign: "middle", color: C.text2, objectName: "trial caveat" });
    s.addNotes("Upload, Whisper, Gemini, MMS-TTS, end to end on one public hand-washing video. Translation kept every number and the negation, by my reading, which is unverified until a Tamil rater checks it. Timing was poor: only two lines fit. Important honesty point: the review in that run was done by the AI assistant, so that export was withdrawn and is never cited as human-reviewed.");
  }
  {
    const s = content("What the trial changed (ADR 0022)", "Results");
    const rows = [
      ["FaBolt", "Free-tier quota ran out; chain silently fell back to MOCK", "Batch whole clip: ~16 → 2 requests; never fall back to MOCK after a real failure; \"translation pending\" + Retry"],
      ["FaClock", "Only 2 / 14 lines fitted their slot", "Length budget in the prompt (11 chars/s); speed-up cap 1.2×; blocking overrun check"],
      ["FaGlobe", "Export tracks tagged \"und\"", "Audio and subtitles tagged with the target language (tam)"],
      ["FaHashtag", "Tamil number words unverifiable", "Draft parser for 0–100: a wrong number word now FAILS"],
    ];
    txt(s, "Problem observed", { x: 1.5, y: 1.45, w: 4.6, h: 0.4, fontSize: 15, bold: true, color: C.accent5, objectName: "col head problem" });
    txt(s, "Change made and tested", { x: 6.6, y: 1.45, w: 6.13, h: 0.4, fontSize: 15, bold: true, color: C.accent5, objectName: "col head fix" });
    for (let i = 0; i < 4; i++) {
      const y = 1.95 + i * 1.15;
      card(s, 0.6, y, 12.13, 1.0, `change row ${i + 1}`);
      await iconCircle(s, 0.8, y + 0.18, 0.64, rows[i][0], C.accent1, HEX.lt1, `change icon ${i + 1}`);
      txt(s, rows[i][1], { x: 1.6, y, w: 4.6, h: 1.0, fontSize: 15, valign: "middle", objectName: `change problem ${i + 1}` });
      txt(s, rows[i][2], { x: 6.6, y, w: 5.95, h: 1.0, fontSize: 15, valign: "middle", color: C.text2, objectName: `change fix ${i + 1}` });
    }
    txt(s, "Re-run (project 5) stopped honestly at \"translation pending\": daily quota used, 0 translations, 0 MOCK. The timing fix is NOT yet re-measured.", { x: 0.6, y: 6.6, w: 12.13, h: 0.4, fontSize: 14, italic: true, color: C.accent3, objectName: "rerun note" });
    s.addNotes("Every problem the trial found was turned into a design change with tests: 210 pass. The re-run then hit the daily quota and did exactly what it should: no fake text, a clear pending state, and a retry button. The improvement in timing is not measured yet, so I don't claim it.");
  }
  {
    const s = content("Honest status of the nine use cases", "Results");
    const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.accent1 } } });
    const rows = [
      [hdr("Use case"), hdr("Status (2026-10-22)")],
      ["UC1 Create and Generate a Localization Project", "Implemented and tested"],
      ["UC2 Upload and Analyze Source Video", "Implemented; faster-whisper ran on real clips; no diarization"],
      ["UC3 Context-Aware Localization Preview", "Implemented; Gemini candidate partial; quality not measured"],
      ["UC4 Generate Localized Preview", "Stock voice real (MMS-TTS); cloned voice MOCK"],
      ["UC5 Review and Regenerate a Scene", "Implemented and tested"],
      ["UC6 Approve and Export Localization Package", "Implemented and tested"],
      ["UC7 Revoke Consent and Stop Identity", "Implemented and tested with MOCK voices"],
      ["UC8 Administer Users, Providers and Policies", "Implemented and tested"],
      ["UC9 Inspect Quality, Audit and Evidence", "Implemented and tested"],
    ];
    s.addTable(rows, { x: 0.6, y: 1.45, w: 12.13, colW: [5.6, 6.53], fontSize: 15, color: C.text1, border: { type: "solid", pt: 0.75, color: "C9D6D3" }, fill: { color: C.background1 }, rowH: 0.5, valign: "middle", margin: [3, 8, 3, 8], objectName: "status table" });
    txt(s, "Not measured yet: transcription WER, translation quality (MQM, chrF), speaker similarity, speed, and whether context helps.", { x: 0.6, y: 6.55, w: 12.13, h: 0.4, fontSize: 14, italic: true, color: C.accent3, objectName: "status caveat" });
    s.addNotes("This table is copied from docs/STATUS.md, our honest source of truth. Implemented means written and tested. The governance features are solid; the AI quality claims are not yet measured, and I say so.");
  }

  // ===== Section: Conclusion =====
  pres.addSection({ title: "Conclusion" });
  {
    const s = content("Limitations and future work", "Conclusion");
    card(s, 0.6, 1.5, 5.9, 4.4, "limits card");
    card(s, 6.83, 1.5, 5.9, 4.4, "future card");
    await iconCircle(s, 0.9, 1.8, 0.65, "FaTriangleExclamation", C.accent3, HEX.lt1, "limits icon");
    await iconCircle(s, 7.13, 1.8, 0.65, "FaRoad", C.accent1, HEX.lt1, "future icon");
    txt(s, "Limitations", { x: 1.75, y: 1.85, w: 4.5, h: 0.55, fontSize: 22, bold: true, color: C.text2, valign: "middle", objectName: "limits title" });
    txt(s, "Future work", { x: 7.98, y: 1.85, w: 4.5, h: 0.55, fontSize: 22, bold: true, color: C.text2, valign: "middle", objectName: "future title" });
    txt(s, bullets([
      "Formal evaluation not run; one real clip so far",
      "Cloned voice is MOCK; no faces or lip-sync",
      "No speaker diarization or visual context",
      "Number check compares counts, not positions",
      "Free tier ≈ 20 requests/day; Docker not yet run",
    ]), { x: 0.9, y: 2.7, w: 5.3, h: 3.0, fontSize: 16, objectName: "limits list" });
    txt(s, bullets([
      "Run the spike: consented speakers, Tamil raters, MQM, WER, listening tests",
      "Context ablation vs an IndicTrans2 baseline",
      "Choose a cloned-voice provider from measured results",
      "Re-measure timing after ADR 0022",
      "Diarization, visual context, more language pairs",
    ]), { x: 7.13, y: 2.7, w: 5.3, h: 3.0, fontSize: 16, objectName: "future list" });
    txt(s, "Lip-sync and face processing stay future scope: they would need their own consent design.", { x: 0.6, y: 6.15, w: 12.13, h: 0.6, fontSize: 15, italic: true, color: C.accent1, objectName: "future note" });
    s.addNotes("Limitations first, then what removes them. The spike needs consent forms, two speakers and Tamil-literate raters, so it is planned rather than done. Lip-sync and faces stay out of scope until they have their own consent design.");
  }
  {
    const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Conclusion" });
    s.addText("Thank you", { placeholder: "title" });
    s.addText("Questions?", { placeholder: "body" });
    txt(s, "HyperLocalize turns commodity AI models into an accountable workflow: drafts are checked, humans decide, consent is enforced, and every export carries its own evidence.",
      { x: 0.8, y: 5.0, w: 11.7, h: 1.2, fontSize: 20, italic: true, color: C.background2, objectName: "closing message" });
    s.addNotes("Close with the one-sentence summary. Likely questions and honest answers are in docs/VIVA.md: is this just ASR to MT to TTS; how do you know context helps; what is identity here; can an admin enable someone's voice; is the audit log tamper-proof.");
  }

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
