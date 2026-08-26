import urllib.request
import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('CloudflareSync')

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
SCRIPT_NAME = "app"

def sync_cloudflare_worker(backend_host: str):
    """
    Sync active backend tunnel hostname to the Cloudflare Worker on investpro.workers.dev.
    Provides a 100% permanent, zero-passcode, fixed domain for InvestPro!
    """
    clean_host = backend_host.replace("https://", "").replace("http://", "").split("/")[0].strip()
    if not clean_host:
        return False
        
    logger.info(f"Syncing Cloudflare Worker on investpro.workers.dev to target: {clean_host}")
    
    worker_js = f"""
addEventListener('fetch', event => {{
  event.respondWith(handleRequest(event.request));
}});

async function handleRequest(request) {{
  const targetUrl = new URL(request.url);
  targetUrl.hostname = "{clean_host}";
  targetUrl.protocol = "https:";
  targetUrl.port = "";
  
  const upgradeHeader = request.headers.get("Upgrade");
  if (upgradeHeader === "websocket") {{
    return fetch(targetUrl.toString(), request);
  }}
  
  const newRequest = new Request(targetUrl.toString(), {{
    method: request.method,
    headers: request.headers,
    body: request.body,
    redirect: "follow"
  }});
  
  return fetch(newRequest);
}}
"""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/javascript"
    }
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/workers/scripts/{SCRIPT_NAME}"
    try:
        req = urllib.request.Request(url, data=worker_js.encode('utf-8'), headers=headers, method="PUT")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('success'):
                logger.info(f"🎉 Cloudflare Worker updated! Permanent domain https://{SCRIPT_NAME}.investpro.workers.dev is synchronized.")
                return True
    except Exception as e:
        logger.error(f"Failed to sync Cloudflare Worker: {e}")
        return False

if __name__ == "__main__":
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else "minutes-borders-gone-delegation.trycloudflare.com"
    sync_cloudflare_worker(host)
