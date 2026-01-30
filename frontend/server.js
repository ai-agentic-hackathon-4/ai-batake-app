const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8080;

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Proxy API requests to the Python backend running on localhost:8081
app.use('/api', createProxyMiddleware({
    target: 'http://127.0.0.1:8081',
    changeOrigin: true,
    proxyTimeout: 1800000, // 30 minutes
    timeout: 1800000,      // 30 minutes
}));

app.listen(PORT, () => {
    console.log(`Frontend server is running on port ${PORT}`);
});
