/* -----------------------------
 * 监控页面逻辑（模拟数据）
 * ----------------------------- */
const state = {
    cpuSeries: Array.from({length: 60}, () => 10 + Math.random() * 20),
    netInSeries: Array.from({length: 60}, () => 5 + Math.random() * 10),
    netOutSeries: Array.from({length: 60}, () => 3 + Math.random() * 8)
};

function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
}

function fmtPct(v) {
    return `${v.toFixed(1)}%`;
}

function badgeByPct(pct) {
    if (pct >= 90) return {cls: 'err', text: 'CRITICAL'};
    if (pct >= 75) return {cls: 'warn', text: 'WARNING'};
    return {cls: '', text: 'NORMAL'};
}

function setBadge(el, pct) {
    const b = badgeByPct(pct);
    el.className = `badge ${b.cls}`.trim();
    el.textContent = b.text;
}

function updateOverallBadge(cpu, mem, disk) {
    const maxv = Math.max(cpu, mem, disk);
    const badge = document.getElementById('overallBadge');
    if (maxv >= 90) {
        badge.className = 'badge err';
        badge.textContent = 'CRITICAL';
        return;
    }
    if (maxv >= 75) {
        badge.className = 'badge warn';
        badge.textContent = 'WARNING';
        return;
    }
    badge.className = 'badge ok';
    badge.textContent = 'OK';
}

function nowStr() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function genNextValue(prev, volatility = 6, floor = 1, ceil = 98) {
    const drift = (Math.random() - 0.5) * volatility;
    return clamp(prev + drift, floor, ceil);
}

function updateSeries() {
    state.cpuSeries.push(genNextValue(state.cpuSeries[state.cpuSeries.length - 1], 9, 2, 98));
    state.cpuSeries.shift();
    state.netInSeries.push(genNextValue(state.netInSeries[state.netInSeries.length - 1], 6, 0.5, 80));
    state.netInSeries.shift();
    state.netOutSeries.push(genNextValue(state.netOutSeries[state.netOutSeries.length - 1], 6, 0.5, 80));
    state.netOutSeries.shift();
}

