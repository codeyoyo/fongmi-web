/**
 * Node.js Spider Engine - 执行JS爬虫代码
 * 通过 HTTP 通信 (port 19999) 与 Python 交互
 */
const http = require('http');
const https = require('https');
const vm = require('vm');
const crypto = require('crypto');

const PORT = 19999;

function fetchUrl(url, headers = {}) {
    return new Promise((resolve, reject) => {
        const mod = url.startsWith('https') ? https : http;
        const h = Object.assign({ 'User-Agent': 'Dart/2.19 (dart:io)' }, headers);
        let parsed;
        try { parsed = new URL(url); } catch (e) { return reject(e); }
        const req = mod.get({
            hostname: parsed.hostname,
            port: parsed.port || (url.startsWith('https') ? 443 : 80),
            path: parsed.pathname + parsed.search,
            headers: h,
            rejectUnauthorized: false,
        }, (res) => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                return fetchUrl(res.headers.location, headers).then(resolve, reject);
            }
            let data = '';
            res.setEncoding('utf-8');
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        req.setTimeout(30000, () => { req.destroy(); reject(new Error('timeout')); });
        req.on('error', reject);
    });
}

function transformCode(code) {
    return code
        .replace(/\/\/.*$/gm, '')
        .replace(/^[\s]*export\s+(default\s+)?(async\s+)?(function|class|const|let|var)\s+/gm, '$2$3 ')
        .replace(/^[\s]*export\s*\{[^}]*\};?\s*$/gm, '')
        .replace(/^[\s]*import\s+.*?['"][^'"]+['"];?\s*$/gm, '');
}

const spiderStore = {};

const server = http.createServer(async (req, res) => {
    if (req.method !== 'POST') return res.end('{}');
    let body = '';
    req.on('data', c => body += c);
    req.on('end', async () => {
        try {
            const msg = JSON.parse(body);
            const { action, payload } = msg;

            if (action === 'load') {
                const { apiUrl, key } = payload;
                let jsCode;
                try { jsCode = await fetchUrl(apiUrl); }
                catch (e) { return res.end(JSON.stringify({ ok: false, error: e.message })); }
                try {
                    const code = transformCode(jsCode);
                    // Build sandbox with all globals the spider needs
                    const log = [];
                    const sandbox = {
                        console: { log: (...a) => log.push(a.join(' ')), error: (...a) => log.push('ERR:' + a.join(' ')) },
                        self: null, window: null, globalThis: null,
                        setTimeout, Promise, Buffer, URL, RegExp, Error,
                        JSON, Math, Date, Array, Object, String, Number, Boolean,
                        Set, Map, parseInt, parseFloat, isNaN, isFinite,
                        encodeURI, decodeURI, encodeURIComponent, decodeURIComponent,
                        fetch: async (u, opts) => {
                            try { const t = await fetchUrl(u, opts?.headers); return { ok: true, text: t }; }
                            catch (e) { return { ok: false, text: e.message }; }
                        },
                        md5: (s) => crypto.createHash('md5').update(String(s)).digest('hex'),
                        atob: (s) => Buffer.from(String(s), 'base64').toString('utf-8'),
                        btoa: (s) => Buffer.from(String(s)).toString('base64'),
                        require: () => ({}),
                    };
                    sandbox.self = sandbox;
                    sandbox.window = sandbox;
                    sandbox.globalThis = sandbox;
                    const ctx = vm.createContext(sandbox);
                    vm.runInContext(code, ctx, { timeout: 30000 });
                    // After running code, expose all top-level functions
                    const spider = {};
                    ['init', 'homeContent', 'homeVideoContent', 'categoryContent',
                     'detailContent', 'searchContent', 'playerContent', 'liveContent', 'proxy', 'action'].forEach(name => {
                        const val = sandbox[name];
                        if (typeof val === 'function') spider[name] = val;
                        else if (Array.isArray(val)) spider[name] = val;
                        else if (val !== undefined) spider[name] = val;
                    });
                    spiderStore[key] = { spider, sandbox, log };
                    res.end(JSON.stringify({ ok: true, funcs: Object.keys(spider) }));
                } catch (e) {
                    res.end(JSON.stringify({ ok: false, error: e.message }));
                }
            } else if (action === 'call') {
                const { key, method, args = [] } = payload;
                const entry = spiderStore[key];
                if (!entry) return res.end(JSON.stringify({ ok: false, error: 'loaded' }));
                const fn = entry.spider[method];
                if (typeof fn !== 'function') return res.end(JSON.stringify({ ok: false, error: method + ' not found', available: Object.keys(entry.spider) }));
                try {
                    const r = fn(...args);
                    let out;
                    if (typeof r === 'string') { try { out = JSON.parse(r); } catch (e) { out = r; } }
                    else { out = r; }
                    res.end(JSON.stringify({ ok: true, result: out }));
                } catch (e) {
                    res.end(JSON.stringify({ ok: false, error: e.message }));
                }
            } else if (action === 'destroy') {
                delete spiderStore[payload.key];
                res.end(JSON.stringify({ ok: true }));
            }
        } catch (e) {
            res.end(JSON.stringify({ ok: false, error: e.message }));
        }
    });
});

server.listen(PORT, '127.0.0.1', () => console.log('OK ' + PORT));
