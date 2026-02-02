/* -----------------------------
 * 系统设置页面逻辑
 * ----------------------------- */
// 模拟设置数据（基于你提供的表结构）
const fallbackSettings = [
    {
        id: 1,
        key: 'bot_name',
        value: 'Chobits',
        description: '机器人名称',
        status: 'normal',
        created_time: '2023-01-15 10:35:22',
        updated_time: '2023-12-01 14:22:45',
        deleted_time: null
    },
    {
        id: 2,
        key: 'admin_qq',
        value: '123456789',
        description: '管理员QQ号',
        status: 'normal',
        created_time: '2023-01-15 10:36:15',
        updated_time: '2023-11-20 09:18:33',
        deleted_time: null
    },
    {
        id: 3,
        key: 'auto_reply',
        value: 'true',
        description: '是否启用自动回复功能',
        status: 'normal',
        created_time: '2023-02-10 08:25:44',
        updated_time: '2023-12-10 11:42:18',
        deleted_time: null
    },
    {
        id: 4,
        key: 'max_users',
        value: '1000',
        description: '最大用户数量限制',
        status: 'normal',
        created_time: '2023-02-10 08:26:30',
        updated_time: '2023-10-28 16:37:52',
        deleted_time: null
    },
    {
        id: 5,
        key: 'log_level',
        value: 'info',
        description: '日志级别 (debug/info/warn/error)',
        status: 'normal',
        created_time: '2023-03-01 12:15:27',
        updated_time: '2023-09-14 08:55:19',
        deleted_time: null
    },
    {
        id: 6,
        key: 'backup_interval',
        value: '86400',
        description: '备份间隔时间（秒），默认24小时',
        status: 'disable',
        created_time: '2023-04-18 21:35:11',
        updated_time: '2023-12-15 13:28:44',
        deleted_time: null
    },
    {
        id: 7,
        key: 'api_timeout',
        value: '30',
        description: 'API请求超时时间（秒）',
        status: 'normal',
        created_time: '2023-05-28 14:50:38',
        updated_time: '2023-11-30 17:12:05',
        deleted_time: null
    },
    {
        id: 8,
        key: 'maintenance_mode',
        value: 'false',
        description: '维护模式开关',
        status: 'normal',
        created_time: '2023-05-28 14:51:22',
        updated_time: '2023-08-22 10:44:37',
        deleted_time: null
    },
    {
        id: 9,
        key: 'cache_ttl',
        value: '3600',
        description: '缓存过期时间（秒）',
        status: 'normal',
        created_time: '2023-06-15 09:30:45',
        updated_time: '2023-12-05 15:20:18',
        deleted_time: null
    },
    {
        id: 10,
        key: 'webhook_url',
        value: 'https://example.com/webhook',
        description: 'Webhook回调地址',
        status: 'disable',
        created_time: '2023-07-22 16:45:33',
        updated_time: '2023-11-18 12:33:27',
        deleted_time: null
    }
];

let settingsData = [...fallbackSettings];
let filteredSettings = [...settingsData];
let currentPage = 1;
const settingsPerPage = 5;

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '--';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 渲染设置表格
function renderSettingsTable() {
    const startIndex = (currentPage - 1) * settingsPerPage;
    const endIndex = startIndex + settingsPerPage;
    const paginatedSettings = filteredSettings.slice(startIndex, endIndex);

    const tbody = document.getElementById('settingsTableBody');
    tbody.innerHTML = '';

    paginatedSettings.forEach(setting => {
        const row = document.createElement('tr');

        // 状态标签
        const statusClass = setting.status === 'normal' ? 'status-normal' : 'status-disable';
        const statusText = setting.status === 'normal' ? '正常' : '已禁用';

        row.innerHTML = `
                    <td>${setting.id}</td>
                    <td><strong>${setting.key}</strong></td>
                    <td class="value-cell">${setting.value || '--'}</td>
                    <td class="description-cell">${setting.description || '--'}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td class="muted">${formatDate(setting.created_time)}</td>
                    <td class="muted">${formatDate(setting.updated_time)}</td>
                    <td>
                        <button class="action-btn btn-edit" onclick="editSetting(${setting.id})">编辑</button>
                        <button class="action-btn ${setting.status === 'normal' ? 'btn-disable' : 'btn-normal'}"
                                onclick="toggleSettingStatus(${setting.id})">
                            ${setting.status === 'normal' ? '禁用' : '启用'}
                        </button>
                        <button class="action-btn btn-delete" onclick="deleteSetting(${setting.id})">删除</button>
                    </td>
                `;
        tbody.appendChild(row);
    });

    // 更新总设置数
    document.getElementById('totalCount').textContent = filteredSettings.length;
}

