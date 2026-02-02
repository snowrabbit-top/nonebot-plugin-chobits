/* -----------------------------
 * 命令管理页面逻辑
 * ----------------------------- */
// 模拟命令数据（基于你提供的表结构）
const fallbackFunctions = [
    {
        id: 1,
        name: 'ping',
        description: '测试机器人是否在线，返回pong响应',
        status: 'normal',
        created_time: '2023-01-15 10:35:22',
        updated_time: '2023-12-01 14:22:45',
        deleted_time: null
    },
    {
        id: 2,
        name: 'help',
        description: '显示所有可用命令的帮助信息',
        status: 'normal',
        created_time: '2023-01-15 10:36:15',
        updated_time: '2023-11-20 09:18:33',
        deleted_time: null
    },
    {
        id: 3,
        name: 'ban',
        description: '封禁指定用户，禁止其使用机器人功能',
        status: 'disable',
        created_time: '2023-02-10 08:25:44',
        updated_time: '2023-12-10 11:42:18',
        deleted_time: null
    },
    {
        id: 4,
        name: 'unban',
        description: '解封被封禁的用户',
        status: 'normal',
        created_time: '2023-02-10 08:26:30',
        updated_time: '2023-10-28 16:37:52',
        deleted_time: null
    },
    {
        id: 5,
        name: 'stats',
        description: '显示系统统计信息和用户活跃度',
        status: 'normal',
        created_time: '2023-03-01 12:15:27',
        updated_time: '2023-09-14 08:55:19',
        deleted_time: null
    },
    {
        id: 6,
        name: 'reload',
        description: '重新加载配置文件和命令模块',
        status: 'disable',
        created_time: '2023-04-18 21:35:11',
        updated_time: '2023-12-15 13:28:44',
        deleted_time: null
    },
    {
        id: 7,
        name: 'backup',
        description: '创建系统数据备份',
        status: 'normal',
        created_time: '2023-05-28 14:50:38',
        updated_time: '2023-11-30 17:12:05',
        deleted_time: null
    },
    {
        id: 8,
        name: 'restore',
        description: '从备份恢复系统数据',
        status: 'normal',
        created_time: '2023-05-28 14:51:22',
        updated_time: '2023-08-22 10:44:37',
        deleted_time: null
    },
    {
        id: 9,
        name: 'clear',
        description: '清理缓存和临时文件',
        status: 'normal',
        created_time: '2023-06-15 09:30:45',
        updated_time: '2023-12-05 15:20:18',
        deleted_time: null
    },
    {
        id: 10,
        name: 'update',
        description: '检查并应用系统更新',
        status: 'disable',
        created_time: '2023-07-22 16:45:33',
        updated_time: '2023-11-18 12:33:27',
        deleted_time: null
    }
];

let functionsData = [...fallbackFunctions];
let filteredFunctions = [...functionsData];
let currentPage = 1;
const functionsPerPage = 5;

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

// 渲染命令表格
function renderFunctionsTable() {
    const startIndex = (currentPage - 1) * functionsPerPage;
    const endIndex = startIndex + functionsPerPage;
    const paginatedFunctions = filteredFunctions.slice(startIndex, endIndex);

    const tbody = document.getElementById('functionsTableBody');
    tbody.innerHTML = '';

    paginatedFunctions.forEach(func => {
        const row = document.createElement('tr');

        // 状态标签
        const statusClass = func.status === 'normal' ? 'status-normal' : 'status-disable';
        const statusText = func.status === 'normal' ? '正常' : '已禁用';

        row.innerHTML = `
                    <td>${func.id}</td>
                    <td><strong>${func.name}</strong></td>
                    <td class="description">${func.description || '--'}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td class="muted">${formatDate(func.created_time)}</td>
                    <td class="muted">${formatDate(func.updated_time)}</td>
                    <td>
                        <button class="action-btn btn-edit" onclick="editFunction(${func.id})">编辑</button>
                        <button class="action-btn ${func.status === 'normal' ? 'btn-disable' : 'btn-normal'}"
                                onclick="toggleFunctionStatus(${func.id})">
                            ${func.status === 'normal' ? '禁用' : '启用'}
                        </button>
                        <button class="action-btn btn-delete" onclick="deleteFunction(${func.id})">删除</button>
                    </td>
                `;
        tbody.appendChild(row);
    });

    // 更新总命令数
    document.getElementById('totalCount').textContent = filteredFunctions.length;
}

