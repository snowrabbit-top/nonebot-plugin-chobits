"""
获取收藏表情
"""
import json

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.internal.params import ArgPlainText
from nonebot.adapters.onebot.v11 import Message, Bot, Event

from ...unit import ImageProcessor


class FetchCustomFace:
    # 缓存路径
    cache_path = '/media/debian/warehouse/Image/cache'

    def command(self):
        """
        定义获取收藏表情命令处理器
        """
        # 创建获取收藏表情命令，触发词为"获取收藏表情"
        fetch_custom_face = on_command(cmd="获取收藏表情")

        @fetch_custom_face.handle()
        async def handle_fetch_custom_face(bot: Bot, event: Event, args: Message = CommandArg()):
            """
            处理获取收藏表情命令
            :param bot:
            :param event:
            :param args: 命令参数
            """
            face_list = await bot.call_api(api="fetch_custom_face", count=6)
            for face in face_list:
                await fetch_custom_face.send(face)
            face_list = json.dumps(face_list)
            await fetch_custom_face.finish(face_list)
