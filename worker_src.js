// Pages _worker.js for vista-previews.pages.dev. KV binding VIDEOS holds:
//   meta:<key> = {"size","chunk","n","type"} ; video:<key>:<i> = chunk bytes ; poster:<key> = jpeg
//   <key> = slug, or slug@<ver> when VERS[slug] is set (re-renders use NEW keys, so KV edge cache never serves stale chunks)
const KEY = slug => VERS[slug] ? `${slug}@${VERS[slug]}` : slug;
const Q = slug => VERS[slug] ? `?v=${VERS[slug]}` : "";
const esc = s => s.replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function page(slug, title) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Walkthrough preview: ${esc(title)}</title>
<meta property="og:title" content="Walkthrough preview: ${esc(title)}"><meta property="og:image" content="/poster/${slug}.jpg${Q(slug)}">
<style>body{margin:0;background:#111;color:#eee;font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.w{max-width:1100px;margin:0 auto;padding:20px 16px}h1{font-size:1.3rem;margin:.2em 0 .6em}video{width:100%;border-radius:10px;background:#000}
p{color:#bbb;font-size:14px}</style></head><body><div class="w">
<h1>Walkthrough preview: ${esc(title)}</h1>
<video controls playsinline autoplay muted loop preload="metadata" poster="/poster/${slug}.jpg${Q(slug)}"><source src="/v/${slug}.mp4${Q(slug)}" type="video/mp4"></video>
<p>Watermarked preview.</p>
</div></body></html>`;
}
async function video(env, slug, request) {
  const meta = await env.VIDEOS.get("meta:" + KEY(slug), "json");
  if (!meta) return new Response("Not found", { status: 404 });
  const size = meta.size, CH = meta.chunk;
  let start = 0, end = size - 1, status = 200;
  const range = request.headers.get("range");
  if (range) {
    const m = /bytes=(\d*)-(\d*)/.exec(range);
    if (m) {
      if (m[1] === "" && m[2] !== "") { start = Math.max(0, size - +m[2]); }
      else { start = +m[1]; if (m[2] !== "") end = Math.min(+m[2], size - 1); }
      if (start > end || start >= size) return new Response(null, { status: 416, headers: { "content-range": `bytes */${size}` } });
      status = 206;
    }
  }
  const h = { "content-type": "video/mp4", "accept-ranges": "bytes", "content-length": String(end - start + 1), "cache-control": "public, max-age=86400" };
  if (status === 206) h["content-range"] = `bytes ${start}-${end}/${size}`;
  if (request.method === "HEAD") return new Response(null, { status, headers: h });
  const { readable, writable } = new FixedLengthStream(end - start + 1);
  (async () => {
    const w = writable.getWriter();
    try {
      for (let i = Math.floor(start / CH); i <= Math.floor(end / CH); i++) {
        const buf = new Uint8Array(await env.VIDEOS.get(`video:${KEY(slug)}:${i}`, { type: "arrayBuffer", cacheTtl: 86400 }));
        const s = Math.max(start - i * CH, 0), e = Math.min(end - i * CH + 1, buf.length);
        await w.write(buf.subarray(s, e));
      }
      await w.close();
    } catch (err) { await w.abort(err); }
  })();
  return new Response(readable, { status, headers: h });
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url), p = url.pathname;
    if (request.method !== "GET" && request.method !== "HEAD") return new Response("Method not allowed", { status: 405 });
    let m;
    if ((m = /^\/p\/([a-z0-9-]+)\/?$/.exec(p)) && TITLES[m[1]]) return new Response(page(m[1], TITLES[m[1]]), { headers: { "content-type": "text/html; charset=utf-8", "x-robots-tag": "noindex", "cache-control": "no-cache" } });
    if ((m = /^\/v\/([a-z0-9-]+)\.mp4$/.exec(p)) && TITLES[m[1]]) return video(env, m[1], request);
    if ((m = /^\/poster\/([a-z0-9-]+)\.jpg$/.exec(p)) && TITLES[m[1]]) {
      const b = await env.VIDEOS.get("poster:" + KEY(m[1]), { type: "arrayBuffer" });
      return b ? new Response(b, { headers: { "content-type": "image/jpeg", "cache-control": "public, max-age=86400" } }) : new Response("Not found", { status: 404 });
    }
    if (p === "/robots.txt") return new Response("User-agent: *\nDisallow: /\n");
    return new Response("Not found", { status: 404 });
  },
};