// 渲染分页
function renderPagination() {
    const totalPages = Math.ceil(filteredFunctions.length / functionsPerPage);
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
            renderFunctionsTable();
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
            renderFunctionsTable();
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
            renderFunctionsTable();
            renderPagination();
        };
        paginationDiv.appendChild(nextBtn);
    }
}

// 筛选命令
function filterFunctions() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;

    filteredFunctions = functionsData.filter(func => {
        const matchesSearch = func.id.toString().includes(searchValue) ||
            func.name.toLowerCase().includes(searchValue) ||
            (func.description && func.description.toLowerCase().includes(searchValue));
        const matchesStatus = statusFilter === '' || func.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    currentPage = 1;
    renderFunctionsTable();
    renderPagination();
}

// 切换命令状态
function toggleFunctionStatus(functionId) {
    const func = functionsData.find(f => f.id === functionId);
    if (func) {
        func.status = func.status === 'normal' ? 'disable' : 'normal';
        func.updated_time = new Date().toISOString().slice(0, 19).replace('T', ' ');
        filterFunctions(); // 重新应用筛选
        alert(`命令 "${func.name}" 已${func.status === 'normal' ? '启用' : '禁用'}`);
    }
}

// 删除命令
function deleteFunction(functionId) {
    if (confirm('确定要删除此命令吗？此操作不可恢复。')) {
        const funcIndex = functionsData.findIndex(f => f.id === functionId);
        if (funcIndex !== -1) {
            const funcName = functionsData[funcIndex].name;
            functionsData.splice(funcIndex, 1);
            filterFunctions(); // 重新应用筛选
            alert(`命令 "${funcName}" 删除成功`);
        }
    }
}

// 添加命令
function addFunction() {
    const name = prompt('请输入命令名称:');
    if (name && name.trim()) {
        const description = prompt('请输入命令描述（可选）:') || '';
        const newFunction = {
            id: functionsData.length ? Math.max(...functionsData.map(f => f.id)) + 1 : 1,
            name: name.trim(),
            description: description.trim(),
            status: 'normal',
            created_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            updated_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            deleted_time: null
        };
        functionsData.push(newFunction);
        filterFunctions();
        alert('命令添加成功');
    } else if (name !== null) {
        alert('命令名称不能为空');
    }
}

// 编辑命令
function editFunction(functionId) {
    const func = functionsData.find(f => f.id === functionId);
    if (func) {
        const newName = prompt('编辑命令名称:', func.name);
        if (newName === null) return; // 用户取消
        if (!newName.trim()) {
            alert('命令名称不能为空');
            return;
        }
        const newDescription = prompt('编辑命令描述:', func.description || '');
        func.name = newName.trim();
        func.description = newDescription ? newDescription.trim() : '';
        func.updated_time = new Date().toISOString().slice(0, 19).replace('T', ' ');
        filterFunctions();
        alert('命令更新成功');
    }
}

async function loadFunctions(apiUrl = '/chobits/functions') {
    try {
        const res = await fetch(apiUrl);
        const data = await res.json();
        if (data.status === 'success' && data.data && Array.isArray(data.data.items)) {
            functionsData = [...data.data.items];
        } else {
            functionsData = [...fallbackFunctions];
        }
    } catch (err) {
        console.error('命令数据加载失败:', err);
        functionsData = [...fallbackFunctions];
    }
    filteredFunctions = [...functionsData];
    currentPage = 1;
    renderFunctionsTable();
    renderPagination();
}

/* -----------------------------
 * 初始化
 * ----------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    initTechBackground('particles', 28);
    setupSidebarNavigation();

    // 初始化命令列表
    loadFunctions();
});
