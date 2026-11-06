# Usage: make_kv_upload.py KEY FILE CONTENT_TYPE > upload.js  (run via Cloudflare MCP execute with code "$file:...")
import sys,base64
key,fn,ct=sys.argv[1:4]
b=base64.b64encode(open(fn,'rb').read()).decode()
NS="e01348c8ded545bfb67f3257b7f6103d"
print(f"""async () => {{
  const b64 = "{b}";
  const bin = atob(b64); const u8 = new Uint8Array(bin.length); for (let i=0;i<bin.length;i++) u8[i]=bin.charCodeAt(i);
  const r = await cloudflare.request({{ method:'PUT', path:`/accounts/${{accountId}}/storage/kv/namespaces/{NS}/values/{key}`, body:u8, contentType:'{ct}', rawBody:true }});
  return {{ok:r.success, errors:r.errors, bytes:u8.length}};
}}""")
