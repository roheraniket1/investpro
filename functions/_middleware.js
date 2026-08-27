export async function onRequest(context) {
  const url = new URL(context.request.url);
  const primaryHost = "investpro-riyy.onrender.com";
  
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/') || url.pathname === '/health') {
    const isWs = context.request.headers.get("Upgrade") === "websocket";
    const targetUrl = new URL(context.request.url);
    targetUrl.hostname = primaryHost;
    targetUrl.protocol = "https:";
    targetUrl.port = "";
    
    const newHeaders = new Headers(context.request.headers);
    newHeaders.delete("cf-ray");
    newHeaders.delete("cf-connecting-ip");
    newHeaders.delete("cf-visitor");
    newHeaders.delete("cf-ipcountry");
    newHeaders.delete("x-forwarded-proto");
    newHeaders.delete("x-real-ip");
    
    let bodyBuffer = null;
    if (!['GET', 'HEAD'].includes(context.request.method) && !isWs) {
      try {
        bodyBuffer = await context.request.arrayBuffer();
      } catch (e) {}
    }
    
    let lastError = null;
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const reqInit = {
          method: context.request.method,
          headers: newHeaders,
          redirect: "follow"
        };
        if (bodyBuffer) {
          reqInit.body = bodyBuffer;
        }
        
        const resp = await fetch(targetUrl.toString(), reqInit);
        if (resp.status !== 502 && resp.status !== 503) {
          return resp;
        }
      } catch (err) {
        lastError = err;
      }
    }
    
    return new Response(JSON.stringify({ 
      error: "Server warming up. Please wait 3 seconds and retry.",
      detail: String(lastError || "Backend unreachable")
    }), {
      status: 502,
      headers: { "Content-Type": "application/json" }
    });
  }
  
  return context.next();
}


