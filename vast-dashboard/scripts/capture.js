#!/usr/bin/env node
/**
 * capture.js — Puppeteer 截图脚本
 * 启动本地 HTTP 服务器，打开仪表盘，对每个图表导出高清 PNG。
 *
 * 用法: node scripts/capture.js
 * 输出: vast-dashboard/exports/*.png
 */

const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const DASHBOARD_DIR = path.resolve(__dirname, '..');
const EXPORT_DIR = path.join(DASHBOARD_DIR, 'exports');

if (!fs.existsSync(EXPORT_DIR)) {
    fs.mkdirSync(EXPORT_DIR, { recursive: true });
}

const CHARTS = [
    { name: '01_circular_bar', selector: '#circular_bar_svg' },
    { name: '02_ring_chart', selector: '#right-ring-div' },
    { name: '03_sankey', selector: '#sankey_svg' },
    { name: '04_map', selector: '#map_div' },
    { name: '05_box_plot', selector: '#box_plot_div' },
    { name: '06_network', selector: '#network_div' },
];

// ── Simple Static Server ──────────────────────────────────────
const mimeTypes = {
    '.html': 'text/html', '.js': 'application/javascript',
    '.css': 'text/css', '.json': 'application/json',
    '.csv': 'text/csv', '.svg': 'image/svg+xml',
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.png': 'image/png', '.geojson': 'application/json',
    '.ttf': 'font/ttf', '.woff': 'font/woff',
};

function startServer() {
    const http = require('http');
    const server = http.createServer((req, res) => {
        let filePath = path.join(DASHBOARD_DIR, req.url.split('?')[0]);
        if (filePath.endsWith('/')) filePath += 'dashboard.html';
        if (!fs.existsSync(filePath)) { res.writeHead(404); res.end('Not found'); return; }
        const ext = path.extname(filePath).toLowerCase();
        res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
        res.end(fs.readFileSync(filePath));
    });
    return new Promise((resolve) => {
        server.listen(8765, () => { console.log('Server: http://localhost:8765'); resolve(server); });
    });
}

// ── Main ──────────────────────────────────────────────────────
async function main() {
    const server = await startServer();

    const browser = await puppeteer.launch({
        headless: 'new',
        executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });

        // 加载页面
        console.log('Loading dashboard...');
        await page.goto('http://localhost:8765/dashboard.html', {
            waitUntil: 'networkidle0',
            timeout: 120000
        });

        // 等待各图表渲染
        console.log('Waiting for D3 charts to render...');
        const selectors = [
            '#circular_bar_svg g', '#ring_svg .legend', '#sankey_svg g',
            '#map_svg image', '#box_plot_svg g', '#network_svg g',
        ];
        for (const sel of selectors) {
            try {
                await page.waitForSelector(sel, { timeout: 60000 });
                console.log(`  ✓ ${sel}`);
            } catch (e) {
                console.log(`  ⚠ timeout: ${sel}`);
            }
        }

        // 等待力模拟完成
        console.log('Waiting for force simulation...');
        await page.evaluate(() => {
            return new Promise((resolve) => {
                let attempts = 0;
                const check = setInterval(() => {
                    const nodes = document.querySelectorAll('.network_nodes');
                    if (nodes.length > 0 && nodes[0].getAttribute('x') &&
                        parseFloat(nodes[0].getAttribute('x')) !== 0) {
                        clearInterval(check); resolve();
                    }
                    if (++attempts > 150) { clearInterval(check); resolve(); }
                }, 200);
            });
        });
        await new Promise(r => setTimeout(r, 4000));

        // 截取各图表
        for (const chart of CHARTS) {
            console.log(`Capturing: ${chart.name}...`);
            try {
                // 桑基图：先展开滚动容器完整截取
                if (chart.name === '03_sankey') {
                    await page.evaluate(() => {
                        const scroll = document.querySelector('.sankey-scroll');
                        if (scroll) {
                            scroll.style.height = 'auto';
                            scroll.style.overflow = 'visible';
                        }
                    });
                    await new Promise(r => setTimeout(r, 500));
                }

                const el = await page.$(chart.selector);
                if (!el) { console.log(`  ⚠ Not found: ${chart.selector}`); continue; }
                const outPath = path.join(EXPORT_DIR, `${chart.name}.png`);
                await el.screenshot({ path: outPath, type: 'png' });
                const stat = fs.statSync(outPath);
                console.log(`  ✓ ${outPath} (${(stat.size/1024).toFixed(0)} KB)`);
            } catch (err) {
                console.log(`  ✗ ${chart.name}: ${err.message}`);
            }
        }

        // 地图特殊状态：未分配车辆
        console.log('Capturing unassigned vehicles...');
        await page.evaluate(() => {
            ['101','104','105','106','107'].forEach(carId => {
                if (typeof selected_cars !== 'undefined' && selected_cars.indexOf(carId) === -1) {
                    selected_cars.push(carId);
                }
                if (typeof updateData !== 'undefined') updateData(carId);
            });
            if (typeof plotGPS !== 'undefined') plotGPS();
        });
        await new Promise(r => setTimeout(r, 2000));

        const mapEl = await page.$('#map_div');
        if (mapEl) {
            const p = path.join(EXPORT_DIR, '07_map_unassigned.png');
            await mapEl.screenshot({ path: p, type: 'png' });
            console.log(`  ✓ ${p}`);
        }

    } finally {
        await browser.close();
        server.close();
    }

    console.log('\n✓ Done. Exports:', EXPORT_DIR);
}

main().catch(err => { console.error('Error:', err); process.exit(1); });
