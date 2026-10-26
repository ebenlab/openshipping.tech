// Serves Next.js RSC payloads for client-side navigation in the Mintlify export.
// A request with an `RSC: 1` header or an `_rsc` query parameter gets
// `<path>/index.txt` as text/x-component; everything else is a plain static asset.
export async function onRequest({ request, env, next }: any): Promise<Response> {
  const url = new URL(request.url);
  const isRsc = request.headers.get("RSC") === "1" || url.searchParams.has("_rsc");
  if (!isRsc) {
    const res = await next();
    if ((res.headers.get("Content-Type") || "").startsWith("text/html")) {
      const out = new Response(res.body, res);
      out.headers.set("Cache-Control", "no-cache");
      out.headers.append("Vary", "RSC");
      return out;
    }
    return res;
  }
  const path = url.pathname.replace(/\/+$/, "");
  const asset = await env.ASSETS.fetch(new URL(`${path}/index.txt`, url.origin));
  if (!asset.ok) return next();
  return new Response(asset.body, {
    status: 200,
    headers: { "Content-Type": "text/x-component", "Cache-Control": "no-cache", Vary: "RSC" },
  });
}
