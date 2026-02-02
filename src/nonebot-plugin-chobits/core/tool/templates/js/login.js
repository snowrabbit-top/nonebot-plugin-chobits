// 登录功能相关脚本
async function login(loginUrl = '/login', redirectUrl = '/domain') {
    const account = document.getElementById('account');
    const password = document.getElementById('password');

    if (!account || !password) {
        showPopup('error', '页面元素未找到');
        return;
    }

    const accountValue = account.value;
    const passwordValue = password.value;

    // 简单验证输入
    if (!accountValue.trim()) {
        showPopup('error', '请输入账号');
        return;
    }
    if (!passwordValue.trim()) {
        showPopup('error', '请输入密码');
        return;
    }

    try {
        const res = await fetch(loginUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({account: accountValue, password: passwordValue})
        });

        const data = await res.json();

        if (data.status === 'success') {
            showPopup('success', '登录成功');
            setTimeout(() => {
                window.location.href = redirectUrl;
            }, 1200);
        } else {
            showPopup('error', data.message || '登录失败');
        }
    } catch (err) {
        console.error('登录请求错误:', err);
        showPopup('error', '请求异常');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化背景效果
    initTechBackground();

    // 绑定回车键登录事件
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('keypress', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                login();
            }
        });
    }
});
