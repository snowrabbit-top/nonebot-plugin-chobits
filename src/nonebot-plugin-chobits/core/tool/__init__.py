"""
Chobits 管理工具
"""

from .command import ToolCommandMixin
from .common import ToolCommonMixin
from .http import ToolHTTPMixin
from .server import ToolServerMixin
from .ws import ToolWSMixin


class Tool(
    ToolHTTPMixin,
    ToolWSMixin,
    ToolCommandMixin,
    ToolServerMixin,
    ToolCommonMixin,
):
    """
    Chobits 管理工具类

    作用：
    - 提供一组 HTTP/WS 管理服务接口（通过 nonebot 的 driver 路由能力注册）
    - 提供一组聊天命令入口（/chobits ...）用于提示或触发服务端接口

    使用方式（典型）：
    - 在插件加载时调用：Tool().server() 注册路由
    - 在插件加载时调用：Tool().command() 注册命令
    """


__all__ = ["Tool"]
