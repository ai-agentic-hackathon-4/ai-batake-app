/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        // Note: /api/diary/generate-manual is handled by Next.js API Route (app/api/diary/generate-manual/route.ts)
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
