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
    "methods.html", "research.html", "results.html", "sources.html"]);
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
    "Tavily", "No independent human scientific validation", "not a generated"]) {
    assert.ok(html.includes(phrase), phrase);
  }
  assert.doesNotMatch(html, /\$\d/);
});
