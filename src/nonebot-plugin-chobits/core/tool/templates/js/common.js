// 创建动态粒子背景
function createParticles(containerId = 'particles', particleCount = 25) {
    const particlesContainer = document.getElementById(containerId);
    if (!particlesContainer) return;

    particlesContainer.innerHTML = '';

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';

        const left = Math.random() * 100;
        const delay = Math.random() * 20;
        const duration = 15 + Math.random() * 25;

        particle.style.left = `${left}%`;
        particle.style.animationDelay = `-${delay}s`;
        particle.style.animationDuration = `${duration}s`;

        const size = 1 + Math.random() * 1.2;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;

        const opacity = 0.12 + Math.random() * 0.25;
        const blueTint = 140 + Math.floor(Math.random() * 40);
        particle.style.background = `rgba(0, ${blueTint}, 180, ${opacity})`;

        particlesContainer.appendChild(particle);
    }
}

// 创建动态背景光晕
function createBackgroundGlows() {
    const body = document.body;
    const glowCount = 4;

    document.querySelectorAll('.glow-circle').forEach(node => node.remove());

    const positions = [
        {top: '10%', left: '15%'},
        {bottom: '15%', right: '20%'},
        {top: '25%', right: '10%'},
        {bottom: '20%', left: '25%'}
    ];
    const sizes = [200, 250, 180, 220];
    const colors = [
        'radial-gradient(circle, #008cff, transparent)',
        'radial-gradient(circle, #00c8dc, transparent)',
        'radial-gradient(circle, #0070b0, transparent)',
        'radial-gradient(circle, #00a0d0, transparent)'
    ];

    for (let i = 0; i < glowCount; i++) {
        const glow = document.createElement('div');
        glow.className = 'glow-circle';

        const pos = positions[i];
        if (pos.top) glow.style.top = pos.top;
        if (pos.bottom) glow.style.bottom = pos.bottom;
        if (pos.left) glow.style.left = pos.left;
        if (pos.right) glow.style.right = pos.right;

        glow.style.width = `${sizes[i]}px`;
        glow.style.height = `${sizes[i]}px`;
        glow.style.background = colors[i];

        const delay = Math.random() * 5;
        const duration = 8 + Math.random() * 12;
        glow.style.animation = `glowPulse${i} ${duration}s ease-in-out ${delay}s infinite alternate`;

        body.appendChild(glow);

        const style = document.createElement('style');
        style.textContent = `
        @keyframes glowPulse${i} {
            0% { opacity: 0.10; transform: scale(0.95); }
            50% { opacity: 0.18; transform: scale(1.05); }
            100% { opacity: 0.12; transform: scale(1); }
        }
        `;
        document.head.appendChild(style);
    }
}

// 显示弹出消息
function showPopup(type, message, duration = 2000) {
    const popup = document.createElement('div');
    popup.className = 'popup';

    const popupIcon = document.createElement('div');
    popupIcon.className = `icon ${type}`;
    popupIcon.innerHTML = type === 'success' ? '✔' : '✘';

    const popupMsg = document.createElement('div');
    popupMsg.textContent = message;

    popup.appendChild(popupIcon);
    popup.appendChild(popupMsg);
    document.body.appendChild(popup);

    requestAnimationFrame(() => popup.classList.add('show'));

    setTimeout(() => {
        popup.classList.remove('show');
        popup.addEventListener('transitionend', () => popup.remove(), {once: true});
    }, duration);
}

// 初始化科技感背景
function initTechBackground(particlesContainerId = 'particles', particleCount = 25) {
    let particlesContainer = document.getElementById(particlesContainerId);
    if (!particlesContainer) {
        particlesContainer = document.createElement('div');
        particlesContainer.id = particlesContainerId;
        particlesContainer.className = 'particles';
        document.body.insertBefore(particlesContainer, document.body.firstChild);
    }

    createParticles(particlesContainerId, particleCount);
    createBackgroundGlows();
}

// 侧边栏菜单交互
function setupSidebarNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    if (!navItems.length) return;

    navItems.forEach(item => {
        item.addEventListener('click', function () {
            navItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            const titleText = this.querySelector('span:last-child')?.textContent;
            const headerTitle = document.querySelector('.header-title');
            const breadcrumb = document.querySelector('.breadcrumb span:last-child');

            if (titleText && headerTitle) headerTitle.textContent = titleText;
            if (titleText && breadcrumb) breadcrumb.textContent = titleText;
        });
    });
}
