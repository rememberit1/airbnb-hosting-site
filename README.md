# Airbnb hosting tour preview toolkit

## Overview

Toolkit that hosts **watermarked video walkthrough previews** for Airbnb / short-term rental listings on a Cloudflare Pages project (`vista-previews`) backed by Workers KV. Prospective hosts can open a shareable `/p/<slug>/` page with an autoplaying muted tour video.

## Purpose

Give hosts a private, noindex preview link for a 3D/video tour of their property without uploading huge files to email. Videos are chunked into KV; the Pages `_worker.js` reassembles them with HTTP range support.

## Features

- Preview HTML pages at `/p/<slug>/` (title + `<video>` + poster)
- Streaming MP4 at `/v/<slug>.mp4` with `Range` / 206 support
- JPEG posters at `/poster/<slug>.jpg`
- Per-slug version map so re-uploads bust KV edge cache (`versions.json`)
- `robots.txt` disallows crawlers; pages send `x-robots-tag: noindex`
- Python helpers to build deploy payloads and KV chunk uploads:
  - `make_deploy.py` / `deploy.js` — publish `_worker.js` to Pages
  - `make_kv_chunks.py` / `make_kv_upload.py` — upload video chunks + meta
  - `rehost.py` / `retire.py` — rehost or retire a tour
  - `worker_src.js` — readable source for the Pages worker

Large generated `up_*.js` KV upload blobs are **not** in this repo (they are rebuildable artifacts).

## Tech stack

- Cloudflare Pages (project worker) + Workers KV
- Vanilla JS worker (`worker_src.js`)
- Small Python scripts that emit Cloudflare API call payloads

## Run / deploy

1. Put tour video bytes into KV as `meta:<key>`, `video:<key>:<i>`, `poster:<key>` (see comments in `worker_src.js`).
2. Update title / version maps as needed.
3. Generate and run the deploy script (`python3 make_deploy.py` → execute `deploy.js` via your Cloudflare tooling).

Local preview of the worker requires Wrangler + a KV namespace binding named `VIDEOS`. Do not commit API tokens.

## Notes

Preview URLs are meant for private sharing with hosts, not public SEO.