function buildSparklineSVG(series, opts = {}) {
    const w = 1000, h = 260;
    const padding = 18;
    const max = Math.max(...series, 1);
    const min = Math.min(...series, 0);
    const xStep = (w - padding * 2) / (series.length - 1 || 1);
    const yMap = (v) => {
        if (max === min) return h / 2;
        const t = (v - min) / (max - min);
        return padding + (1 - t) * (h - padding * 2);
    };
    let d = '';
    series.forEach((v, i) => {
        const x = padding + i * xStep;
        const y = yMap(v);
        d += (i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
    });
    const area = `${d} L ${padding + (series.length - 1) * xStep} ${h - padding} L ${padding} ${h - padding} Z`;
    const gridY = [0.25, 0.5, 0.75].map(t => padding + t * (h - padding * 2));
    const gridLines = gridY.map(y => `<line class="gridline" x1="${padding}" y1="${y}" x2="${w - padding}" y2="${y}" />`).join('');
    return `
                <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
                    ${gridLines}
                    <path class="area" d="${area}"></path>
                    <path class="line" d="${d}"></path>
                </svg>
            `;
}

function renderCharts() {
    document.getElementById('cpuChart').innerHTML = buildSparklineSVG(state.cpuSeries);
    const w = 1000, h = 260, padding = 18;
    const all = state.netInSeries.concat(state.netOutSeries);
    const max = Math.max(...all, 1);
    const min = Math.min(...all, 0);
    const xStep = (w - padding * 2) / (state.netInSeries.length - 1 || 1);
    const yMap = (v) => {
        if (max === min) return h / 2;
        const t = (v - min) / (max - min);
        return padding + (1 - t) * (h - padding * 2);
    };

    function pathFor(series) {
        let d = '';
        series.forEach((v, i) => {
            const x = padding + i * xStep;
            const y = yMap(v);
            d += (i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
        });
        return d;
    }

    const gridY = [0.25, 0.5, 0.75].map(t => padding + t * (h - padding * 2));
    const gridLines = gridY.map(y => `<line class="gridline" x1="${padding}" y1="${y}" x2="${w - padding}" y2="${y}" />`).join('');
    const netSvg = `
                <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
                    ${gridLines}
                    <path d="${pathFor(state.netInSeries)}" class="line"></path>
                    <path d="${pathFor(state.netOutSeries)}" style="fill:none;stroke:rgba(0,200,220,0.45);stroke-width:2"></path>
                </svg>
            `;
    document.getElementById('netChart').innerHTML = netSvg;
}

function renderTop() {
    const cpu = state.cpuSeries[state.cpuSeries.length - 1];
    const mem = clamp(35 + (Math.random() * 35), 10, 95);
    const disk = clamp(50 + (Math.random() * 40), 20, 98);
    const cores = 8;
    const memTotalGB = 32;
    const memUsedGB = (memTotalGB * mem / 100);
    const diskTotalGB = 200;
    const diskUsedGB = (diskTotalGB * disk / 100);
    document.getElementById('lastUpdated').textContent = nowStr();
    document.getElementById('cpuValue').textContent = fmtPct(cpu);
    document.getElementById('cpuBar').style.width = `${cpu.toFixed(1)}%`;
    document.getElementById('cpuAvg').textContent = fmtPct((state.cpuSeries.slice(-10).reduce((a, b) => a + b, 0) / 10));
    document.getElementById('cpuCores').textContent = `${cores}`;
    document.getElementById('memValue').textContent = fmtPct(mem);
    document.getElementById('memBar').style.width = `${mem.toFixed(1)}%`;
    document.getElementById('memUsed').textContent = `${memUsedGB.toFixed(1)} GB`;
    document.getElementById('memTotal').textContent = `${memTotalGB} GB`;
    document.getElementById('diskValue').textContent = fmtPct(disk);
    document.getElementById('diskBar').style.width = `${disk.toFixed(1)}%`;
    document.getElementById('diskUsed').textContent = `${diskUsedGB.toFixed(0)} GB`;
    document.getElementById('diskTotal').textContent = `${diskTotalGB} GB`;
    setBadge(document.getElementById('cpuBadge'), cpu);
    setBadge(document.getElementById('memBadge'), mem);
    setBadge(document.getElementById('diskBadge'), disk);
    updateOverallBadge(cpu, mem, disk);
    const load = (cpu / 100 * (cores / 2)).toFixed(2);
    document.getElementById('loadLabel').textContent = `load: ${load}`;
    const inNow = state.netInSeries[state.netInSeries.length - 1];
    const outNow = state.netOutSeries[state.netOutSeries.length - 1];
    document.getElementById('netLabel').textContent = `in: ${inNow.toFixed(1)} MB/s · out: ${outNow.toFixed(1)} MB/s`;
}

function renderTables() {
    const procs = [
        {pid: 1842, name: "chobits-api", cpu: clamp(6 + Math.random() * 18, 0.3, 45), mem: clamp(3 + Math.random() * 10, 0.2, 30), user: "root"},
        {pid: 2211, name: "postgres", cpu: clamp(2 + Math.random() * 10, 0.3, 35), mem: clamp(6 + Math.random() * 15, 0.2, 45), user: "postgres"},
        {pid: 987, name: "redis-server", cpu: clamp(1 + Math.random() * 6, 0.2, 18), mem: clamp(1 + Math.random() * 6, 0.2, 12), user: "redis"},
        {pid: 3021, name: "nginx", cpu: clamp(0.5 + Math.random() * 3.5, 0.1, 10), mem: clamp(0.8 + Math.random() * 2.2, 0.1, 6), user: "www-data"},
        {pid: 4112, name: "node-exporter", cpu: clamp(0.2 + Math.random() * 1.2, 0.1, 6), mem: clamp(0.2 + Math.random() * 0.8, 0.1, 4), user: "nobody"}
    ].sort((a, b) => b.cpu - a.cpu);
    const procTbody = document.getElementById('procTbody');
    procTbody.innerHTML = procs.map(p => `
                <tr>
                    <td>${p.pid}</td>
                    <td>${p.name}</td>
                    <td>${p.cpu.toFixed(1)}%</td>
                    <td>${p.mem.toFixed(1)}%</td>
                    <td class="muted">${p.user}</td>
                </tr>
            `).join('');
    const svc = [
        {name: "chobits-api", ok: true, latency: 18 + Math.random() * 30, note: "HTTP 200 /health"},
        {name: "postgres", ok: true, latency: 2 + Math.random() * 6, note: "连接正常"},
        {name: "redis", ok: true, latency: 1 + Math.random() * 4, note: "PONG"},
        {name: "prometheus", ok: Math.random() > 0.08, latency: 25 + Math.random() * 60, note: "抓取正常"},
        {name: "grafana", ok: Math.random() > 0.10, latency: 30 + Math.random() * 80, note: "登录可用"}
    ];
    const svcTbody = document.getElementById('svcTbody');
    svcTbody.innerHTML = svc.map(s => {
        const status = s.ok ? `<span class="badge ok">RUNNING</span>` : `<span class="badge err">DOWN</span>`;
        const note = s.ok ? s.note : '健康检查失败';
        return `
                    <tr>
                        <td>${s.name}</td>
                        <td>${status}</td>
                        <td>${s.latency.toFixed(0)} ms</td>
                        <td class="muted">${note}</td>
                    </tr>
                `;
    }).join('');
}

function renderAlerts() {
    const n = 3 + Math.floor(Math.random() * 3);
    const list = [];
    for (let i = 0; i < n; i++) {
        const r = Math.random();
        if (r > 0.78) {
            list.push({icon: '⛔', title: '服务不可用：prometheus 健康检查失败', time: '刚刚'});
        } else if (r > 0.5) {
            list.push({icon: '⚠️', title: '磁盘使用率上升，建议清理日志/缓存', time: '3 分钟前'});
        } else {
            list.push({icon: 'ℹ️', title: '配置热更新完成：监控采样间隔已应用', time: '10 分钟前'});
        }
    }
    const wrap = document.getElementById('alerts');
    wrap.innerHTML = list.map(a => `
                <div class="alert">
                    <div class="icon">${a.icon}</div>
                    <div class="text">
                        <div class="title">${a.title}</div>
                        <div class="time">${a.time}</div>
                    </div>
                </div>
            `).join('');
}

function tick() {
    updateSeries();
    renderCharts();
    renderTop();
    renderTables();
    renderAlerts();
}

/* -----------------------------
 * 初始化
 * ----------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    initTechBackground('particles', 28);
    setupSidebarNavigation();
    // 首次渲染
    tick();
    // 定时刷新（每3秒）
    setInterval(tick, 3000);
});
