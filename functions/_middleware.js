export async function onRequest(context) {
  const url = new URL(context.request.url);
  const primaryHost = "investpro-riyy.onrender.com";
  const fallbackHost = "interesting-peer-curtis-loose.trycloudflare.com";
  
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/') || url.pathname === '/health') {
    const targetUrl = new URL(context.request.url);
    targetUrl.protocol = "https:";
    targetUrl.port = "";
    
    const upgradeHeader = context.request.headers.get("Upgrade");
    if (upgradeHeader === "websocket") {
      try {
        targetUrl.hostname = primaryHost;
        const resp = await fetch(targetUrl.toString(), context.request);
        if (resp && resp.status < 500) return resp;
      } catch (e) {}
      targetUrl.hostname = fallbackHost;
      return fetch(targetUrl.toString(), context.request);
    }
    
    // HTTP API Request - try Render with 3.5s timeout, then fallback
    try {
      targetUrl.hostname = primaryHost;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3500);
      const reqClone = context.request.clone();
      const hasBody = !['GET', 'HEAD'].includes(context.request.method);
      const bodyData = hasBody ? await reqClone.arrayBuffer() : undefined;
      
      const resp = await fetch(new Request(targetUrl.toString(), {
        method: context.request.method,
        headers: context.request.headers,
        body: bodyData,
        signal: controller.signal
      }));
      clearTimeout(timeoutId);
      if (resp && resp.status < 500) {
        return resp;
      }
    } catch (e) {
      // Primary failed or timed out
    }
    
    // Fallback to active tunnel
    try {
      targetUrl.hostname = fallbackHost;
      const reqClone = context.request.clone();
      const hasBody = !['GET', 'HEAD'].includes(context.request.method);
      const bodyData = hasBody ? await reqClone.arrayBuffer() : undefined;
      return await fetch(new Request(targetUrl.toString(), {
        method: context.request.method,
        headers: context.request.headers,
        body: bodyData
      }));
    } catch (err) {
      return new Response(JSON.stringify({ error: "Backend connecting...", status: "connecting" }), {
        status: 503,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
  
  return context.next();
}
