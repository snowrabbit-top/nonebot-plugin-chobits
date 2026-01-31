"""
天依哈气
"""
import os
import random
import httpx

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment

from ...unit import ImageProcessor


class HA:
    image_path = '/media/debian/warehouse/Image/test/ha'
    cache_image_path = '/media/debian/warehouse/Image/test/cache'
    # image_list = ImageProcessor().list_files_in_directory(image_path)
    napcat_path = '/app/napcat/Image/test/ha'

    def command(self):
        """

        :return:
        """
        ha = on_regex(pattern=r'.*')

        @ha.handle()
        async def handle_ha(bot: Bot, event: Event, ):
            """
            处理
            :param bot:
            :param event:
            :return:
            """
            if event.group_id in [330591690, 1078155153, 83135114, 83135115]:
                # image_processor = ImageProcessor()
                # result = image_processor.download_image(message.data.get('url'), self.cache_image_path)
                # print(result)
                # result = await bot.call_api(".ocr_image", image=f"file://{result.get('file_path')}")

                message = event.get_plaintext()
                image = random.choice(self.image_list)
                file_path = "file://" + os.path.join(self.napcat_path, image)
                ha_list = ['哈', 'ha', 'HA']
                if any(keyword in message for keyword in ha_list):
                    await bot.send_group_msg(group_id=event.group_id, message={
                        "type": "image",
                        "data": {
                            "summary": "哈！",
                            "sub_type": 1,
                            "file": file_path
                        }
                    })
                    await ha.finish()
