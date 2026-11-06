# Builds deploy.js (Pages direct upload of a single _worker.js). Run via Cloudflare MCP execute, code "$file:/workspace/airbnb/hosting/deploy.js"
import json
titles=json.load(open('/workspace/airbnb/hosting/previews.json'))
import os
vers=json.load(open("/workspace/airbnb/hosting/versions.json")) if os.path.exists("/workspace/airbnb/hosting/versions.json") else {}
worker="const TITLES = "+json.dumps(titles)+";\nconst VERS = "+json.dumps(vers)+";\n"+open('/workspace/airbnb/hosting/worker_src.js').read()
js="""async () => {
  const worker = %s;
  const b = 'VISTA' + Date.now();
  const part = (name, ctype, data, filename) => [`--${b}`, `Content-Disposition: form-data; name="${name}"` + (filename ? `; filename="${filename}"` : ''), `Content-Type: ${ctype}`, '', data].join('\\r\\n');
  const body = [part('manifest', 'application/json', '{}'), part('branch', 'text/plain', 'main'),
                part('_worker.js', 'application/javascript+module', worker, '_worker.js'), `--${b}--`, ''].join('\\r\\n');
  const r = await cloudflare.request({ method: 'POST', path: `/accounts/${accountId}/pages/projects/vista-previews/deployments`, body, contentType: `multipart/form-data; boundary=${b}`, rawBody: true });
  return { ok: r.success, errors: r.errors, id: r.result?.id, url: r.result?.url, stage: r.result?.latest_stage };
}""" % json.dumps(worker)
open('/workspace/airbnb/hosting/deploy.js','w').write(js)

# Guard (standing rule): nothing viewer-facing may mention AI.
import re as _re
_dj = open('/workspace/airbnb/hosting/deploy.js').read()
_bad = _re.findall(r"\bAI\b|[Aa]rtificial", _dj)
if _bad: raise SystemExit(f"REFUSING: deploy.js mentions {_bad} (never mention AI to viewers)")
print("AI-mention guard: clean")
