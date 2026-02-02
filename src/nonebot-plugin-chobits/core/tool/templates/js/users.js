/* -----------------------------
 * 用户管理页面逻辑
 * ----------------------------- */
// 模拟用户数据（基于你提供的表结构）
const mockUsers = [
    {
        id: 1,
        qq: '123456789',
        avatar: null,
        register_time: '2023-01-15 10:30:00',
        status: 'normal',
        token: 'abc123def456ghi789jkl012mno345p',
        created_time: '2023-01-15 10:35:22',
        updated_time: '2023-12-01 14:22:45',
        deleted_time: null
    },
    {
        id: 2,
        qq: '987654321',
        avatar: 'https://q1.qlogo.cn/g?b=qq&nk=987654321&s=100',
        register_time: '2022-08-22 15:45:00',
        status: 'ban',
        token: 'xyz987uvw654rst321qpo098nml765k',
        created_time: '2022-08-22 16:00:12',
        updated_time: '2023-11-15 09:18:33',
        deleted_time: null
    },
    {
        id: 3,
        qq: '111222333',
        avatar: 'https://q1.qlogo.cn/g?b=qq&nk=111222333&s=100',
        register_time: '2023-05-10 08:20:00',
        status: 'normal',
        token: 'mno345pqr678stu901vwx234yz567ab',
        created_time: '2023-05-10 08:25:44',
        updated_time: '2023-12-10 11:42:18',
        deleted_time: null
    },
    {
        id: 4,
        qq: '444555666',
        avatar: null,
        register_time: '2023-03-05 19:15:00',
        status: 'normal',
        token: 'cde890fgh123ijk456lmn789opq012r',
        created_time: '2023-03-05 19:20:33',
        updated_time: '2023-10-28 16:37:52',
        deleted_time: null
    },
    {
        id: 5,
        qq: '777888999',
        avatar: 'https://q1.qlogo.cn/g?b=qq&nk=777888999&s=100',
        register_time: '2022-12-01 12:10:00',
        status: 'ban',
        token: 'stu345vwx678yz901abc234def567g',
        created_time: '2022-12-01 12:15:27',
        updated_time: '2023-09-14 08:55:19',
        deleted_time: null
    },
    {
        id: 6,
        qq: '123123123',
        avatar: null,
        register_time: '2023-07-18 21:30:00',
        status: 'normal',
        token: 'hij890klm123nop456qrs789tuv012w',
        created_time: '2023-07-18 21:35:11',
        updated_time: '2023-12-15 13:28:44',
        deleted_time: null
    },
    {
        id: 7,
        qq: '456456456',
        avatar: 'https://q1.qlogo.cn/g?b=qq&nk=456456456&s=100',
        register_time: '2023-02-28 14:45:00',
        status: 'normal',
        token: 'xyz345abc678def901ghi234jkl567m',
        created_time: '2023-02-28 14:50:38',
        updated_time: '2023-11-30 17:12:05',
        deleted_time: null
    },
    {
        id: 8,
        qq: '789789789',
        avatar: null,
        register_time: '2022-11-11 09:20:00',
        status: 'ban',
        token: 'nop890qrs123tuv456wxy789zab012c',
        created_time: '2022-11-11 09:25:19',
        updated_time: '2023-08-22 10:44:37',
        deleted_time: null
    }
];

let filteredUsers = [...mockUsers];
let currentPage = 1;
const usersPerPage = 5;

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

// 获取QQ号首字母作为默认头像
function getInitials(qq) {
    return qq.charAt(0).toUpperCase();
}

// 渲染用户表格
function renderUsersTable() {
    const startIndex = (currentPage - 1) * usersPerPage;
    const endIndex = startIndex + usersPerPage;
    const paginatedUsers = filteredUsers.slice(startIndex, endIndex);

    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = '';

    paginatedUsers.forEach(user => {
        const row = document.createElement('tr');

        // 头像处理
        let avatarHTML;
        if (user.avatar) {
            avatarHTML = `<img src="${user.avatar}" alt="Avatar" class="avatar">`;
        } else {
            avatarHTML = `<div class="avatar default-avatar">${getInitials(user.qq)}</div>`;
        }

        // 状态标签
        const statusClass = user.status === 'normal' ? 'status-normal' : 'status-ban';
        const statusText = user.status === 'normal' ? '正常' : '已封禁';

        row.innerHTML = `
                    <td>${user.id}</td>
                    <td>${avatarHTML}</td>
                    <td>${user.qq}</td>
                    <td class="muted">${formatDate(user.register_time)}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td class="muted">${formatDate(user.created_time)}</td>
                    <td class="muted">${formatDate(user.updated_time)}</td>
                    <td>
                        <button class="action-btn ${user.status === 'normal' ? 'btn-ban' : 'btn-normal'}"
                                onclick="toggleUserStatus(${user.id})">
                            ${user.status === 'normal' ? '封禁' : '解封'}
                        </button>
                        <button class="action-btn btn-delete" onclick="deleteUser(${user.id})">删除</button>
                    </td>
                `;
        tbody.appendChild(row);
    });

    // 更新总用户数
    document.getElementById('totalCount').textContent = filteredUsers.length;
}

// 渲染分页
function renderPagination() {
    const totalPages = Math.ceil(filteredUsers.length / usersPerPage);
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
            renderUsersTable();
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
            renderUsersTable();
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
            renderUsersTable();
            renderPagination();
        };
        paginationDiv.appendChild(nextBtn);
    }
}

// 筛选用户
function filterUsers() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;

    filteredUsers = mockUsers.filter(user => {
        const matchesSearch = user.id.toString().includes(searchValue) ||
            user.qq.toLowerCase().includes(searchValue);
        const matchesStatus = statusFilter === '' || user.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    currentPage = 1;
    renderUsersTable();
    renderPagination();
}

// 切换用户状态
function toggleUserStatus(userId) {
    const user = mockUsers.find(u => u.id === userId);
    if (user) {
        user.status = user.status === 'normal' ? 'ban' : 'normal';
        user.updated_time = new Date().toISOString().slice(0, 19).replace('T', ' ');
        filterUsers(); // 重新应用筛选
        alert(`用户 ${user.qq} 已${user.status === 'normal' ? '解封' : '封禁'}`);
    }
}

// 删除用户
function deleteUser(userId) {
    if (confirm('确定要删除此用户吗？此操作不可恢复。')) {
        const userIndex = mockUsers.findIndex(u => u.id === userId);
        if (userIndex !== -1) {
            mockUsers.splice(userIndex, 1);
            filterUsers(); // 重新应用筛选
            alert('用户删除成功');
        }
    }
}

// 添加用户
function addUser() {
    const qq = prompt('请输入QQ号:');
    if (qq && /^\d+$/.test(qq)) {
        const newUser = {
            id: Math.max(...mockUsers.map(u => u.id)) + 1,
            qq: qq,
            avatar: null,
            register_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            status: 'normal',
            token: Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15),
            created_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            updated_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            deleted_time: null
        };
        mockUsers.push(newUser);
        filterUsers();
        alert('用户添加成功');
    } else if (qq) {
        alert('QQ号必须为数字');
    }
}

/* -----------------------------
 * 初始化
 * ----------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    initTechBackground('particles', 28);
    setupSidebarNavigation();

    // 初始化用户列表
    renderUsersTable();
    renderPagination();
});
