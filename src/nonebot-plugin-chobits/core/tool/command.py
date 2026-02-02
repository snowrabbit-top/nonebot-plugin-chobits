"""
命令相关处理
"""

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg


class ToolCommandMixin:
    """
    命令入口处理
    """

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
