import { NextRequest } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 1800; // 30 minutes

export async function POST(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const key = searchParams.get('key') || '';

    // Construct backend URL
    const backendUrl = `http://127.0.0.1:8081/api/diary/auto-generate?key=${encodeURIComponent(key)}`;

    try {
        // Proxy to FastAPI backend with a long timeout
        // AbortController to handle 30-minute timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1800_000); // 30 minutes

        const response = await fetch(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        const body = await response.text();

        return new Response(body, {
            status: response.status,
            headers: { 'Content-Type': 'application/json' },
        });
    } catch (error) {
        console.error('Auto-generate diary proxy error:', error);

        const message = error instanceof Error && error.name === 'AbortError'
            ? 'Request timed out (30 minutes)'
            : 'Failed to connect to backend';

        return new Response(
            JSON.stringify({ detail: message }),
            {
                status: 504,
                headers: { 'Content-Type': 'application/json' },
            }
        );
    }
}
