import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 8080;
const BASE_PATH = process.env.BASE_PATH || '/';

console.log(`Serving on BASE_PATH: ${BASE_PATH}`);

// Serve static files from the 'dist' directory
// Mount static middleware at the BASE_PATH
app.use(BASE_PATH, express.static(path.join(__dirname, 'dist')));

// Proxy API requests to the Python backend
// Mount proxy at BASE_PATH + 'api'
// We use pathRewrite to verify that requests forwarded to python backend are clean (if needed)
// But typically proxy middleware forwards the path as is unless rewritten.
// If backend expects /api/..., we should keep it.
// If the request comes in as /BASE_PATH/api/..., we want backend to receive /api/...
app.use(path.join(BASE_PATH, 'api'), createProxyMiddleware({
    target: 'http://127.0.0.1:8081',
    changeOrigin: true,
    pathRewrite: (path, req) => {
        // Remove BASE_PATH from the beginning of the path so backend gets /api/...
        // path.join might remove trailing slash of BASE_PATH, so be careful.
        // E.g. BASE_PATH=/batake, request=/batake/api/foo
        // We want to forward /api/foo

        // Simple replace first occurrence
        if (BASE_PATH !== '/' && path.startsWith(BASE_PATH)) {
            return path.replace(BASE_PATH, '');
        }
        return path;
    }
}));

// Handle SPA routing: return index.html for any unknown route under BASE_PATH
app.get(path.join(BASE_PATH, '*'), (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Frontend server is running on port ${PORT} with BASE_PATH path ${BASE_PATH}`);
});
