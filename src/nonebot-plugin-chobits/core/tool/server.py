"""
服务端路由注册
"""

from nonebot import get_driver, logger
from nonebot.drivers import ASGIMixin, HTTPServerSetup, URL, WebSocketServerSetup


class ToolServerMixin:
    """
    负责注册 HTTP / WebSocket 路由
    """

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
