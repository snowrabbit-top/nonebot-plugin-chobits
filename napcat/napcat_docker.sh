#!/bin/bash

# ========== 颜色 ==========
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ========== 检测操作系统类型 ==========
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        DISTRO=$ID
        VER=$VERSION_ID
    else
        echo -e "${RED}❌ 无法检测操作系统类型${NC}"
        exit 1
    fi
}

detect_os

# ========== 判断是否使用 sudo ==========
if [ "$EUID" -eq 0 ]; then
    SUDO=""
    USER_ID=0
    GROUP_ID=0
else
    SUDO="sudo"
    USER_ID=$(id -u)
    GROUP_ID=$(id -g)
fi

BASE_DIR="/opt/napcat"
IMAGE="docker.1ms.run/mlikiowa/napcat-docker:latest"

# ========== 安装 Docker ==========
install_docker() {
    echo -e "${CYAN}📦 检测到未安装 Docker，开始安装...${NC}"
    
    # 根据不同发行版执行不同的安装方式
    case $DISTRO in
        ubuntu|debian|raspbian)
            # 更新包索引
            echo -e "${BLUE}🔄 更新软件包索引...${NC}"
            ${SUDO} apt update
            
            # 安装必要包
            echo -e "${BLUE}📥 安装必要的包...${NC}"
            ${SUDO} apt install -y ca-certificates curl gnupg lsb-release
            
            # 添加 Docker 官方 GPG 密钥
            echo -e "${BLUE}🔐 添加 Docker 官方 GPG 密钥...${NC}"
            ${SUDO} install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/debian/gpg | ${SUDO} gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            ${SUDO} chmod a+r /etc/apt/keyrings/docker.gpg
            
            # 添加 Docker 仓库源
            echo -e "${BLUE}📡 添加 Docker 仓库源...${NC}"
            echo \
            "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
            $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
            ${SUDO} tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # 再次更新包索引
            ${SUDO} apt update
            
            # 安装 Docker 引擎
            echo -e "${BLUE}🐳 安装 Docker 引擎...${NC}"
            ${SUDO} apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        centos|rhel|fedora)
            # 对于 CentOS/RHEL/Fedora 系统
            ${SUDO} dnf install -y yum-utils
            ${SUDO} yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            ${SUDO} dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        opensuse-leap|opensuse-tumbleweed)
            # 对于 openSUSE 系统
            ${SUDO} zypper install -y docker
            ;;
        arch)
            # 对于 Arch Linux 系统
            ${SUDO} pacman -Syu --noconfirm docker
            ;;
        *)
            echo -e "${RED}❌ 不支持的操作系统: $DISTRO${NC}"
            echo -e "${YELLOW}💡 请手动安装 Docker 并重新运行此脚本${NC}"
            exit 1
            ;;
esac
    
    # 启动并启用 Docker 服务
    echo -e "${BLUE}▶️ 启动 Docker 服务...${NC}"
    ${SUDO} systemctl start docker
    ${SUDO} systemctl enable docker
    
    # 配置 Docker 镜像加速
    echo -e "${BLUE}🌐 配置 Docker 镜像加速...${NC}"
    ${SUDO} mkdir -p /etc/docker
    ${SUDO} tee /etc/docker/daemon.json > /dev/null <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF
    
    # 重启 Docker 服务使配置生效
    echo -e "${BLUE}🔄 重启 Docker 服务...${NC}"
    ${SUDO} systemctl restart docker
    
    # 将当前用户添加到 docker 组
    ${SUDO} usermod -aG docker $USER
    
    echo -e "${GREEN}✅ Docker 安装和配置完成！${NC}"
}

# ========== 依赖检查 ==========
echo -e "${CYAN}🔍 检查系统依赖...${NC}"
for cmd in docker jq ss; do
    if ! command -v "$cmd" &>/dev/null; then
        if [ "$cmd" = "docker" ]; then
            echo -e "${YELLOW}⚠️  未安装 Docker，将自动为您安装${NC}"
            install_docker
        else
            echo -e "${RED}❌ 未安装 $cmd，请先安装（如：${SUDO} apt install -y iproute2 jq）${NC}"
            exit 1
        fi
    fi
done
echo -e "${GREEN}✅ 依赖检查通过${NC}"

# ========== 端口占用检测函数 ==========
is_port_in_use() {
    local port=$1
    if ${SUDO} ss -tuln 2>/dev/null | grep -q ":$port\b"; then
        return 0
    else
        return 1
    fi
}

