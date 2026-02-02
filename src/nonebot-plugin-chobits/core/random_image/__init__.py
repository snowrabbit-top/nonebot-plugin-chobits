"""
随机图片
"""
import os
import random
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageSegment

from ...unit import ImageProcessor


class RandomImage:
    image_path = ''
    image_list = ''
    napcat_path = ''

    def __init__(self):
        self.image_path = '/media/debian/warehouse/Image/anime'
        self.napcat_path = '/app/napcat/Image/anime'
        self.image_list = ImageProcessor().list_files_in_directory(self.image_path)

    def command(self):
        """
        命令列表
        """
        self.__init__()
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
