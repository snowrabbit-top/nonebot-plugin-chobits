"""
Chobits 管理工具
"""

import contextlib
import json
from collections.abc import Mapping, Sequence

from nonebot import get_bots, get_driver, logger, on_command
from nonebot.adapters import Message
from nonebot.drivers import (
    ASGIMixin,
    HTTPServerSetup,
    Request,
    Response,
    URL,
    WebSocket,
    WebSocketServerSetup,
)
from nonebot.exception import WebSocketClosed
from nonebot.matcher import Matcher
from nonebot.params import CommandArg


class Tool:
    """
    Chobits 管理工具类

    作用：
    - 提供一组 HTTP/WS 管理服务接口（通过 nonebot 的 driver 路由能力注册）
    - 提供一组聊天命令入口（/chobits ...）用于提示或触发服务端接口

    使用方式（典型）：
    - 在插件加载时调用：Tool().server() 注册路由
    - 在插件加载时调用：Tool().command() 注册命令
    """

    # -------------------------
    # 路由配置（集中定义，一眼看全）
    # -------------------------
    HTTP_ROUTES: Sequence[tuple[str, str, str]] = (
        # (HTTP_METHOD, PATH, ROUTE_NAME)
        ("GET", "/chobits/ping", "chobits_http_ping"),
        ("GET", "/chobits/status", "chobits_http_status"),
        ("GET", "/chobits/command", "chobits_http_command"),
    )
    WS_ROUTES: Sequence[tuple[str, str]] = (
        # (PATH, ROUTE_NAME)
        ("/chobits/ws", "chobits_ws_echo"),
    )

    # -------------------------
    # HTTP handlers（路由 = 方法）
    # -------------------------
    async def http_ping(self, _: Request) -> Response:
        """
        HTTP 健康检查接口

        路由：
        - GET /chobits/ping

        用途：
        - 用于探测服务是否存活、路由是否成功注册

        参数：
        - _: Request（未使用）

        返回：
        - Response：200 + "pong"
        """
        return Response(200, content="pong")

    async def http_status(self, _: Request) -> Response:
        """
        HTTP 状态查询接口

        路由：
        - GET /chobits/status

        用途：
        - 返回当前 driver 类型、已连接 bot 列表等信息

        参数：
        - _: Request（未使用）

        返回：
        - Response：200 + JSON
          {
            "ok": true,
            "driver_type": "...",
            "bots": [...]
          }
        """
        payload = {
            "ok": True,
            "driver_type": getattr(get_driver(), "type", None),
            "bots": list(get_bots().keys()),
        }
        return self._json(payload)

    async def http_command(self, request: Request) -> Response:
        """
        HTTP 命令执行入口（示例占位）

        路由：
        - GET /chobits/command?cmd=xxx

        用途：
        - 作为“管理命令”统一入口（目前示例只是回显）
        - 真实使用请务必加鉴权/白名单/签名校验等安全措施

        参数：
        - request: Request
          用于读取 query 参数 cmd

        返回：
        - Response：
          - 400：缺少 cmd 参数
          - 200：返回 {"ok": True, "cmd": "...", "result": "..."}
        """
        cmd = self._query(request, "cmd")
        if not cmd:
            return self._json({"ok": False, "error": "missing query param: cmd"}, status=400)

        # TODO: 替换为你的真实逻辑（强烈建议加鉴权/白名单）
        return self._json({"ok": True, "cmd": cmd, "result": f"received: {cmd}"})

    # -------------------------
    # WebSocket handlers
    # -------------------------
    async def ws_echo(self, ws: WebSocket) -> None:
        """
        WebSocket Echo 服务（示例）

        路由：
        - WS /chobits/ws

        用途：
        - 接收客户端发送的消息，并回传 “回复:<消息内容>”
        - 适合作为连通性测试或调试通道（生产环境建议加鉴权/限制来源）

        参数：
        - ws: WebSocket
          nonebot driver 抽象的 WebSocket 连接对象

        返回：
        - None（通过 ws.send 推送消息）

        注意：
        - ws.receive() 的返回类型可能是 str/bytes/dict/...，因此使用 _ws_text 做兼容转换
        """
        await ws.accept()
        try:
            while True:
                data = await ws.receive()
                await ws.send("回复:" + self._ws_text(data))
        except WebSocketClosed:
            # 客户端断开或连接关闭
            pass
        finally:
            # 尽最大努力关闭连接，避免抛异常影响上层
            with contextlib.suppress(Exception):
                await ws.close()

    # -------------------------
    # 注册入口
    # -------------------------
    def server(self) -> None:
        """
        注册 HTTP / WebSocket 路由到 nonebot driver

        用途：
        - 将本类中定义的 handler 绑定到指定路径
        - 需要 driver 支持服务端能力（ASGIMixin），否则跳过注册

        注册的接口：
        - GET  /chobits/ping
        - GET  /chobits/status
        - GET  /chobits/command?cmd=
        - WS   /chobits/ws

        返回：
        - None

        注意：
        - route 的 name 必须全局唯一；重复注册通常会报错或冲突
        """
        driver = get_driver()
        if not isinstance(driver, ASGIMixin):
            logger.warning("Chobits Tool.server: 当前驱动不是服务端类型（非 ASGIMixin），跳过路由注册")
            return

        # HTTP：route name -> handler 映射（确保路由定义与方法对应）
        name_to_handler = {
            "chobits_http_ping": self.http_ping,
            "chobits_http_status": self.http_status,
            "chobits_http_command": self.http_command,
        }
        for method, path, name in self.HTTP_ROUTES:
            handler = name_to_handler.get(name)
            if handler is None:
                raise RuntimeError(f"HTTP route name={name} 没有对应 handler")
            driver.setup_http_server(
                HTTPServerSetup(
                    path=URL(path),
                    method=method,
                    name=name,
                    handle_func=handler,
                )
            )

        # WebSocket：route name -> handler 映射
        ws_name_to_handler = {
            "chobits_ws_echo": self.ws_echo,
        }
        for path, name in self.WS_ROUTES:
            handler = ws_name_to_handler.get(name)
            if handler is None:
                raise RuntimeError(f"WS route name={name} 没有对应 handler")
            driver.setup_websocket_server(
                WebSocketServerSetup(
                    path=URL(path),
                    name=name,
                    handle_func=handler,
                )
            )

    def command(self):
        """
        注册聊天命令：/chobits

        用途：
        - 给用户一个聊天侧的入口，用于提示/引导访问 HTTP 服务
        - 当前实现是“提示型命令”，不直接执行敏感操作

        支持的子命令：
        - /chobits
          输出帮助
        - /chobits ping
          输出 ping 接口说明
        - /chobits status
          输出 status 接口说明
        - /chobits cmd <...>
          输出 command 接口调用示例

        返回：
        - matcher（可选返回，用于外部继续链式操作或测试）
        """
        matcher = on_command("chobits", priority=5, block=True)

        @matcher.handle()
        async def _(m: Matcher, args: Message = CommandArg()):
            """
            chobits 命令处理函数（内部 handler）

            参数：
            - m: Matcher
              nonebot 的匹配器对象，用于 finish/send 等
            - args: Message
              命令参数（/chobits 后面的内容）

            行为：
            - 根据子命令分支返回提示文本
            """
            text = args.extract_plain_text().strip()
            if not text:
                await m.finish(self._help())

            head, *rest = text.split(maxsplit=1)
            head = head.lower()
            tail = rest[0].strip() if rest else ""

            if head == "ping":
                await m.finish("OK：GET /chobits/ping -> pong")
            if head == "status":
                await m.finish("OK：GET /chobits/status -> {ok, driver_type, bots}")
            if head == "cmd":
                if not tail:
                    await m.finish("用法：/chobits cmd <something>")
                await m.finish(f"OK：GET /chobits/command?cmd={tail}")

            await m.finish(self._help())

        return matcher

    # -------------------------
    # helpers
    # -------------------------
    def _help(self) -> str:
        """
        生成帮助文本（供命令 /chobits 使用）

        返回：
        - str：包含支持的子命令与服务端路由列表
        """
        return (
            "Chobits 管理工具：\n"
            "- /chobits ping\n"
            "- /chobits status\n"
            "- /chobits cmd <something>\n"
            "服务端：\n"
            "/chobits/ping\n"
            "/chobits/status\n"
            "/chobits/command?cmd=\n"
            "WS: /chobits/ws"
        )

    def _json(self, payload: object, status: int = 200) -> Response:
        """
        将 Python 对象序列化为 JSON 响应

        参数：
        - payload: object
          任意可 JSON 序列化对象
        - status: int
          HTTP 状态码，默认 200

        返回：
        - Response：JSON 字符串 + UTF-8 content-type
        """
        return Response(
            status,
            content=json.dumps(payload, ensure_ascii=False),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    def _query(self, request: Request, key: str) -> str | None:
        """
        从 Request 中读取 query 参数（兼容不同 driver 的 query 表达）

        参数：
        - request: Request
          nonebot driver 的 Request 抽象
        - key: str
          query 参数名

        返回：
        - str | None：找到则返回字符串；否则返回 None

        说明：
        - 某些 driver 的 request.url.query 是 Mapping
        - 某些是 MultiDict 风格（提供 .get）
        - 因此此处做了兼容处理
        """
        query = getattr(request.url, "query", None)
        if query is None:
            return None

        if isinstance(query, Mapping):
            v = query.get(key)
            return str(v) if v is not None else None

        get = getattr(query, "get", None)
        if callable(get):
            v = get(key)
            return str(v) if v is not None else None

        return None

    def _ws_text(self, data: object) -> str:
        """
        将 ws.receive() 的返回值稳妥地转成文本

        参数：
        - data: object
          ws.receive() 返回的任意对象（可能是 str/bytes/dict/...）

        返回：
        - str：可安全拼接/发送的字符串

        策略：
        - bytes：按 utf-8 解码（无法解码时替换异常字符）
        - str：原样返回
        - 其他：尽量 json.dumps，失败则 str()
        """
        if data is None:
            return ""
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return str(data)
