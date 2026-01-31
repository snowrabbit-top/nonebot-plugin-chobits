---

## ✅ 一、Docker 容器镜像地址

在脚本中，容器镜像地址为：

```
mlikiowa/napcat-docker:latest
```

如果使用了代理（如 `--proxy` 参数），会自动加上代理前缀，例如：

```
https://docker.1ms.run/mlikiowa/napcat-docker:latest
```

但**默认不加代理时的官方地址就是**：

> **`mlikiowa/napcat-docker:latest`**

该镜像托管在 [Docker Hub](https://hub.docker.com/r/mlikiowa/napcat-docker) 上。

---

## ✅ 二、如何下载这个镜像？

你不需要手动“下载”，Docker 在 `run` 时会自动拉取。但如果你想**提前拉取**，可以运行：

```bash
docker pull mlikiowa/napcat-docker:latest
```

> ⚠️ 注意：你的用户必须属于 `docker` 用户组，或使用 `sudo`。

---

## ✅ 三、如何运行 NapCat Docker 容器？

脚本支持三种运行模式，对应不同的环境变量和端口映射：

### 1. **WebSocket 模式（`ws`）**

```bash
docker run -d \
  -e ACCOUNT=你的QQ号 \
  -e WS_ENABLE=true \
  -e NAPCAT_UID=$(id -u) \
  -e NAPCAT_GID=$(id -g) \
  -p 3001:3001 \
  -p 6099:6099 \
  --name napcat \
  --restart=always \
  mlikiowa/napcat-docker:latest
```

- 提供正向 WebSocket 服务（OneBot v11）
- WebUI/API 端口：`3001`
- NapCat 内部通信端口：`6099`

---

### 2. **反向 WebSocket 模式（`reverse_ws`）**

```bash
docker run -d \
  -e ACCOUNT=你的QQ号 \
  -e WSR_ENABLE=true \
  -e NAPCAT_UID=$(id -u) \
  -e NAPCAT_GID=$(id -g) \
  -p 6099:6099 \
  --name napcat \
  --restart=always \
  mlikiowa/napcat-docker:latest
```

- 容器会主动连接你指定的反向 WebSocket 服务器（需在配置中设置 URL）
- 只需暴露 `6099` 端口（用于 NapCat 自身通信或日志）

---

### 3. **反向 HTTP 模式（`reverse_http`）**

```bash
docker run -d \
  -e ACCOUNT=你的QQ号 \
  -e HTTP_ENABLE=true \
  -e NAPCAT_UID=$(id -u) \
  -e NAPCAT_GID=$(id -g) \
  -p 3000:3000 \
  -p 6099:6099 \
  --name napcat \
  --restart=always \
  mlikiowa/napcat-docker:latest
```

- 提供反向 HTTP POST 推送（OneBot v11）
- HTTP 回调监听端口：`3000`
- 同样需要你在 NapCat 配置中指定目标 URL

---

## ✅ 四、关键说明

| 环境变量                        | 作用                    |
|-----------------------------|-----------------------|
| `ACCOUNT`                   | 必填！你的 QQ 号码           |
| `WS_ENABLE`                 | 启用正向 WebSocket        |
| `WSR_ENABLE`                | 启用反向 WebSocket        |
| `HTTP_ENABLE`               | 启用反向 HTTP             |
| `NAPCAT_UID` / `NAPCAT_GID` | 用于容器内以当前用户身份运行，避免权限问题 |

> 💡 实际运行时，脚本会自动填充 `$(id -u)` 和 `$(id -g)`，确保文件权限正确。

---

## ✅ 五、完整示例（以 WebSocket 模式为例）

```bash
# 替换 123456789 为你的 QQ 号
docker run -d \
  -e ACCOUNT=123456789 \
  -e WS_ENABLE=true \
  -e NAPCAT_UID=$(id -u) \
  -e NAPCAT_GID=$(id -g) \
  -p 3001:3001 \
  -p 6099:6099 \
  --name napcat \
  --restart=always \
  mlikiowa/napcat-docker:latest
```

启动后：

- 访问 `http://localhost:3001` 可打开 NapCat WebUI（首次需扫码登录）
- OneBot WebSocket 地址：`ws://localhost:3001`

---

如需查看日志：

```bash
docker logs -f napcat
```

停止容器：

```bash
docker stop napcat
```

删除容器：

```bash
docker rm -f napcat
```

---

```shell
docker ps
docker exec -it napcat_1851991319 /bin/bash
docker restart napcat_1851991319
docker start napcat_1851991319
docker logs napcat_1851991319
docker exec -it napcat_1851991319 /bin/bash
cd /work/python/qq-bot/
source .venv/bin/activate
nohup nb run -r > /dev/null 2>&1 &
```
