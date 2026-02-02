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
    # -------------------------
    # 路由配置（集中定义，一眼看全）
    # -------------------------
    HTTP_ROUTES: Sequence[tuple[str, str, str]] = (
        ("GET", "/chobits/ping", "chobits_http_ping"),
        ("GET", "/chobits/status", "chobits_http_status"),
        ("GET", "/chobits/command", "chobits_http_command"),
    )
    WS_ROUTES: Sequence[tuple[str, str]] = (
        ("/chobits/ws", "chobits_ws_echo"),
    )

    # -------------------------
    # HTTP handlers（路由 = 方法）
    # -------------------------
    async def http_ping(self, _: Request) -> Response:
        return Response(200, content="pong")

    async def http_status(self, _: Request) -> Response:
        payload = {
            "ok": True,
            "driver_type": getattr(get_driver(), "type", None),
            "bots": list(get_bots().keys()),
        }
        return self._json(payload)

    async def http_command(self, request: Request) -> Response:
        cmd = self._query(request, "cmd")
        if not cmd:
            return self._json({"ok": False, "error": "missing query param: cmd"}, status=400)

        # TODO: 替换为你的真实逻辑（强烈建议加鉴权/白名单）
        return self._json({"ok": True, "cmd": cmd, "result": f"received: {cmd}"})

    # -------------------------
    # WebSocket handlers
    # -------------------------
    async def ws_echo(self, ws: WebSocket) -> None:
        await ws.accept()
        try:
            while True:
                data = await ws.receive()
                await ws.send("回复:" + self._ws_text(data))
        except WebSocketClosed:
            pass
        finally:
            with contextlib.suppress(Exception):
                await ws.close()

    # -------------------------
    # 注册入口
    # -------------------------
    def server(self) -> None:
        """
        服务
        - GET  /chobits/ping
        - GET  /chobits/status
        - GET  /chobits/command?cmd=
        - WS   /chobits/ws
        """
        driver = get_driver()
        if not isinstance(driver, ASGIMixin):
            logger.warning("Chobits Tool.server: 当前驱动不是服务端类型（非 ASGIMixin），跳过路由注册")
            return

        # HTTP
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

        # WebSocket
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
        命令
        - /chobits
        - /chobits ping
        - /chobits status
        - /chobits cmd <...>
        """
        matcher = on_command("chobits", priority=5, block=True)

        @matcher.handle()
        async def _(m: Matcher, args: Message = CommandArg()):
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
        return Response(
            status,
            content=json.dumps(payload, ensure_ascii=False),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    def _query(self, request: Request, key: str) -> str | None:
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
        将 ws.receive() 的返回值稳妥地转成文本。
        """
        if data is None:
            return ""
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        if isinstance(data, str):
            return data
        # dict / list / 其他对象：尽量 JSON 化，失败就 str()
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return str(data)
