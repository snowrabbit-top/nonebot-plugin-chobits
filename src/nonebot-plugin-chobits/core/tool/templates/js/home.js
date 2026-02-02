// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initTechBackground();
    setupSidebarNavigation();

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
            // 这里可以添加实际的刷新逻辑
            alert('刷新系统状态数据...');
        });
    }
});
