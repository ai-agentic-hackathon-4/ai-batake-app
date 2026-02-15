/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        // Note: The following paths are handled by Next.js API Routes (not proxied):
        //   - /api/diary/generate-manual  (SSE streaming proxy with long timeout)
        //   - /api/diary/auto-generate    (Cloud Scheduler proxy with 30min timeout)
        // All other /api/* requests are proxied to FastAPI backend
        return [
            {
                source: '/api/:path*',
                destination: 'http://127.0.0.1:8081/api/:path*',
            },
        ]
    },
}

export default nextConfig
