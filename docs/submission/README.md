# College submission: report and presentation

Built 2026-10-22/23 from `docs/STATUS.md`, `docs/ARCHITECTURE.md`, `docs/EVALUATION.md`, `docs/TESTING.md`, the ADRs and the clip 01 trial record. The facts are as of 2026-10-22.

| File | What |
|---|---|
| `HyperLocalize_Project_Report.docx` | Project report (54 pages, A4): front matter, 8 chapters, references, appendices A–E |
| `HyperLocalize_Project_Report.pdf` | The same report as a PDF, with the table of contents filled in |
| `HyperLocalize_Presentation.pptx` | 21-slide deck (16:9) with speaker notes on every slide |
| `HyperLocalize_Presentation.pdf` | The same deck as a PDF |
| `source/` | The generators (`report.js`, `deck.js`, `chart.js`, `topdf.py`) and the core ER diagram source |
| `REPORT_CONTENT_5CHAPTER.md` | **College 5-chapter format** (Cover → Abstract → TOC → List of Figures/Tables → Ch. 1–5 → References). Full report text, restructured 2026-10-30 from the documents and the 2026-10-29 run |
| `HyperLocalize_Report_5Chapter.docx` | The 5-chapter report in Word, generated from the Markdown, with the seven 2026-10-12 screenshots embedded |
| `source/report_from_md.js` | Generator: Markdown → formatted .docx (headings, TOC field, tables, screenshots) |

## Before submitting

- **Fill in the placeholders.** Every `[BRACKETED]` field is a placeholder: student name, register number, degree, guide, HOD, principal, college, university, place, date and month/year. They appear on the title page, the bonafide certificate, the declaration, the acknowledgement and slide 1. Then regenerate the PDF (in Word: File → Export → PDF).
- **In Word, accept "update fields"** when it asks, so the table of contents gets page numbers. The PDF here already has them.
- Check the declaration's statement about AI-assisted development against your college's rules.
- The literature survey (Chapter 2) is not a systematic review. Verify the commercial-tool descriptions before quoting them.

## Honesty notes

- Numbers are labelled MEASURED (with date) or NOT MEASURED. The only real-data result is the n = 1 clip 01 trial.
- The clip 01 export reviewed by the assistant is described as withdrawn, never as human-reviewed (CLAUDE.md §11 c2).
- Screenshots are from 2026-10-12 and show MOCK output.

## Regenerating

The scripts need `docx`, `pptxgenjs`, `@mermaid-js/mermaid-cli@11.4.2`, `react-icons`, `react`, `react-dom` and `sharp` (npm), plus LibreOffice for the PDF. `report.js <workdir> <out.docx>` and `deck.js <workdir> <out.pptx>` expect `<workdir>/uml/*.png` (rendered from `docs/uml/*.md` and `source/er_core.mmd`), `<workdir>/shots/` (cropped screenshots) and `<workdir>/timing_chart.png` (from `chart.js`).

For the 5-chapter report, edit `REPORT_CONTENT_5CHAPTER.md` (the single source of truth) and regenerate:

```
npm install --prefix /tmp/hl-docx docx@9.15.0
NODE_PATH=/tmp/hl-docx/node_modules node source/report_from_md.js \
  REPORT_CONTENT_5CHAPTER.md HyperLocalize_Report_5Chapter.docx
```

Only the screenshots are embedded automatically. The UML figures (Mermaid sources in `docs/uml/README.md`) must be rendered and inserted by hand: paste each block into mermaid.live and export PNG, then replace the corresponding `**Figure 3.x**` caption area. There is no PDF of the 5-chapter report yet (LibreOffice is not installed on the development laptop).
