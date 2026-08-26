export async function onRequest(context) {
  const url = new URL(context.request.url);
  const primaryHost = "investpro-riyy.onrender.com";
  const fallbackHost = "interesting-peer-curtis-loose.trycloudflare.com";
  
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/') || url.pathname === '/health') {
    const isWs = context.request.headers.get("Upgrade") === "websocket";
    const method = context.request.method;
    const hasBody = !['GET', 'HEAD'].includes(method);
    
    // Read body once as ArrayBuffer so it can be reused safely
    let bodyBuffer = undefined;
    if (hasBody && !isWs) {
      try {
        bodyBuffer = await context.request.arrayBuffer();
      } catch (e) {
        bodyBuffer = undefined;
      }
    }
    
    // Helper to make proxied request
    const proxyTo = async (hostname, timeoutMs = 4000) => {
      const target = new URL(context.request.url);
      target.hostname = hostname;
      target.protocol = "https:";
      target.port = "";
      
      const newHeaders = new Headers(context.request.headers);
      newHeaders.set("Host", hostname);
      newHeaders.delete("cf-ray");
      newHeaders.delete("cf-connecting-ip");
      newHeaders.delete("cf-visitor");
      
      if (isWs) {
        return fetch(target.toString(), {
          method: method,
          headers: newHeaders
        });
      }
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
      
      try {
        const resp = await fetch(target.toString(), {
          method: method,
          headers: newHeaders,
          body: bodyBuffer,
          signal: controller.signal
        });
        clearTimeout(timeoutId);
        return resp;
      } catch (err) {
        clearTimeout(timeoutId);
        throw err;
      }
    };
    
    // 1. Try Primary (Render Cloud 24/7 Backend)
    try {
      const resp = await proxyTo(primaryHost, 35000);
      if (resp && resp.status < 500) {
        return resp;
      }
    } catch (e) {
      // Primary timed out or errored
    }
    
    // 2. Fallback to Active Tunnel (if laptop is on)
    try {
      const resp = await proxyTo(fallbackHost, 8000);
      if (resp && resp.status < 500) {
        return resp;
      }
    } catch (e) {
      return new Response(JSON.stringify({ error: "Cloud backend connecting...", status: "connecting" }), {
        status: 503,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
  
  return context.next();
}