# ========== 安全读取端口（自动重试直到可用）==========
read_available_port() {
    local prompt="$1" default="$2"
    while true; do
        port=$(read_nonempty "$prompt" "$default")
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
            echo -e "${RED}❌ 请输入有效的端口号（1-65535）${NC}"
            continue
        fi
        if is_port_in_use "$port"; then
            echo -e "${YELLOW}⚠️  端口 $port 已被占用，请换一个！${NC}"
            continue
        fi
        echo "$port"
        return
    done
}

# ========== 通用非空输入 ==========
read_nonempty() {
    local prompt="$1" default="$2"
    while true; do
        if [[ -n "$default" ]]; then
            read -rp "$prompt (默认: $default): " input
            input="${input:-$default}"
        else
            read -rp "$prompt: " input
        fi
        if [[ -n "$input" ]]; then
            echo "$input"
            return
        else
            echo -e "${RED}⚠️ 输入不能为空${NC}"
        fi
    done
}

# ========== 主流程 ==========
echo -e "\n${PURPLE}============================================${NC}"
echo -e "${BLUE}🚀 添加 NapCat 容器（带端口占用检测）${NC}"
echo -e "${PURPLE}============================================${NC}"

while true; do
    qq=$(read_nonempty "请输入 QQ 号")
    container_name="napcat_$qq"
    data_dir="$BASE_DIR/$container_name"
    config_dir="$data_dir/config"

    # 删除旧容器（如果存在）
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${YELLOW}⚠️  容器 $container_name 已存在，正在清理...${NC}"
        ${SUDO} docker rm -f "$container_name" >/dev/null 2>&1
    fi

    # 创建目录
    ${SUDO} mkdir -p "$config_dir"
    ${SUDO} chmod 777 "$data_dir" "$config_dir"

    # ========== 用户输入 WebSocket 参数 ==========
    name=$(read_nonempty "客户端名称" "WsClient")
    url=$(read_nonempty "WebSocket 地址" "ws://host.docker.internal:12000/onebot/v11/ws/")
    reconnect_interval=$(read_nonempty "重连间隔（毫秒）" "1200")
    if ! [[ "$reconnect_interval" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}❌ 重连间隔必须为数字，使用默认值 1200${NC}"
        reconnect_interval=1200
    fi

    # ========== 生成配置内容 ==========
    NAPCAT_CONTENT='{
    "fileLog": false,
    "consoleLog": true,
    "fileLogLevel": "debug",
    "consoleLogLevel": "info",
    "packetBackend": "auto",
    "packetServer": "",
    "o3HookMode": 1
}'

    ONEBOT_CONTENT=$(jq -n \
        --arg name "$name" \
        --arg url "$url" \
        --argjson interval "$reconnect_interval" \
        '{
          "network": {
            "httpServers": [],
            "httpSseServers": [],
            "httpClients": [],
            "websocketServers": [],
            "websocketClients": [
              {
                "enable": true,
                "name": $name,
                "url": $url,
                "reportSelfMessage": false,
                "messagePostFormat": "array",
                "token": "",
                "debug": false,
                "heartInterval": 30000,
                "reconnectInterval": $interval
              }
            ],
            "plugins": []
          },
          "musicSignUrl": "",
          "enableLocalFile2Url": false,
          "parseMultMsg": false
        }')

    # 写入四个文件
    echo "$NAPCAT_CONTENT" | ${SUDO} tee "$config_dir/napcat.json" >/dev/null
    echo "$NAPCAT_CONTENT" | ${SUDO} tee "$config_dir/napcat_${qq}.json" >/dev/null
    echo "$ONEBOT_CONTENT" | ${SUDO} tee "$config_dir/onebot11.json" >/dev/null
    echo "$ONEBOT_CONTENT" | ${SUDO} tee "$config_dir/onebot11_${qq}.json" >/dev/null
    ${SUDO} chmod 644 "$config_dir"/*.json

    echo -e "${GREEN}✅ 四个配置文件已创建于: $config_dir${NC}"

    # ========== 输入端口（按你要求的用途命名）==========
    default_api_port=$((3001 + ${#qq}))
    host_api_port=$(read_available_port "宿主机 API 端口（用于 OneBot HTTP API）" "$default_api_port")
    host_webui_port=$(read_available_port "宿主机 WebUI 端口（用于 NapCat 控制面板）" "6099")

    # ========== 启动容器 ==========
    echo -e "\n${BLUE}🐳 启动容器: $container_name${NC}"
    # 打印将要执行的 Docker 命令
    echo -e "${CYAN}📋 执行的 Docker 命令:${NC}"
    echo -e "${CYAN}    ${SUDO} docker run -d \${NC}"
    echo -e "${CYAN}        --name \"$container_name\" \${NC}"
    echo -e "${CYAN}        --restart=always \${NC}"
    echo -e "${CYAN}        --add-host=host.docker.internal:host-gateway \${NC}"
    echo -e "${CYAN}        -e ACCOUNT=\"$qq\" \${NC}"
    echo -e "${CYAN}        -e WS_ENABLE=false \${NC}"
    echo -e "${CYAN}        -e WSR_ENABLE=false \${NC}"
    echo -e "${CYAN}        -e HTTP_ENABLE=false \${NC}"
    echo -e "${CYAN}        -e NAPCAT_UID=\"$USER_ID\" \${NC}"
    echo -e "${CYAN}        -e NAPCAT_GID=\"$GROUP_ID\" \${NC}"
    echo -e "${CYAN}        -p \"$host_api_port:3001\" \${NC}"
    echo -e "${CYAN}        -p \"$host_webui_port:6099\" \${NC}"
    echo -e "${CYAN}        -v \"$data_dir:/app/napcat\" \${NC}"
    echo -e "${CYAN}        \"$IMAGE\"${NC}"
    
    ${SUDO} docker run -d \
        --name "$container_name" \
        --restart=always \
        --add-host=host.docker.internal:host-gateway \
        -e ACCOUNT="$qq" \
        -e WS_ENABLE=false \
        -e WSR_ENABLE=false \
        -e HTTP_ENABLE=false \
        -e NAPCAT_UID="$USER_ID" \
        -e NAPCAT_GID="$GROUP_ID" \
        -p "$host_api_port:3001" \
        -p "$host_webui_port:6099" \
        -v "$data_dir:/app/napcat" \
        "$IMAGE" >/dev/null 2>&1

    # 检查容器是否真正创建成功
    if ${SUDO} docker inspect "$container_name" &>/dev/null; then
        echo -e "\n${GREEN}🎉 容器 $container_name 启动成功！${NC}"
        echo -e "   📁 数据目录: $data_dir"
        echo -e "   🌐 API 端口: http://localhost:$host_api_port"
        echo -e "   🖥️  WebUI 端口: http://localhost:$host_webui_port"
        echo -e "   🔗 WebSocket: $url"
        echo -e ""
        echo -e "   💬 查看日志:      ${CYAN}docker logs $container_name${NC}"
        echo -e "   ▶️ 启动容器:      ${CYAN}docker start $container_name${NC}"
        echo -e "   🔄 重启容器:      ${CYAN}docker restart $container_name${NC}"
        echo -e "   🐚 进入容器:      ${CYAN}docker exec -it $container_name /bin/bash${NC}"
        echo -e "   📋 查看状态:      ${CYAN}docker ps | grep $container_name${NC}"
    else
        echo -e "${RED}❌ 容器启动失败！可能原因：镜像拉取失败、端口冲突、权限问题等。${NC}"
        echo -e ""
        echo -e "   🔧 手动调试命令（前台运行，查看实时日志）："
        echo -e "      ${CYAN}docker run --rm -it \\"
        echo -e "        -v $data_dir:/app/napcat \\"
        echo -e "        -v /media/debian/warehouse/Image:/app/napcat/Image \\"
        echo -e "        -p $host_api_port:3001 \\"
        echo -e "        -p $host_webui_port:6099 \\"
        echo -e "        --add-host=host.docker.internal:host-gateway \\"
        echo -e "        -e ACCOUNT=$qq \\"
        echo -e "        $IMAGE${NC}"
        echo -e ""
        echo -e "   📋 检查容器列表: ${CYAN}docker ps -a | grep $container_name${NC}"
        echo -e "   🗑️ 清理残留容器: ${CYAN}docker rm -f $container_name 2>/dev/null${NC}"
    fi
    echo -e "\n${PURPLE}────────────────────────────────────────────${NC}"
    read -rp "继续添加其他账号？(y/N): " again
    [[ ! "$again" =~ ^[Yy]$ ]] && break
done

echo -e "\n${GREEN}✨ 所有 NapCat 实例部署完成！${NC}"
