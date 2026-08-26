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
    
    const reqInit = {
      method: context.request.method,
      headers: newHeaders,
      redirect: "follow"
    };
    
    if (!['GET', 'HEAD'].includes(context.request.method) && !isWs) {
      reqInit.body = context.request.body;
      reqInit.duplex = "half";
    }
    
    try {
      return await fetch(targetUrl.toString(), reqInit);
    } catch (err) {
      return new Response(JSON.stringify({ error: "Backend connecting...", detail: String(err) }), {
        status: 502,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
  
  return context.next();
}


