"""
机器人生命周期控制器
"""
from nonebot import get_driver, get_adapter, on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Adapter


class LifeCycle:

    def command(self):
        """
        命令列表
        """
        driver = get_driver()

        @driver.on_startup
        async def handle_startup():
            """
            开机处理
            :param bot:
            :return:
            """
            print("机器人已开机")

        @driver.on_shutdown
        async def handle_shutdown():
            """
            关机处理
            :param bot:
            :return:
            """
            print("机器人已关机")

        @driver.on_bot_connect
        async def handle_bot_connect(bot: Bot):
            """
            Bot 连接处理
            :param bot:
            :return:
            """
            print("bot已连接")
            print(bot)
            if bot.self_id == "1018784768":
                await bot.call_api(api="send_msg", message_type='group', group_id=1078155153, message=f"bot已连接")
            elif bot.self_id == "1851991319":
                await bot.call_api(api="send_msg", message_type='group', group_id=330591690, message=f"bot已连接")


        @driver.on_bot_disconnect
        async def handle_bot_disconnect(bot: Bot):
            """
            Bot 断开连接处理
            :param bot:
            :return:
            """
            print("bot已断开")
            print(bot)
            if bot.self_id == "1018784768":
                await bot.call_api(api="send_msg", message_type='group', group_id=1078155153, message=f"bot已连接")
            elif bot.self_id == "1851991319":
                await bot.call_api(api="send_msg", message_type='group', group_id=330591690, message=f"bot已连接")
