"""
换群头像功能
允许群管理员通过回复带图片的消息来更换群头像
"""
from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent


class SetGroupPortrait:

    def command(self):
        """
        定义换群头像命令处理器
        """
        # 创建换群头像命令，触发词为"换群头像"
        set_group_portrait = on_command(cmd="换群头像", permission=SUPERUSER)

        @set_group_portrait.handle()
        async def handle_set_group_portrait(bot: Bot, event: Event):
            """
            处理换群头像命令
            :param bot: 机器人实例
            :param event: 事件对象
            """
            await set_group_portrait.send("读取信息中...")
            # 检查是否为群聊消息事件
            if not isinstance(event, GroupMessageEvent):
                await set_group_portrait.finish("此功能仅在群聊中可用")
                return

            # 获取群ID
            group_id = event.group_id
            await set_group_portrait.send(f"正在设置群 {group_id} 的头像...")

            # 检查是否有回复消息
            if not hasattr(event, 'reply') or not event.reply:
                await set_group_portrait.finish("请回复一条包含图片的消息来设置群头像")
                return

            reply_id = event.reply.message_id

            try:
                # 获取回复的消息内容
                reply_message = await bot.call_api('get_msg', message_id=reply_id)

                # 遍历消息内容，查找图片
                for content in reply_message['message']:
                    if content['type'] == 'image':
                        # 提取图片URL
                        portrait_image_path = content['data']['url']

                        await set_group_portrait.send(f"头像地址为: {portrait_image_path}")

                        # 调用OneBot V11协议的设置群头像API
                        # 注意：不同的OneBot实现可能API名称略有不同
                        await bot.call_api(
                            api="set_group_portrait",
                            group_id=group_id,
                            file=portrait_image_path
                        )
                        await set_group_portrait.finish("群头像更换成功！")

                # 如果回复消息中没有找到图片
                await set_group_portrait.finish("回复的消息中没有图片，无法设置群头像")

            except Exception as e:
                # 处理可能出现的异常情况
                await set_group_portrait.finish(f"设置群头像时出现错误: {str(e)}")
