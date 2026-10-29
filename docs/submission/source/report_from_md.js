// Builds a formatted .docx from docs/submission/REPORT_CONTENT_5CHAPTER.md
// (the college's 5-chapter micro-project format).
//
// Usage:
//   npm install --prefix /tmp/hl-docx docx
//   NODE_PATH=/tmp/hl-docx/node_modules node report_from_md.js <content.md> <out.docx>
//
// The Markdown file is the single source of truth: edit the text there, regenerate here.
// Front matter (cover page) is built by this script; the Abstract, list of figures/tables
// and chapters are parsed from the Markdown.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, PageBreak, Footer, PageNumber, TableOfContents,
  LevelFormat,
} = require("docx");

const MD = process.argv[2];
const OUT = process.argv[3];
if (!MD || !OUT) {
  console.error("usage: node report_from_md.js <content.md> <out.docx>");
  process.exit(1);
}
const ROOT = path.resolve(__dirname, "../../.."); // repo root
const SHOTS = path.join(ROOT, "docs/screenshots");

const FONT = "Times New Roman";
const TEXT_W = 8306; // A4 11906 - margins 2160/1440 (DXA)
const MAX_IMG_W = 560;

// Which figure caption gets which screenshot.
const FIG_IMAGES = {
  "4.1": "02-manager-project-list.png",
  "4.2": "03-manager-project-detail.png",
  "4.3": "05-reviewer-scene-review.png",
  "4.4": "06-identity-owner-consent.png",
  "4.5": "07-auditor-audit-trail.png",
  "4.6": "08-admin-policies-and-quota.png",
  "4.7": "04-operator-jobs.png",
};

// ---------- inline markup ----------
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, ...o });
function rich(text, base = {}) {
  const parts = String(text).split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g).filter(Boolean);
  return parts.map((p) => {
    if (p.startsWith("**") && p.endsWith("**") && p.length > 4)
      return run(p.slice(2, -2), { ...base, bold: true });
    if (p.startsWith("`") && p.endsWith("`"))
      return new TextRun({ text: p.slice(1, -1), font: "Courier New", size: 21, ...base });
    if (p.startsWith("*") && p.endsWith("*") && p.length > 2)
      return run(p.slice(1, -1), { ...base, italics: true });
    return run(p, base);
  });
}

const P = (t, o = {}) =>
  new Paragraph({
    children: rich(t),
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 360 },
    ...o.para,
  });

function bullet(t, level = 0, ref = "bullets") {
  return new Paragraph({
    children: rich(t),
    numbering: { reference: ref, level },
    spacing: { after: 60, line: 320 },
    alignment: AlignmentType.LEFT,
  });
}

// ---------- headings ----------
const hstyle = (id, name, size, before, after) => ({
  id, name, basedOn: "Normal", next: "Normal", quickFormat: true,
  run: { size, bold: true, color: "000000", font: FONT },
  paragraph: { spacing: { before, after }, outlineLevel: Number(id.slice(-1)) - 1 },
});

function H1(text, pageBreak = true) {
  return [
    ...(pageBreak ? [new Paragraph({ children: [new PageBreak()] })] : []),
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [run(text, { bold: true, size: 32 })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 360 },
    }),
  ];
}
function H2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [run(text, { bold: true, size: 28 })],
    spacing: { before: 280, after: 140 },
    keepNext: true,
  });
}
function H3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [run(text, { bold: true, size: 24 })],
    spacing: { before: 200, after: 100 },
    keepNext: true,
  });
}

// ---------- tables ----------
const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(rows) {
  const cols = Math.max(...rows.map((r) => r.length));
  const w = Math.floor(TEXT_W / cols);
  const cell = (t, i, head) =>
    new TableCell({
      borders,
      width: { size: w, type: WidthType.DXA },
      shading: head ? { fill: "D9E2E1", type: ShadingType.CLEAR, color: "auto" } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: String(t)
        .split("\n")
        .map(
          (line) =>
            new Paragraph({
              children: rich(line, { size: 20, bold: head || undefined }),
              spacing: { after: 20, line: 260 },
            })
        ),
    });
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    rows: rows.map(
      (r, ri) =>
        new TableRow({
          tableHeader: ri === 0,
          children: Array.from({ length: cols }, (_, ci) => cell(r[ci] ?? "", ci, ri === 0)),
        })
    ),
  });
}

