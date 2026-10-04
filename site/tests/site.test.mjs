import test from "node:test";
import assert from "node:assert/strict";
import { readFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Marked } from "marked";

const site = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const root = path.dirname(site);
const out = path.join(site, "dist");
const read = file => readFile(file, "utf8");
const pages = (await readdir(out)).filter(file => file.endsWith(".html"));

test("all required static pages exist with landmarks, navigation, and unique IDs", async () => {
  assert.deepEqual(pages.sort(), ["ai-usage.html", "demo.html", "framework.html", "index.html",
    "mariupol-review.html", "methods.html", "research.html", "results.html", "sources.html"]);
  for (const file of pages) {
    const html = await read(path.join(out, file));
    assert.match(html, /<html lang="en">/);
    assert.equal((html.match(/<main\b/g) ?? []).length, 1);
    assert.match(html, /Skip to content/);
    assert.match(html, /aria-current="page"/);
    assert.match(html, /name="viewport"/);
    assert.doesNotMatch(html, /\{\{[A-Z_]+\}\}/);
    const ids = Array.from(html.matchAll(/\bid="([^"]+)"/g), match => match[1]);
    assert.equal(ids.length, new Set(ids).size, `Duplicate IDs: ${file}`);
    if (file !== "demo.html") assert.doesNotMatch(html, /<script\b/);
  }
});

test("every internal HTML link, download, image, stylesheet, script, and anchor resolves under a Pages subpath", async () => {
  const base = "https://example.test/ariane-501-blind-spot-lab/";
  for (const page of pages) {
    const html = await read(path.join(out, page));
    const urls = Array.from(html.matchAll(/\b(?:href|src)="([^"]+)"/g), match => match[1]);
    for (const url of urls) {
      if (/^(https?:|mailto:)/.test(url)) continue;
      const resolved = new URL(url.replaceAll("&amp;", "&"), base + page);
      assert.ok(resolved.pathname.startsWith("/ariane-501-blind-spot-lab/"), `${page}: escaped Pages subpath: ${url}`);
      const relative = decodeURIComponent(resolved.pathname.replace("/ariane-501-blind-spot-lab/", ""));
      const target = path.join(out, relative || page);
      assert.ok((await stat(target)).isFile(), `${page}: missing ${url}`);
      if (resolved.hash && target.endsWith(".html")) {
        assert.ok((await read(target)).includes(`id="${resolved.hash.slice(1)}"`), `${page}: missing anchor ${url}`);
      }
    }
  }
});

test("full documents, not hand-written summaries, are rendered into the research library", async () => {
  const docs = [
    ["docs", "STUDY.md", "research.html"],
    ["docs", "METHODS.md", "methods.html"],
    ["docs", "FRAMEWORK.md", "framework.html"],
    ["docs", "AI_USAGE.md", "ai-usage.html"],
    ["docs", "MARIUPOL_REVIEW.md", "mariupol-review.html"],
    ["results", "summary.md", "results.html"],
  ];
  for (const [folder, source, page] of docs) {
    const markdown = await read(path.join(root, folder, source));
    const html = await read(path.join(out, page));
    const headings = new Marked().lexer(markdown).filter(token => token.type === "heading");
    assert.equal((html.match(/<h[1-6]\b/g) ?? []).length, headings.length, `${page}: missing source sections`);
    assert.equal(await read(path.join(out, folder, source)), markdown);
  }
});

test("published data is copied byte-for-byte and the overview counts come from it", async () => {
  for (const folder of ["results", "data"]) {
    const files = await readdir(path.join(out, folder));
    for (const file of files) {
      assert.deepEqual(await readFile(path.join(out, folder, file)), await readFile(path.join(root, folder, file)));
    }
  }
  const data = JSON.parse(await read(path.join(root, "results", "study.json")));
  const html = await read(path.join(out, "index.html"));
  assert.ok(html.includes(data.monte_carlo.reduce((sum, row) => sum + row.n, 0).toLocaleString("en-US")));
  for (const row of data.monte_carlo) {
    assert.ok(html.includes(`<td>${row.n.toLocaleString("en-US")}</td><td>${row.navigation_losses.toLocaleString("en-US")}</td><td><strong>${row.detected.toLocaleString("en-US")}</strong></td>`));
  }
});

test("disclosure carries provenance and unknowns without fabricated measurements", async () => {
  const html = await read(path.join(out, "ai-usage.html"));
  for (const phrase of ["Unknown is not zero", "usage-calc", "Copilot SDK in VS Code",
    "Alternative web search", "No independent human scientific validation", "not a generated"]) {
    assert.ok(html.includes(phrase), phrase);
  }
  assert.doesNotMatch(html, /\$\d/);
});

test("prerequisite controls are rendered from the current generated experiment", async () => {
  const { detection_readiness: readiness } = JSON.parse(await read(path.join(root, "results", "study.json")));
  const html = await read(path.join(out, "index.html"));
  assert.ok(html.includes(`${readiness.summary.cases} configurations`));
  for (const row of readiness.ablations) {
    const cells = [
      row.actual_navigation_loss ? "Yes" : "No", row.injected_control_detected ? "Yes" : "No",
      row.campaign_budget.toLocaleString("en-US"), `${(row.campaign_detection_probability * 100).toFixed(6)}%`,
      row.discovery_target_met ? "Yes" : "No", row.replay_case !== null ? "Yes" : "No",
      row.modeled_response_blocks ? "Yes" : "No",
    ];
    assert.ok(html.includes(`<th scope="row">${row.name}</th>${cells.map(value => `<td>${value}</td>`).join("")}`), row.name);
  }
  for (const page of ["research.html", "methods.html", "framework.html", "results.html"]) {
    assert.match(await read(path.join(out, page)), /prerequisite/i);
  }
});

test("companion review preserves its scope, pinned evidence, and downloadable audit", async () => {
  const html = await read(path.join(out, "mariupol-review.html"));
  const audit = JSON.parse(await read(path.join(root, "data", "mariupol-audit.json")));
  assert.match(html, /<title>Mariupol evidence review \| Blind Spot Lab/);
  assert.match(html, /COMPANION REVIEW/);
  assert.match(html, /not operational evacuation advice/);
  assert.match(html, /Research and methods do exist/);
  assert.match(html, /I did not find the specific/);
  assert.ok(html.includes(audit.reviewedRevision));
  assert.match(html, /href="data\/mariupol-audit\.json" download/);
  assert.deepEqual(await readFile(path.join(out, "data", "mariupol-audit.json")),
    await readFile(path.join(root, "data", "mariupol-audit.json")));
  for (const page of ["research.html", "methods.html", "framework.html", "results.html", "sources.html"]) {
    const content = await read(path.join(out, page));
    assert.match(content, /aria-label="Companion reviews"/);
    assert.match(content, /href="mariupol-review.html"/);
  }
  const research = await read(path.join(out, "research.html"));
  assert.match(research, /The 37-Second Blind Spot/);
  assert.doesNotMatch(research, /id="mariupol-does-the-model/);
});
