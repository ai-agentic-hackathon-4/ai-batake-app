import { NextRequest } from 'next/server';

export const runtime = 'nodejs'; // Use Node.js runtime for streaming
export const dynamic = 'force-dynamic'; // Disable caching

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const date = searchParams.get('date');

    if (!date) {
        return new Response(JSON.stringify({ detail: 'Date parameter is required' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
        });
    }

    // Construct backend URL
    const backendUrl = `http://127.0.0.1:8081/api/diary/generate-manual?date=${encodeURIComponent(date)}`;

    try {
        // Fetch from FastAPI backend
        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: {
                'Accept': 'text/event-stream',
            },
        });

        if (!response.ok) {
            const errorText = await response.text();
            return new Response(errorText, {
                status: response.status,
                headers: { 'Content-Type': 'application/json' },
            });
        }

        // CRITICAL: Return Response immediately with the stream
        // This prevents Next.js from buffering the entire response
        return new Response(response.body, {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache, no-transform',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no', // Disable buffering in Nginx
            },
        });
    } catch (error) {
        console.error('Streaming proxy error:', error);
        return new Response(
            JSON.stringify({ detail: 'Failed to connect to backend' }),
            {
                status: 500,
                headers: { 'Content-Type': 'application/json' },
            }
        );
    }
}
