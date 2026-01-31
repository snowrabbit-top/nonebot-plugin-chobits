"""
设置账号信息
"""
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, MessageEvent, Message
from nonebot.internal.params import ArgPlainText


class SetQQProfile:

    async def _get_current_nickname(self, bot: Bot):
        """
        获取当前机器人的昵称
        :param bot: 机器人实例
        :return: 当前昵称
        """
        self_info = await bot.call_api(
            api="get_stranger_info",
            user_id=bot.self_id
        )
        return self_info['nickname']

    def _convert_gender_to_english(self, gender_input: str) -> str:
        """
        将汉字性别转换为英文参数
        :param gender_input: 输入的性别（汉字）
        :return: 对应的英文参数
        """
        gender_mapping = {
            "男": "male",
            "男性": "male",
            "女": "female",
            "女性": "female",
            "未知": "unknown",
            "保密": "unknown"
        }
        return gender_mapping.get(gender_input.strip(), "unknown")

    async def _process_profile_update(self, bot: Bot, key: str, value: str, current_nickname: str = None):
        """
        处理账号信息更新的私有方法
        :param bot: 机器人实例
        :param key: 要修改的字段名（昵称、签名、性别）
        :param value: 字段的新值
        :param current_nickname: 当前昵称（用于确保在修改其他字段时不丢失昵称）
        """
        # 根据key的值只传递相应的参数，同时确保昵称不会丢失
        if key == "昵称":
            await bot.call_api(
                api="set_qq_profile",
                nickname=value
            )
        elif key == "签名":
            # 只在修改签名时获取当前昵称
            if current_nickname is None:
                current_nickname = await self._get_current_nickname(bot)
            await bot.call_api(
                api="set_qq_profile",
                nickname=current_nickname,  # 保持当前昵称
                personal_note=value
            )
        elif key == "性别":
            # 将汉字性别转换为英文参数
            english_gender = self._convert_gender_to_english(value)
            # 只在修改性别时获取当前昵称
            if current_nickname is None:
                current_nickname = await self._get_current_nickname(bot)
            await bot.call_api(
                api="set_qq_profile",
                nickname=current_nickname,  # 保持当前昵称
                sex=english_gender
            )

    def _parse_input(self, input_str: str):
        """
        解析输入字符串，将其按空格拆分为key和value
        :param input_str: 输入字符串
        :return: tuple (key, value)
        """
        parts = input_str.split(" ", 1)  # 最多分割成2个部分
        if len(parts) >= 2:
            key = parts[0]
            value = parts[1]
        else:
            key = parts[0] if parts else ""
            value = ""
        return key, value

    async def _validate_and_update_profile(self, bot: Bot, set_qq_profile, key: str, value: str):
        """
        验证输入并更新账号信息的私有方法
        :param bot: 机器人实例
        :param set_qq_profile: 命令处理器
        :param key: 要修改的字段名
        :param value: 字段的新值
        """
        if key == "" or value == "":
            await set_qq_profile.reject(f"请提示重新输入！")

        if key not in ["昵称", "签名", "性别"]:
            await set_qq_profile.reject(f"你想修改的信息 {key} 暂不支持修改，请重新输入！")

        # 只有在修改非昵称字段时才获取当前昵称
        current_nickname = None
        if key != "昵称":
            current_nickname = await self._get_current_nickname(bot)

        # 处理账号信息更新
        await self._process_profile_update(bot, key, value, current_nickname)

        await set_qq_profile.send(f"{key} 已设置为 {value}")

    def command(self):
        """
        定义设置账号信息命令处理器
        """
        # 创建设置账号信息命令，触发词为"设置账号信息"
        set_qq_profile = on_command(cmd="设置账号信息", permission=SUPERUSER)

        @set_qq_profile.handle()
        async def handle_set_qq_profile(bot: Bot, event: Event, args: Message = CommandArg()):
            """
            设置账号信息命令
            :param bot: 机器人实例
            :param event: 事件对象
            :param args:
            """
            if args.extract_plain_text().strip() != "":
                # 如果输入完成，则直接输出修改完成并结束方法
                if args.extract_plain_text().strip() == "完成":
                    await set_qq_profile.finish("修改已完成！")

                # 解析输入
                input_text = args.extract_plain_text()
                key, value = self._parse_input(input_text)

                # 验证输入并更新账号信息
                await self._validate_and_update_profile(bot, set_qq_profile, key, value)

        @set_qq_profile.got("info", prompt="""请输入想要更改的信息:
称昵 XXX
签名 XXXXXX
性别 XX""")
        async def got_set_qq_profile(bot: Bot, event: Event, info: str = ArgPlainText()):
            """
            处理设置账号信息命令的多轮对话
            :param event:
            :param bot:
            :param info: 账号信息
            """
            # 如果输入完成，则直接输出修改完成并结束方法
            if info.strip() == "完成":
                await set_qq_profile.finish("修改已完成！")

            # 解析输入
            key, value = self._parse_input(info)

            # 验证输入并更新账号信息
            await self._validate_and_update_profile(bot, set_qq_profile, key, value)

            # 继续提示用户输入更多信息，直到用户输入"完成"
            await set_qq_profile.reject("""请输入想要更改的信息:
称昵 XXX
签名 XXXXXX
性别 XX
输入"完成"结束修改""")
