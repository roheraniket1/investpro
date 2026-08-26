export async function onRequest(context) {
  const url = new URL(context.request.url);
  const backendHost = "minutes-borders-gone-delegation.trycloudflare.com";
  
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/') || url.pathname === '/health') {
    const targetUrl = new URL(context.request.url);
    targetUrl.hostname = backendHost;
    targetUrl.protocol = "https:";
    targetUrl.port = "";
    
    const upgradeHeader = context.request.headers.get("Upgrade");
    if (upgradeHeader === "websocket") {
      return fetch(targetUrl.toString(), context.request);
    }
    
    return fetch(new Request(targetUrl.toString(), context.request));
  }
  
  return context.next();
}
