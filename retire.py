"""Take preview pages down (they 404) and write a KV cleanup script.
Usage: python3 hosting/retire.py <slug> [...] [--keep-kv]
- moves slug(s) from previews.json to previews_retired.json, drops them from versions.json, regenerates deploy.js
- writes hosting/del_<slug>.js (Cloudflare execute) that deletes video:/meta:/poster: keys for slug and slug@N
Run: deploy.js FIRST (page goes 404), then del_<slug>.js (unless --keep-kv)."""
import json, os, subprocess, sys
HO = "/workspace/airbnb/hosting"; NS = "e01348c8ded545bfb67f3257b7f6103d"
slugs = [a for a in sys.argv[1:] if not a.startswith("--")]
T = json.load(open(f"{HO}/previews.json")); R = json.load(open(f"{HO}/previews_retired.json")) if os.path.exists(f"{HO}/previews_retired.json") else {}
V = json.load(open(f"{HO}/versions.json")) if os.path.exists(f"{HO}/versions.json") else {}
for s in slugs:
    if s in T: R[s] = T.pop(s)
    V.pop(s, None)
json.dump(T, open(f"{HO}/previews.json", "w"), indent=1, ensure_ascii=False)
json.dump(R, open(f"{HO}/previews_retired.json", "w"), indent=1, ensure_ascii=False)
json.dump(V, open(f"{HO}/versions.json", "w"), indent=1)
subprocess.run(["python3", "make_deploy.py"], cwd=HO, check=True)
if "--keep-kv" not in sys.argv:
    for s in slugs:
        js = """async () => {
  const slug = %s, ns = '%s', base = `/accounts/${accountId}/storage/kv/namespaces/${ns}`;
  const names = [];
  for (const pre of ['video:', 'meta:', 'poster:']) {
    let cursor;
    do {
      const r = await cloudflare.request({ method: 'GET', path: `${base}/keys`, query: { prefix: pre + slug, limit: 1000, cursor } });
      for (const k of r.result || []) { const rest = k.name.slice((pre + slug).length); if (rest === '' || rest[0] === ':' || rest[0] === '@') names.push(k.name); }
      cursor = r.result_info?.cursor;
    } while (cursor);
  }
  if (!names.length) return { deleted: 0 };
  let r = await cloudflare.request({ method: 'POST', path: `${base}/bulk/delete`, body: names });
  if (!r.success) r = await cloudflare.request({ method: 'DELETE', path: `${base}/bulk`, body: names });
  return { ok: r.success, errors: r.errors, deleted: names.length, names };
}""" % (json.dumps(s), NS)
        open(f"{HO}/del_{s}.js", "w").write(js); print("wrote", f"{HO}/del_{s}.js")
print("live:", list(T))