// ---------- images ----------
function pngSize(buf) {
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}
function figureImage(num) {
  const file = FIG_IMAGES[num];
  if (!file) return null;
  const p = path.join(SHOTS, file);
  if (!fs.existsSync(p)) return null;
  const data = fs.readFileSync(p);
  const { width, height } = pngSize(data);
  const w = Math.min(MAX_IMG_W, width);
  const h = Math.round((height / width) * w);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: 80 },
    children: [new ImageRun({ data, transformation: { width: w, height: h } })],
  });
}

// ---------- cover page ----------
function cover() {
  const c = (t, o = {}) =>
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: o.after ?? 120 },
      children: [run(t, { bold: o.bold, size: o.size, italics: o.italics })],
    });
  return [
    c("A MICRO PROJECT REPORT", { bold: true, size: 26, after: 300 }),
    c("on", { size: 24, after: 300 }),
    c("HYPERLOCALIZE", { bold: true, size: 40, after: 80 }),
    c("CONTEXT-AWARE IDENTITY-PRESERVING VIDEO LOCALIZATION", { bold: true, size: 28, after: 400 }),
    c("Submitted by", { size: 24, after: 120 }),
    c("[STUDENT NAME]  —  [REGISTER NUMBER]", { bold: true, size: 26, after: 400 }),
    c("in partial fulfilment of the requirements for the award of the degree of", { size: 22, after: 120 }),
    c("[BACHELOR OF ENGINEERING / BACHELOR OF TECHNOLOGY]", { bold: true, size: 24, after: 120 }),
    c("in", { size: 22, after: 120 }),
    c("COMPUTER SCIENCE AND ENGINEERING", { bold: true, size: 24, after: 400 }),
    c("Under the guidance of", { size: 22, after: 100 }),
    c("[GUIDE NAME], [DESIGNATION]", { bold: true, size: 24, after: 400 }),
    c("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", { bold: true, size: 24, after: 60 }),
    c("[COLLEGE NAME], [PLACE]", { bold: true, size: 24, after: 60 }),
    c("[UNIVERSITY NAME]", { bold: true, size: 24, after: 300 }),
    c("[MONTH, YEAR]", { bold: true, size: 24, after: 200 }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ---------- markdown parsing ----------
const raw = fs.readFileSync(MD, "utf8").split(/\r?\n/);

// cut the "notes for you" section
const cut = raw.findIndex((l) => /^#+\s*Notes for you/i.test(l));
const lines = cut >= 0 ? raw.slice(0, cut) : raw;

const children = [];
const numberingConfigs = [
  {
    reference: "bullets",
    levels: [0, 1].map((l) => ({
      level: l,
      format: LevelFormat.BULLET,
      text: l ? "–" : "•",
      alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720 + l * 360, hanging: 360 } } },
    })),
  },
];
let numRef = 0;

