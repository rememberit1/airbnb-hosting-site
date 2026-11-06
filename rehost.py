"""Re-host an already-rendered preview at its SAME page URL with fresh (versioned) KV keys.
Usage: python3 hosting/rehost.py <slug> [<slug> ...]   (uses previews/<slug>.mp4 and .png)
Writes hosting/pending_<slug>.txt (run each with Cloudflare execute "$file:..."), then regenerates deploy.js (run last)."""
import json, os, subprocess, sys, glob
HO = "/workspace/airbnb/hosting"; PV = "/workspace/airbnb/previews"
sh = lambda *a, **k: subprocess.run(a, check=True, **k)
vj = f"{HO}/versions.json"; V = json.load(open(vj)) if os.path.exists(vj) else {}
T = json.load(open(f"{HO}/previews.json"))
for slug in sys.argv[1:]:
    assert slug in T, slug
    out = f"{PV}/{slug}.mp4"
    sh("ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-maxrate", "2500k", "-bufsize", "5000k",
       "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", f"{HO}/{slug}.web.mp4")
    sh("ffmpeg", "-v", "error", "-y", "-i", out[:-4] + ".png", "-vf", "scale=1280:-2", "-q:v", "3", out[:-4] + ".jpg")
    V[slug] = V.get(slug, 1) + 1; key = f"{slug}@{V[slug]}"
    for f in glob.glob(f"{HO}/up_{key}_*.js"): os.remove(f)
    sh("python3", "make_kv_chunks.py", key, f"{slug}.web.mp4", cwd=HO)
    with open(f"{HO}/up_p_{key}.js", "w") as fh: sh("python3", "make_kv_upload.py", f"poster:{key}", out[:-4] + ".jpg", "image/jpeg", cwd=HO, stdout=fh)
    pend = sorted(glob.glob(f"{HO}/up_{key}_*.js"), key=lambda s: int(s.rsplit("_", 1)[1][:-3])) + [f"{HO}/up_p_{key}.js"]
    open(f"{HO}/pending_{slug}.txt", "w").write("\n".join(pend + [f"{HO}/deploy.js"]) + "\n")
    print(slug, "->", key, len(pend), "files")
json.dump(V, open(vj, "w"), indent=1)
sh("python3", "make_deploy.py", cwd=HO); print("deploy.js regenerated; run it LAST")
