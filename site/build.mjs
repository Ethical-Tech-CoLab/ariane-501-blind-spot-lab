import { readFile, writeFile, mkdir, copyFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Marked, Renderer } from "marked";

const site = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(site);
const out = path.join(site, "dist");
const repo = "https://github.com/Ethical-Tech-CoLab/ariane-501-blind-spot-lab";
const publicURL = "https://ethical-tech-colab.github.io/ariane-501-blind-spot-lab/";
const title = "The 37-Second Blind Spot: A Million Green Tests, One Missing Assumption";
const read = file => readFile(path.join(root, ...file.split("/")), "utf8");
const escape = text => String(text).replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);
const number = value => value.toLocaleString("en-US");
const study = JSON.parse(await read("results/study.json"));
const catalog = JSON.parse(await read("data/sources.json"));
const assumptions = JSON.parse(await read("data/assumptions.json"));
const docs = [
  { source: "docs/STUDY.md", file: "research.html", label: "Full study", group: "Research" },
  { source: "docs/METHODS.md", file: "methods.html", label: "Methods & limitations", group: "Research" },
  { source: "docs/FRAMEWORK.md", file: "framework.html", label: "BLIND-SPOT framework", group: "Research" },
  { source: "results/summary.md", file: "results.html", label: "Published results", group: "Research" },
  { source: "docs/AI_USAGE.md", file: "ai-usage.html", label: "AI usage disclosure", group: "AI Usage" },
];
const docMap = new Map(docs.map(doc => [doc.source, doc.file]));