// 渲染分页
function renderPagination() {
    const totalPages = Math.ceil(filteredSettings.length / settingsPerPage);
    const paginationDiv = document.getElementById('pagination');
    paginationDiv.innerHTML = '';

    if (totalPages <= 1) return;

    // 上一页
    if (currentPage > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.className = 'page-btn';
        prevBtn.textContent = '‹';
        prevBtn.onclick = () => {
            currentPage--;
            renderSettingsTable();
            renderPagination();
        };
        paginationDiv.appendChild(prevBtn);
    }

    // 页码按钮
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => {
            currentPage = i;
            renderSettingsTable();
            renderPagination();
        };
        paginationDiv.appendChild(pageBtn);
    }

    // 下一页
    if (currentPage < totalPages) {
        const nextBtn = document.createElement('button');
        nextBtn.className = 'page-btn';
        nextBtn.textContent = '›';
        nextBtn.onclick = () => {
            currentPage++;
            renderSettingsTable();
            renderPagination();
        };
        paginationDiv.appendChild(nextBtn);
    }
}

// 筛选设置
function filterSettings() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;

    filteredSettings = settingsData.filter(setting => {
        const matchesSearch = setting.id.toString().includes(searchValue) ||
            setting.key.toLowerCase().includes(searchValue) ||
            (setting.description && setting.description.toLowerCase().includes(searchValue)) ||
            (setting.value && setting.value.toLowerCase().includes(searchValue));
        const matchesStatus = statusFilter === '' || setting.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    currentPage = 1;
    renderSettingsTable();
    renderPagination();
}

// 切换设置状态
function toggleSettingStatus(settingId) {
    const setting = settingsData.find(s => s.id === settingId);
    if (setting) {
        setting.status = setting.status === 'normal' ? 'disable' : 'normal';
        setting.updated_time = new Date().toISOString().slice(0, 19).replace('T', ' ');
        filterSettings(); // 重新应用筛选
        alert(`设置 "${setting.key}" 已${setting.status === 'normal' ? '启用' : '禁用'}`);
    }
}

// 删除设置
function deleteSetting(settingId) {
    if (confirm('确定要删除此设置吗？此操作不可恢复。')) {
        const settingIndex = settingsData.findIndex(s => s.id === settingId);
        if (settingIndex !== -1) {
            const settingKey = settingsData[settingIndex].key;
            settingsData.splice(settingIndex, 1);
            filterSettings(); // 重新应用筛选
            alert(`设置 "${settingKey}" 删除成功`);
        }
    }
}

// 添加设置
function addSetting() {
    const key = prompt('请输入设置键名:');
    if (key && key.trim()) {
        const value = prompt('请输入设置值:') || '';
        const description = prompt('请输入设置描述（可选）:') || '';
        const newSetting = {
            id: settingsData.length ? Math.max(...settingsData.map(s => s.id)) + 1 : 1,
            key: key.trim(),
            value: value.trim(),
            description: description.trim(),
            status: 'normal',
            created_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            updated_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            deleted_time: null
        };
        settingsData.push(newSetting);
        filterSettings();
        alert('设置添加成功');
    } else if (key !== null) {
        alert('设置键名不能为空');
    }
}

// 编辑设置
function editSetting(settingId) {
    const setting = settingsData.find(s => s.id === settingId);
    if (setting) {
        const newKey = prompt('编辑设置键名:', setting.key);
        if (newKey === null) return; // 用户取消
        if (!newKey.trim()) {
            alert('设置键名不能为空');
            return;
        }
        const newValue = prompt('编辑设置值:', setting.value || '');
        const newDescription = prompt('编辑设置描述:', setting.description || '');
        setting.key = newKey.trim();
        setting.value = newValue ? newValue.trim() : '';
        setting.description = newDescription ? newDescription.trim() : '';
        setting.updated_time = new Date().toISOString().slice(0, 19).replace('T', ' ');
        filterSettings();
        alert('设置更新成功');
    }
}

async function loadSettings(apiUrl = '/chobits/settings') {
    try {
        const res = await fetch(apiUrl);
        const data = await res.json();
        if (data.status === 'success' && data.data && Array.isArray(data.data.items)) {
            settingsData = [...data.data.items];
        } else {
            settingsData = [...fallbackSettings];
        }
    } catch (err) {
        console.error('设置数据加载失败:', err);
        settingsData = [...fallbackSettings];
    }
    filteredSettings = [...settingsData];
    currentPage = 1;
    renderSettingsTable();
    renderPagination();
}

/* -----------------------------
 * 初始化
 * ----------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    initTechBackground('particles', 28);
    setupSidebarNavigation();

    // 初始化设置列表
    loadSettings();
});
