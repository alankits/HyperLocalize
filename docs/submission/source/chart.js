// Clip 01 timing-fit chart (MEASURED ratios from docs/trials/2026-10-22-clip01-adr0021-trial.md)
const sharp = require("sharp");
const r = [1.78,1.70,1.28,0.98,1.48,0.95,1.17,1.34,1.77,1.38,1.40,2.02,1.22,1.39];
const W = 1600, H = 720, L = 120, R = 150, T = 90, B = 100, ymax = 2.25;
const pw = W - L - R, ph = H - T - B, step = pw / r.length, bw = step * 0.55;
const y = (v) => T + ph - (v / ymax) * ph;
let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" font-family="Arial">
<rect width="100%" height="100%" fill="#FFFFFF"/>
<text x="${L}" y="50" font-size="30" fill="#222">Only 2 of 14 lines fitted their slot (MEASURED, n = 1 clip, tempo cap 1.15×)</text>`;
for (const g of [0, 0.5, 1.5, 2.0]) s += `<line x1="${L}" x2="${L + pw}" y1="${y(g)}" y2="${y(g)}" stroke="#E5E5E5" stroke-width="2"/><text x="${L - 14}" y="${y(g) + 8}" font-size="22" fill="#555" text-anchor="end">${g.toFixed(1)}</text>`;
r.forEach((v, i) => {
  const x = L + i * step + (step - bw) / 2;
  const h = (v / ymax) * ph;
  s += `<path d="M${x},${y(0)} V${y(v) + 8} q0,-8 8,-8 H${x + bw - 8} q8,0 8,8 V${y(0)} Z" fill="#1F6F6B"/>`;
  s += `<text x="${x + bw / 2}" y="${y(0) + 34}" font-size="22" fill="#555" text-anchor="middle">${i + 1}</text>`;
  if (v === 2.02) s += `<text x="${x + bw / 2}" y="${y(v) - 12}" font-size="22" fill="#333" text-anchor="middle">${v.toFixed(2)}×</text>`;
  if (v < 1) s += `<text x="${x + bw / 2}" y="${y(v) + 34}" font-size="20" fill="#FFFFFF" text-anchor="middle">${v.toFixed(2)}×</text>`;
});
s += `<line x1="${L}" x2="${L + pw}" y1="${y(1)}" y2="${y(1)}" stroke="#333" stroke-width="3" stroke-dasharray="12 8"/><text x="${L + pw + 12}" y="${y(1) + 26}" font-size="22" fill="#333">fits (1.0)</text>`;
s += `<line x1="${L}" x2="${L + pw}" y1="${y(1.15)}" y2="${y(1.15)}" stroke="#888" stroke-width="2" stroke-dasharray="4 6"/><text x="${L + pw + 12}" y="${y(1.15) - 8}" font-size="22" fill="#666">+15%</text>`;
s += `<line x1="${L}" x2="${L + pw}" y1="${y(0)}" y2="${y(0)}" stroke="#BBB" stroke-width="2"/>`;
s += `<text x="${L + pw / 2}" y="${H - 25}" font-size="24" fill="#444" text-anchor="middle">Line in clip 01</text>`;
s += `<text transform="translate(40,${T + ph / 2}) rotate(-90)" font-size="24" fill="#444" text-anchor="middle">Speech ÷ slot length</text></svg>`;
sharp(Buffer.from(s)).png().toFile(process.argv[2]).then(() => console.log("ok"));
