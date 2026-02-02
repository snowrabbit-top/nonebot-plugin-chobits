"""
天依哈气
"""
import os
import random

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Bot, Event

from ...unit import ImageProcessor


class HA:
    image_path = ''
    cache_image_path = ''
    image_list = ''
    napcat_path = ''
    group_list = []
    ha_list = []

    def __init__(self):
        self.image_path = '/media/debian/warehouse/Image/test/ha'
        self.cache_image_path = '/media/debian/warehouse/Image/test/cache'
        self.image_list = ImageProcessor().list_files_in_directory(self.image_path)
        self.napcat_path = '/app/napcat/Image/test/ha'
        self.group_list = [330591690, 1078155153, 83135114, 83135115]
        self.ha_list = ['哈', 'ha', 'HA']

    def command(self):
        """
        命令列表
        :return:
        """
        self.__init__()
        ha = on_regex(pattern=r'.*')

        @ha.handle()
        async def handle_ha(bot: Bot, event: Event, ):
            """
            处理
            :param bot:
            :param event:
            :return:
            """
            if event.group_id in self.group_list:
                # image_processor = ImageProcessor()
                # result = image_processor.download_image(message.data.get('url'), self.cache_image_path)
                # print(result)
                # result = await bot.call_api(".ocr_image", image=f"file://{result.get('file_path')}")

                message = event.get_plaintext()
                image = random.choice(self.image_list)
                file_path = "file://" + os.path.join(self.napcat_path, image)
                if any(keyword in message for keyword in self.ha_list):
                    await bot.send_group_msg(group_id=event.group_id, message={
                        "type": "image",
                        "data": {
                            "summary": "哈！",
                            "sub_type": 1,
                            "file": file_path
                        }
                    })
                    await ha.finish()
