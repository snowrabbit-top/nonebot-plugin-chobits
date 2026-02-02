function formatPercent(value) {
    if (typeof value !== 'number' || Number.isNaN(value)) {
        return null;
    }
    return `${value.toFixed(1)}%`;
}

function updateProgress(value, valueEl, barEl, textEl, text) {
    if (value === null || value === undefined) {
        return;
    }
    if (valueEl) {
        valueEl.textContent = formatPercent(value) || valueEl.textContent;
    }
    if (barEl) {
        barEl.style.width = `${value}%`;
    }
    if (textEl && text) {
        textEl.textContent = text;
    }
}

function updateMetrics(metrics) {
    const mapping = [
        {key: 'users', id: 'metricUsers'},
        {key: 'roles', id: 'metricRoles'},
        {key: 'commands', id: 'metricCommands'},
        {key: 'active_today', id: 'metricActive'},
        {key: 'alerts', id: 'metricAlerts'},
        {key: 'tasks', id: 'metricTasks'}
    ];
    mapping.forEach(item => {
        const el = document.getElementById(item.id);
        if (el && metrics && metrics[item.key] !== undefined) {
            el.textContent = metrics[item.key];
        }
    });
}

function updateActivities(activities) {
    const list = document.getElementById('activityList');
    if (!list || !Array.isArray(activities)) {
        return;
    }
    list.innerHTML = '';
    activities.forEach(activity => {
        const item = document.createElement('li');
        item.className = 'activity-item';
        item.innerHTML = `
            <div class="activity-icon">${activity.icon || '📌'}</div>
            <div class="activity-content">
                <div class="activity-text">${activity.text || ''}</div>
                <div class="activity-time">${activity.time || ''}</div>
            </div>
        `;
        list.appendChild(item);
    });
}

async function loadHomeData(apiUrl = '/chobits/home') {
    try {
        const res = await fetch(apiUrl);
        const data = await res.json();
        if (data.status !== 'success') {
            return;
        }
        const payload = data.data || {};
        const status = payload.system_status || {};
        const cpuUsage = status.cpu_usage;
        const memory = status.memory || {};
        const disk = status.disk || {};

        const serverEl = document.getElementById('serverStatusValue');
        if (serverEl) {
            serverEl.textContent = status.server === 'online' ? '在线' : '离线';
        }

        updateProgress(
            cpuUsage,
            document.getElementById('cpuUsageValue'),
            document.getElementById('cpuUsageBar'),
            document.getElementById('cpuUsageText'),
            cpuUsage !== null && cpuUsage !== undefined ? '正常' : ''
        );
        updateProgress(
            memory.percent,
            document.getElementById('memoryUsageValue'),
            document.getElementById('memoryUsageBar'),
            document.getElementById('memoryUsageText'),
            typeof memory.used_gb === 'number' && typeof memory.total_gb === 'number'
                ? `${memory.used_gb}GB/${memory.total_gb}GB`
                : ''
        );
        updateProgress(
            disk.percent,
            document.getElementById('diskUsageValue'),
            document.getElementById('diskUsageBar'),
            document.getElementById('diskUsageText'),
            typeof disk.used_gb === 'number' && typeof disk.total_gb === 'number'
                ? `${disk.used_gb}GB/${disk.total_gb}GB`
                : ''
        );

        updateMetrics(payload.metrics);
        updateActivities(payload.activities);
    } catch (err) {
        console.error('首页数据加载失败:', err);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initTechBackground();
    setupSidebarNavigation();
    loadHomeData();

    // 快捷操作按钮交互
    const quickBtns = document.querySelectorAll('.quick-btn');
    quickBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const action = this.textContent.trim();
            alert(`执行操作: ${action}`);
        });
    });

    // 刷新按钮
    const refreshLink = document.querySelector('.card-header a[href="#"]');
    if (refreshLink) {
        refreshLink.addEventListener('click', function (e) {
            e.preventDefault();
            loadHomeData();
        });
    }
});