function renderMarkdown(markdown, source) {
  const toc = [];
  const ids = new Map();
  const renderer = new Renderer();
  function href(value) {
    if (/^(https?:|mailto:|#)/.test(value)) return value;
    const resolved = new URL(value, `https://local.invalid/${source}`);
    const name = decodeURIComponent(resolved.pathname.slice(1));
    return (docMap.get(name) ?? name) + resolved.hash;
  }
  renderer.heading = function ({ tokens, depth }) {
    const text = this.parser.parseInline(tokens);
    const plain = text.replace(/<[^>]+>/g, "");
    const slug = plain.toLowerCase().replace(/&[^;]+;/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "section";
    const count = ids.get(slug) ?? 0;
    ids.set(slug, count + 1);
    const id = count ? `${slug}-${count}` : slug;
    if (depth === 2) toc.push({ id, text: plain });
    return `<h${depth} id="${id}">${text}</h${depth}>\n`;
  };
  renderer.link = function (token) {
    return `<a href="${escape(href(token.href))}"${token.title ? ` title="${escape(token.title)}"` : ""}>${this.parser.parseInline(token.tokens)}</a>`;
  };
  renderer.image = function (token) {
    return `<img src="${escape(href(token.href))}" alt="${escape(token.text)}" loading="lazy">`;
  };
  renderer.table = function (token) {
    return `<div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable research table">${Renderer.prototype.table.call(this, token)}</div>`;
  };
  const html = new Marked({ renderer }).parse(markdown);
  return { html, toc };
}

function shell(content, current, file, description, pageTitle = title) {
  const navigation = [
    ["Overview", "index.html"], ["Research", "research.html"],
    ["Demo", "demo.html"], ["AI Usage", "ai-usage.html"],
  ];
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="${escape(description)}">
  <meta name="theme-color" content="#0a1020">
  <meta property="og:title" content="${escape(pageTitle)}">
  <meta property="og:description" content="${escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="${publicURL}${file === "index.html" ? "" : file}">
  <link rel="canonical" href="${publicURL}${file === "index.html" ? "" : file}">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="styles.css">
  <title>${escape(pageTitle)} | Ethical Tech CoLab</title>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="masthead"><div class="shell nav">
    <a class="brand" href="index.html" aria-label="Ethical Tech CoLab, Blind Spot Lab home"><span class="brand-mark" aria-hidden="true">E<span>:</span></span><span>Ethical Tech CoLab<small>THE BLIND SPOT LAB</small></span></a>
    <nav aria-label="Main navigation">${navigation.map(([label, link]) => `<a href="${link}"${label === current ? ' aria-current="page"' : ""}>${label}</a>`).join("")}</nav>
    <a class="repository" href="${repo}">GitHub <span aria-hidden="true">&#8599;</span></a>
  </div></header>
  <main id="main">${content}</main>
  <footer><div class="shell footer-grid"><div><a class="brand" href="index.html">Ethical Tech CoLab</a><p>Open research. Explicit assumptions.<br>Evidence before assurance.</p></div><div><a href="sources.html">Sources & provenance</a><a href="ai-usage.html">AI usage disclosure</a><a href="${repo}">Code & reproducibility</a></div><p class="fine">Independent retrospective study. No affiliation with or endorsement by the article author, ESA, CNES, or NIST. Synthetic mechanism model; not flight telemetry, certification, or an empirical AI-discovery study.</p></div></footer>
  ${current === "Demo" ? '<script type="module" src="demo.mjs"></script>' : ""}
</body>
</html>`;
}

function researchLinks(active) {
  return `<p class="eyebrow">RESEARCH LIBRARY</p><nav class="library-nav" aria-label="Research library">${[
    ...docs.filter(doc => doc.group === "Research"),
    { file: "sources.html", label: "Sources & provenance" },
  ].map(doc => `<a href="${doc.file}"${doc.file === active ? ' aria-current="page"' : ""}>${doc.label}</a>`).join("")}</nav>`;
}

function csvTable(csv) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < csv.length; i++) {
    const char = csv[i];
    if (char === '"') {
      if (quoted && csv[i + 1] === '"') { cell += '"'; i++; }
      else quoted = !quoted;
    } else if (!quoted && (char === "," || char === "\n")) {
      row.push(cell.replace(/\r$/, ""));
      cell = "";
      if (char === "\n") { rows.push(row); row = []; }
    } else cell += char;
  }
  if (quoted) throw new Error("Unterminated quote in variable provenance CSV");
  if (cell || row.length) rows.push([...row, cell.replace(/\r$/, "")]);
  const [headers, ...values] = rows;
  if (values.some(row => row.length !== headers.length)) throw new Error("Variable CSV column count mismatch");
  return `<div class="table-scroll" tabindex="0" role="region" aria-label="Full variable provenance table"><table><caption>All variable records. Scroll horizontally for sources, model use, and limitations.</caption><thead><tr>${headers.map(header => `<th scope="col">${escape(header.replaceAll("_", " "))}</th>`).join("")}</tr></thead><tbody>${values.map(row => `<tr>${row.map((value, index) => index === 0 ? `<th scope="row">${escape(value.replaceAll("_", " "))}</th>` : `<td>${value ? escape(value) : "Unavailable"}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

await mkdir(out, { recursive: true });
for (const folder of ["results", "data", "docs"]) await mkdir(path.join(out, folder), { recursive: true });
for (const file of ["styles.css", "model.mjs", "demo.mjs", "favicon.svg"]) {
  await copyFile(path.join(site, file), path.join(out, file));
}
for (const file of [
  "data/sources.json", "data/variables.csv", "data/assumptions.json",
  "results/study.json", "results/summary.md", "results/monte_carlo.csv",
  "results/synthetic_trace.csv", "results/monte_carlo.svg",
  "results/detection_probability.svg", "results/synthetic_trace.svg",
  ...docs.filter(doc => doc.source.startsWith("docs/")).map(doc => doc.source),
]) {
  await copyFile(path.join(root, ...file.split("/")), path.join(out, ...file.split("/")));
}
await writeFile(path.join(out, ".nojekyll"), "");
const total = study.monte_carlo.reduce((sum, row) => sum + row.n, 0);
const expanded = study.monte_carlo.find(row => row.name === "expanded_faithful");
const legacy = study.monte_carlo.find(row => row.name === "million_legacy");
const names = {
  million_legacy: ["Legacy-like support", "The input distribution excludes the failure region."],
  expanded_faithful: ["Expanded support", "The mechanism executes; the safety oracle sees the loss."],
  rare_tail_faithful: ["Rare-tail support", "The trigger exists, but the test budget matters."],
  expanded_idealized_stub: ["Idealized SRI stub", "A nominal-output harness removes the failing path."],
  expanded_packet_oracle: ["Packet-presence oracle", "Diagnostics count as packets. A green result hides navigation loss."],
  expanded_alignment_removed: ["Post-launch alignment removed", "An explicit intervention blocks this modeled chain."],
};
const resultRows = study.monte_carlo.map(row => {
  const [name, meaning] = names[row.name] ?? [row.name, ""];
  return `<tr><th scope="row">${name}<small>${meaning}</small></th><td>${number(row.n)}</td><td>${number(row.navigation_losses)}</td><td><strong>${number(row.detected)}</strong></td></tr>`;
}).join("");
const replacements = {
  TOTAL: number(total),
  EXPANDED: number(expanded.detected),
  LEGACY: number(legacy.n),
  GRID: number(study.coverage.suites.exhaustive.cases),
  RESULT_ROWS: resultRows,
  MODEL_VERSION: escape(study.model_version),
};
let overview = await read("site/overview.html");
overview = overview.replace(/\{\{([A-Z_]+)\}\}/g, (_, key) => {
  if (!(key in replacements)) throw new Error(`Unknown template token ${key}`);
  return replacements[key];
});
await writeFile(path.join(out, "index.html"), shell(overview, "Overview", "index.html",
  "A million passing tests can miss an excluded assumption. Explore Ariane 501 through primary sources, a synthetic mechanism model, and an interactive evaluation lab."));
await writeFile(path.join(out, "demo.html"), shell(await read("site/demo.html"), "Demo", "demo.html",
  "Change the conversion input, lifecycle, barriers, harness, and oracle. Compare modeled failure with apparent evaluation success.", `Interactive demo | ${title}`));

for (const doc of docs) {
  const { html, toc } = renderMarkdown(await read(doc.source), doc.source);
  const content = `<div class="shell document-layout"><aside class="contents">${doc.group === "Research" ? researchLinks(doc.file) : '<p class="eyebrow">PROCESS TRANSPARENCY</p>'}<p class="eyebrow contents-label">ON THIS PAGE</p><nav aria-label="On this page">${toc.map(item => `<a href="#${item.id}">${item.text}</a>`).join("")}</nav><a class="source-link" href="${repo}/blob/main/${doc.source}">View authoritative Markdown &#8599;</a></aside><article class="prose"><div class="document-meta"><span class="badge">OPEN RESEARCH</span><span>4 October 2026</span><a href="${doc.source}" download>Download Markdown</a></div>${html}<div class="notice">Rendered at build time from the repository source. The source document remains authoritative.</div></article></div>`;
  await writeFile(path.join(out, doc.file), shell(content, doc.group, doc.file,
    `${doc.label} for the Ariane 501 Blind Spot Lab. Complete research with sources, methods, and explicit limitations.`, `${doc.label} | ${title}`));
}

const sourceContent = catalog.sources.map(source => `<section class="source-record" id="${source.id.toLowerCase()}"><p class="eyebrow">${source.id} / ${escape(source.evidence_class)}</p><h2><a href="${escape(source.url)}">${escape(source.title)}</a></h2><dl>${Object.entries(source).filter(([key]) => !["id", "title", "url", "evidence_class"].includes(key)).map(([key, value]) => `<dt>${escape(key.replaceAll("_", " "))}</dt><dd>${value === null ? "Unknown / not established" : escape(Array.isArray(value) ? value.join("; ") : value)}</dd>`).join("")}</dl></section>`).join("");
const assumptionContent = assumptions.assumptions.map(item => `<details class="assumption"><summary>${escape(item.id)}: ${escape(item.claim)}</summary><dl>${Object.entries(item).filter(([key]) => !["id", "claim"].includes(key)).map(([key, value]) => `<dt>${escape(key.replaceAll("_", " "))}</dt><dd>${escape(Array.isArray(value) ? value.join(", ") : value)}</dd>`).join("")}</dl></details>`).join("");
const sourcePage = `<div class="shell document-layout"><aside class="contents">${researchLinks("sources.html")}<p class="eyebrow contents-label">ON THIS PAGE</p><nav aria-label="On this page"><a href="#catalog">Source catalog</a><a href="#access">Research access log</a><a href="#variables">Variable provenance</a><a href="#assumptions">Assumption register</a></nav></aside><article class="prose"><p class="eyebrow">THE EVIDENCE TRAIL</p><h1>Sources & provenance</h1><p class="lead">What was read. What was invented. What remains unknown.</p><p>${escape(catalog.method)}. Research date: ${escape(catalog.research_date)}. This page renders the live repository records rather than maintaining a separate source list.</p><h2 id="catalog">Source catalog</h2><a href="data/sources.json">Download source catalog and access log (JSON)</a>${sourceContent}<h2 id="access">Research access log</h2><ul>${catalog.access_log.map(item => `<li><strong>${escape(item.tool ?? item.url)}: ${escape(item.status)}.</strong> ${escape(item.detail)}</li>`).join("")}</ul><h2 id="variables">Variable provenance</h2><p>Documented facts, derived mathematics, synthetic inputs, and unavailable quantities are kept distinct. Empty historical values mean unavailable, not zero. BH values are conversion units, <strong>not speed or telemetry</strong>.</p><a href="data/variables.csv" download>Download full variable register (CSV)</a>${csvTable(await read("data/variables.csv"))}<h2 id="assumptions">Executable assumption register</h2><p>${escape(assumptions.scope)}. Owners below are responsibility roles, not claims of assigned people.</p><p><a href="data/assumptions.json">Download all assumptions (JSON)</a></p>${assumptionContent}</article></div>`;
await writeFile(path.join(out, "sources.html"), shell(sourcePage, "Research", "sources.html",
  "Complete source catalog, access log, variable provenance and falsifiable assumption register.", `Sources & provenance | ${title}`));
console.log(`Built 8 static pages in ${out}; ${number(total)} published opportunities, model ${study.model_version}. No simulation rerun.`);
