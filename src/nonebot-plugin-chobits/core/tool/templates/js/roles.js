/* -----------------------------
 * 角色管理页面逻辑
 * ----------------------------- */
// 模拟角色数据
const fallbackRoles = [
    {
        id: 1,
        name: '超级管理员',
        permissions: 'user.*, role.*, command.*, setting.*, file.*, log.*',
        status: 'normal',
        created_time: '2023-01-15 10:35:22',
        updated_time: '2023-12-01 14:22:45',
        deleted_time: null
    },
    {
        id: 2,
        name: '管理员',
        permissions: 'user.view, user.edit, command.*, setting.view, log.view',
        status: 'normal',
        created_time: '2023-01-15 10:36:15',
        updated_time: '2023-11-20 09:18:33',
        deleted_time: null
    },
    {
        id: 3,
        name: '审核员',
        permissions: 'user.view, command.view, log.*',
        status: 'normal',
        created_time: '2023-02-10 08:25:44',
        updated_time: '2023-12-10 11:42:18',
        deleted_time: null
    },
    {
        id: 4,
        name: '普通用户',
        permissions: 'command.view, log.view',
        status: 'normal',
        created_time: '2023-02-10 08:26:30',
        updated_time: '2023-10-28 16:37:52',
        deleted_time: null
    },
    {
        id: 5,
        name: '访客',
        permissions: 'command.view',
        status: 'disable',
        created_time: '2023-03-01 12:15:27',
        updated_time: '2023-09-14 08:55:19',
        deleted_time: null
    },
    {
        id: 6,
        name: '开发者',
        permissions: 'user.*, role.*, command.*, setting.*, file.*, log.*, system.*',
        status: 'normal',
        created_time: '2023-04-18 21:35:11',
        updated_time: '2023-12-15 13:28:44',
        deleted_time: null
    },
    {
        id: 7,
        name: '安全审计员',
        permissions: 'user.view, role.view, command.view, log.*',
        status: 'normal',
        created_time: '2023-05-28 14:50:38',
        updated_time: '2023-11-30 17:12:05',
        deleted_time: null
    },
    {
        id: 8,
        name: '测试员',
        permissions: 'command.*, setting.view, log.view',
        status: 'disable',
        created_time: '2023-05-28 14:51:22',
        updated_time: '2023-08-22 10:44:37',
        deleted_time: null
    }
];

let rolesData = [...fallbackRoles];
let filteredRoles = [...rolesData];
let currentPage = 1;
const rolesPerPage = 5;

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

// 渲染角色表格
function renderRolesTable() {
    const startIndex = (currentPage - 1) * rolesPerPage;
    const endIndex = startIndex + rolesPerPage;
    const paginatedRoles = filteredRoles.slice(startIndex, endIndex);

    const tbody = document.getElementById('rolesTableBody');
    tbody.innerHTML = '';

    paginatedRoles.forEach(role => {
        const row = document.createElement('tr');

        // 状态标签
        const statusClass = role.status === 'normal' ? 'status-normal' : 'status-disable';
        const statusText = role.status === 'normal' ? '正常' : '已禁用';

        row.innerHTML = `
                    <td>${role.id}</td>
                    <td><strong>${role.name}</strong></td>
                    <td class="permissions-cell">${role.permissions || '--'}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td class="muted">${formatDate(role.created_time)}</td>
                    <td class="muted">${formatDate(role.updated_time)}</td>
                    <td>
                        <button class="action-btn btn-edit" onclick="editRole(${role.id})">编辑</button>
                        <button class="action-btn ${role.status === 'normal' ? 'btn-disable' : 'btn-normal'}"
                                onclick="toggleRoleStatus(${role.id})">
                            ${role.status === 'normal' ? '禁用' : '启用'}
                        </button>
                        <button class="action-btn btn-delete" onclick="deleteRole(${role.id})">删除</button>
                    </td>
                `;
        tbody.appendChild(row);
    });

    // 更新总角色数
    document.getElementById('totalCount').textContent = filteredRoles.length;
}

// 渲染分页
function renderPagination() {
    const totalPages = Math.ceil(filteredRoles.length / rolesPerPage);
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
            renderRolesTable();
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
            renderRolesTable();
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
            renderRolesTable();
            renderPagination();
        };
        paginationDiv.appendChild(nextBtn);
    }
}

// 筛选角色
function filterRoles() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;

    filteredRoles = rolesData.filter(role => {
        const matchesSearch = role.id.toString().includes(searchValue) ||
            role.name.toLowerCase().includes(searchValue) ||
            (role.permissions && role.permissions.toLowerCase().includes(searchValue));
        const matchesStatus = statusFilter === '' || role.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    currentPage = 1;
    renderRolesTable();
    renderPagination();
}

// 切换角色状态
function toggleRoleStatus(roleId) {
    const role = rolesData.find(r => r.id === roleId);
    if (role) {
        role.status = role.status === 'normal' ? 'disable' : 'normal';
        role.updated_time = new Date().toISOString().slice(0, 19).replace('T', ' ');
        filterRoles(); // 重新应用筛选
        alert(`角色 "${role.name}" 已${role.status === 'normal' ? '启用' : '禁用'}`);
    }
}

// 删除角色
function deleteRole(roleId) {
    if (confirm('确定要删除此角色吗？此操作不可恢复。')) {
        const roleIndex = rolesData.findIndex(r => r.id === roleId);
        if (roleIndex !== -1) {
            const roleName = rolesData[roleIndex].name;
            rolesData.splice(roleIndex, 1);
            filterRoles(); // 重新应用筛选
            alert(`角色 "${roleName}" 删除成功`);
        }
    }
}

// 添加角色
function addRole() {
    const name = prompt('请输入角色名称:');
    if (name && name.trim()) {
        const permissions = prompt('请输入权限列表（用逗号分隔）:') || '';
        const newRole = {
            id: rolesData.length ? Math.max(...rolesData.map(r => r.id)) + 1 : 1,
            name: name.trim(),
            permissions: permissions.trim(),
            status: 'normal',
            created_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            updated_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            deleted_time: null
        };
        rolesData.push(newRole);
        filterRoles();
        alert('角色添加成功');
    } else if (name !== null) {
        alert('角色名称不能为空');
    }
}

// 编辑角色
function editRole(roleId) {
    const role = rolesData.find(r => r.id === roleId);
    if (role) {
        const newName = prompt('编辑角色名称:', role.name);
        if (newName === null) return; // 用户取消
        if (!newName.trim()) {
            alert('角色名称不能为空');
            return;
        }
        const newPermissions = prompt('编辑权限列表:', role.permissions || '');
        role.name = newName.trim();
        role.permissions = newPermissions ? newPermissions.trim() : '';
        role.updated_time = new Date().toISOString().slice(0, 19).replace('T', ' ');
        filterRoles();
        alert('角色更新成功');
    }
}

async function loadRoles(apiUrl = '/chobits/roles') {
    try {
        const res = await fetch(apiUrl);
        const data = await res.json();
        if (data.status === 'success' && data.data && Array.isArray(data.data.items)) {
            rolesData = [...data.data.items];
        } else {
            rolesData = [...fallbackRoles];
        }
    } catch (err) {
        console.error('角色数据加载失败:', err);
        rolesData = [...fallbackRoles];
    }
    filteredRoles = [...rolesData];
    currentPage = 1;
    renderRolesTable();
    renderPagination();
}

/* -----------------------------
 * 初始化
 * ----------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    initTechBackground('particles', 28);
    setupSidebarNavigation();

    // 初始化角色列表
    loadRoles();
});
