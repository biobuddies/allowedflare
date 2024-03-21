export interface Env {}

export default {
    async fetch(proxyRequest: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
        const originUrl = new URL(proxyRequest.url)
        const domain = originUrl.hostname.split('.').slice(-2).join('.')
        const [, prefix, subdomain, originPath] = originUrl.pathname.match(/(\/[^/]+\/)([^/]+)(.*)/)
        originUrl.hostname = `${subdomain}.${domain}`
        originUrl.pathname = originPath
        const originRequest = new Request(originUrl.toString(), proxyRequest)
        try {
            const originResponse = await fetch(originRequest)
            console.log(`${originRequest.method} ${originRequest.url} st=${originResponse.status}`)
            const proxyResponse = new Response(originResponse.body, originResponse)
            const location = originResponse.headers.get('Location')
            if (location) {
                proxyResponse.headers.set('Location', `${prefix}${subdomain}${location}`)
            }
            return proxyResponse
        } catch (e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500 })
        }
    },
}
