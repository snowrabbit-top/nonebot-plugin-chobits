"""
HTTP 接口相关处理
"""

from collections.abc import Sequence

from nonebot import get_bots, get_driver
from nonebot.drivers import Request, Response


class ToolHTTPMixin:
    """
    HTTP handlers
    """

    HTTP_ROUTES: Sequence[tuple[str, str, str]] = (
        # (HTTP_METHOD, PATH, ROUTE_NAME)
        ("GET", "/chobits/ping", "chobits_http_ping"),
        ("GET", "/chobits/status", "chobits_http_status"),
        ("GET", "/chobits/command", "chobits_http_command"),
    )

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
