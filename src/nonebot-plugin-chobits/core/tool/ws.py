"""
WebSocket 接口相关处理
"""

import contextlib
from collections.abc import Sequence

from nonebot.exception import WebSocketClosed
from nonebot.drivers import WebSocket


class ToolWSMixin:
    """
    WebSocket handlers
    """

    WS_ROUTES: Sequence[tuple[str, str]] = (
        # (PATH, ROUTE_NAME)
        ("/chobits/ws", "chobits_ws_echo"),
    )

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
