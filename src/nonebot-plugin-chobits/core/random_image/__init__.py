"""
随机图片
"""
import os
import random
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.internal.params import ArgPlainText
from nonebot.adapters.onebot.v11 import Message, Bot, Event, MessageSegment

from ...unit import ImageProcessor


class RandomImage:
    image_path = '/media/debian/warehouse/Image/anime'
    # image_list = ImageProcessor().list_files_in_directory(image_path)
    napcat_path = '/app/napcat/Image/anime'

    def command(self):
        """
        命令列表
        """
        random_image = on_command("随机图片", aliases={"sjtp"})

        @random_image.handle()
        async def handle_random_image():
            """
            随机图片
            :return:
            """
            random_file = random.choice(self.image_list)
            file_path = "file://" + os.path.join(self.napcat_path, random_file)
            print(file_path)
            await random_image.finish(MessageSegment.image(file=file_path, type_="2"))
