const menuItems = [
    {key: 'home', label: '首页', icon: '🏠', href: '/chobits/page?name=home'},
    {key: 'monitor', label: '系统监控', icon: '📊', href: '/chobits/page?name=monitor'},
    {key: 'settings', label: '系统设置', icon: '⚙️', href: '/chobits/page?name=settings'},
    {key: 'users', label: '用户管理', icon: '👥', href: '/chobits/page?name=users'},
    {key: 'roles', label: '角色管理', icon: '🎭', href: '/chobits/page?name=roles'},
    {key: 'functions', label: '命令管理', icon: '💬', href: '/chobits/page?name=functions'},
    {key: 'files', label: '文件管理', icon: '📁'},
    {key: 'tools', label: '工具箱', icon: '🔧'},
    {key: 'logs', label: '日志查看', icon: '📋'},
    {key: 'logout', label: '退出登录', icon: '🚪'}
];

function renderMenu() {
    const navMenu = document.getElementById('navMenu');
    if (!navMenu) return;

    const currentKey = document.body.dataset.page;
    navMenu.innerHTML = '';

    const fragment = document.createDocumentFragment();

    menuItems.forEach(item => {
        const navItem = document.createElement('li');
        navItem.className = 'nav-item';
        if (item.key === currentKey) {
            navItem.classList.add('active');
        }
        if (item.href) {
            navItem.dataset.href = item.href;
            navItem.setAttribute('role', 'link');
            navItem.setAttribute('tabindex', '0');
            navItem.addEventListener('click', () => {
                window.location.href = item.href;
            });
            navItem.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    window.location.href = item.href;
                }
            });
        }

        const iconSpan = document.createElement('span');
        iconSpan.textContent = item.icon;

        const labelSpan = document.createElement('span');
        labelSpan.textContent = item.label;

        navItem.append(iconSpan, labelSpan);
        fragment.appendChild(navItem);
    });

    navMenu.appendChild(fragment);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderMenu);
} else {
    renderMenu();
}