function renderRange(part) {
  let i = 0;
  while (i < part.length) {
    const line = part[i];

    if (!line.trim()) { i++; continue; }
    if (/^>\s?/.test(line)) { i++; continue; }        // editorial instructions
    if (/^---+$/.test(line.trim())) { i++; continue; } // horizontal rule

    if (line.startsWith("```")) {                       // code block
      const buf = [];
      i++;
      while (i < part.length && !part[i].startsWith("```")) buf.push(part[i++]);
      i++;
      buf.forEach((l) =>
        children.push(
          new Paragraph({
            children: [new TextRun({ text: l || " ", font: "Courier New", size: 19 })],
            spacing: { after: 0, line: 240 },
            alignment: AlignmentType.LEFT,
            shading: { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" },
          })
        )
      );
      children.push(new Paragraph({ spacing: { after: 120 } }));
      continue;
    }

    if (line.trim().startsWith("|")) {                  // table
      const rows = [];
      while (i < part.length && part[i].trim().startsWith("|")) {
        const cells = part[i].trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((s) => s.trim());
        if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) rows.push(cells);
        i++;
      }
      if (rows.length) {
        children.push(table(rows));
        children.push(new Paragraph({ spacing: { after: 140 } }));
      }
      continue;
    }

    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      const level = h[1].length;
      const text = h[2].trim();
      if (level === 1) {
        if (/^Chapter\s+\d+/i.test(text) || /^References$/i.test(text)) H1(text).forEach((p) => children.push(p));
        else H1(text.replace(/^\d+\.\s*/, "")).forEach((p) => children.push(p));
      } else if (level === 2) children.push(H2(text));
      else children.push(H3(text));
      i++;
      continue;
    }

    const bl = line.match(/^(\s*)-\s+(.*)$/);
    if (bl) {
      children.push(bullet(bl[2], Math.min(1, Math.floor(bl[1].length / 2))));
      i++;
      continue;
    }

    const nl = line.match(/^\s*\d+\.\s+(.*)$/);
    if (nl) {
      // group the whole numbered list under one numbering instance
      const ref = `num${++numRef}`;
      numberingConfigs.push({
        reference: ref,
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      });
      while (i < part.length && /^\s*\d+\.\s+/.test(part[i])) {
        const m = part[i].match(/^\s*\d+\.\s+(.*)$/);
        children.push(bullet(m[1], 0, ref));
        i++;
      }
      continue;
    }

    // paragraph (join wrapped lines)
    const buf = [line.trim()];
    i++;
    while (
      i < part.length &&
      part[i].trim() &&
      !/^(#{1,6}\s|>\s?|\||```|\s*-\s|\s*\d+\.\s|---+$)/.test(part[i])
    ) {
      buf.push(part[i].trim());
      i++;
    }
    const text = buf.join(" ");

    const fig = text.match(/^\*\*Figure\s+(\d+\.\d+)/);
    if (fig) {
      const img = figureImage(fig[1]);
      if (img) children.push(img);
      children.push(
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200, line: 300 },
          children: rich(text, { size: 21 }),
        })
      );
      continue;
    }
    children.push(P(text));
  }
}

// split the front matter from the chapters
const idxAbstract = lines.findIndex((l) => /^#\s*2\.\s*Abstract/i.test(l));
const idxToc = lines.findIndex((l) => /^#\s*3\.\s*Table of Contents/i.test(l));
const idxLists = lines.findIndex((l) => /^#\s*4\.\s*List of Figures and Tables/i.test(l));
const idxCh1 = lines.findIndex((l) => /^#\s*Chapter\s+1/i.test(l));

children.push(...cover());

// Abstract
if (idxAbstract >= 0 && idxToc > idxAbstract) {
  H1("Abstract").forEach((p) => children.push(p));
  renderRange(lines.slice(idxAbstract + 1, idxToc));
}

// Table of contents (field; Word fills it when the user chooses "Update field")
if (idxToc >= 0) {
  H1("Table of Contents").forEach((p) => children.push(p));
  children.push(
    new Paragraph({
      children: [new TextRun({ text: "Right-click and choose “Update Field” to fill the page numbers.", italics: true, size: 20, font: FONT })],
      spacing: { after: 200 },
    })
  );
  children.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-3" }));
}

// List of figures and tables
if (idxLists >= 0 && idxCh1 > idxLists) {
  H1("List of Figures and Tables").forEach((p) => children.push(p));
  renderRange(lines.slice(idxLists + 1, idxCh1));
}

// Chapters + references
renderRange(lines.slice(idxCh1));

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: 24, color: "000000" }, paragraph: { spacing: { line: 360 } } },
    },
    paragraphStyles: [
      hstyle("Heading1", "Heading 1", 32, 120, 360),
      hstyle("Heading2", "Heading 2", 28, 280, 140),
      hstyle("Heading3", "Heading 3", 24, 200, 100),
    ],
  },
  numbering: { config: numberingConfigs },
  sections: [
    {
      properties: {
        page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1800 } },
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [new TextRun({ children: ["Page ", PageNumber.CURRENT], font: FONT, size: 18 })],
            }),
          ],
        }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log(`wrote ${OUT} (${(buf.length / 1024).toFixed(0)} KB, ${children.length} blocks)`);
});
