"""
换头像功能
允许用户通过回复带图片的消息来更换自己的QQ头像
"""
from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, MessageEvent


class SetQQAvatar:

    def command(self):
        """
        定义换头像命令处理器
        """
        # 创建换头像命令，触发词为"换头像"
        set_qq_avatar = on_command(cmd="换头像", permission=SUPERUSER)

        @set_qq_avatar.handle()
        async def handle_set_qq_avatar(bot: Bot, event: Event):
            """
            处理换头像命令
            :param bot: 机器人实例
            :param event: 事件对象
            """
            await set_qq_avatar.send("读取信息中...")
            # 检查是否有回复消息
            if not hasattr(event, 'reply') or not event.reply:
                await set_qq_avatar.finish("请回复一条包含图片的消息来设置头像")
                return

            reply_id = event.reply.message_id

            try:
                # 获取回复的消息内容
                reply_message = await bot.call_api('get_msg', message_id=reply_id)

                # 遍历消息内容，查找图片
                for content in reply_message['message']:
                    if content['type'] == 'image':
                        # 提取图片URL
                        avatar_image_path = content['data']['url']

                        await set_qq_avatar.send(f"头像地址为: {avatar_image_path}")

                        # 调用OneBot V11协议的设置QQ头像API
                        await bot.call_api(
                            api="set_qq_avatar",
                            file=avatar_image_path
                        )
                        await set_qq_avatar.finish("QQ头像更换成功！")

                # 如果回复消息中没有找到图片
                await set_qq_avatar.finish("回复的消息中没有图片，无法设置头像")

            except Exception as e:
                # 处理可能出现的异常情况
                await set_qq_avatar.finish(f"设置QQ头像时出现错误: {str(e)}")
