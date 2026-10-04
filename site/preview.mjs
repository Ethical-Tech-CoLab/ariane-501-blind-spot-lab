import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "dist");
const base = "/ariane-501-blind-spot-lab";
const types = { ".html": "text/html", ".css": "text/css", ".mjs": "text/javascript", ".svg": "image/svg+xml", ".json": "application/json", ".csv": "text/csv", ".md": "text/plain" };
const server = createServer(async (request, response) => {
  let pathname;
  try {
    pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
  } catch (error) {
    if (!(error instanceof URIError || error instanceof TypeError)) throw error;
    response.writeHead(400).end("Malformed URL");
    return;
  }
  if (pathname === base) {
    response.writeHead(302, { Location: `${base}/` }).end();
    return;
  }
  if (!pathname.startsWith(`${base}/`)) {
    response.writeHead(404).end(`Preview lives at ${base}/`);
    return;
  }
  const relative = pathname.slice(base.length + 1);
  const file = path.resolve(root, relative || "index.html");
  if (path.relative(root, file).startsWith("..") || path.isAbsolute(path.relative(root, file))) {
    response.writeHead(403).end("Outside preview directory");
    return;
  }
  try {
    const content = await readFile(file);
    response.writeHead(200, { "Content-Type": `${types[path.extname(file)] ?? "application/octet-stream"}; charset=utf-8`, "Cache-Control": "no-store" }).end(content);
  } catch (error) {
    if (error.code !== "ENOENT" && error.code !== "EISDIR") {
      console.error(error);
      response.writeHead(500).end("Preview read failed; see server log");
      return;
    }
    response.writeHead(404).end("Not found. Run npm run build first.");
  }
});
server.listen(4173, "127.0.0.1", () => {
  console.log(`Static preview: http://127.0.0.1:4173${base}/`);
});
