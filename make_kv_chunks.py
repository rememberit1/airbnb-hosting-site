# Usage: make_kv_chunks.py SLUG FILE -> writes up_<slug>_<i>.js (one per 2.5MB chunk) + prints meta JSON
# Each JS file is run with Cloudflare MCP execute, code "$file:/workspace/airbnb/hosting/up_<slug>_<i>.js" (MCP body limit is 4 MB).
import sys,base64,json
slug,fn=sys.argv[1:3]
NS="e01348c8ded545bfb67f3257b7f6103d"; CH=2_500_000
data=open(fn,'rb').read(); n=(len(data)+CH-1)//CH
for i in range(n):
    b=base64.b64encode(data[i*CH:(i+1)*CH]).decode()
    meta = json.dumps({"size":len(data),"chunk":CH,"n":n,"type":"video/mp4"}) if i==n-1 else None
    extra = f"""const m = await cloudflare.request({{ method:'PUT', path:`/accounts/${{accountId}}/storage/kv/namespaces/{NS}/values/meta:{slug}`, body:{json.dumps(meta)}, contentType:'text/plain', rawBody:true }});""" if meta else ""
    open(f"up_{slug}_{i}.js","w").write(f"""async () => {{
  const bin = atob("{b}"); const u8 = new Uint8Array(bin.length); for (let i=0;i<bin.length;i++) u8[i]=bin.charCodeAt(i);
  const r = await cloudflare.request({{ method:'PUT', path:`/accounts/${{accountId}}/storage/kv/namespaces/{NS}/values/video:{slug}:{i}`, body:u8, contentType:'application/octet-stream', rawBody:true }});
  {extra}
  return {{ok:r.success, errors:r.errors, bytes:u8.length}};
}}""")
print(slug,len(data),n)
