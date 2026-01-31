"""
机器人测试命令类
功能:
    放置一些命令代码,即时测试
"""
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.internal.params import ArgPlainText
from nonebot.adapters.onebot.v11 import Message, Bot, Event, MessageSegment


class Test:

    def command(self):
        """
        命令列表
        """
        test = on_command("test", permission=SUPERUSER)

        @test.handle()
        async def handle_function():
            await test.finish("test")

        weather = on_command("天气")

        @weather.handle()
        async def handle_function(args: Message = CommandArg()):
            if location := args.extract_plain_text():
                await weather.finish(f"今天{location}的天气是...")

        @weather.got("location", prompt="请输入地名")
        async def got_location(location: str = ArgPlainText()):
            if location not in ["北京", "上海", "广州", "深圳"]:
                await weather.reject(f"你想查询的城市 {location} 暂不支持，请重新输入！")
            await weather.finish(f"今天{location}的天气是...")

        # 信息伪造
        fake_info = on_command('信息伪造')

        @fake_info.handle()
        async def fake_info_handle(bot: Bot, event: Event):
            """
            信息伪造
            :param bot:
            :param event:
            :return:
            """
            """
            [
              {
                "type": "node",
                "data": {
                  "name": "消息发送者A",
                  "uin": "10086",
                  "content": [
                    {
                      "type": "text",
                      "data": {
                        "text": "测试消息1"
                      }
                    }
                  ]
                }
              },
              {
                "type": "node",
                "data": {
                  "name": "消息发送者B",
                  "uin": "10087",
                  "content": "测试消息2"
                }
              }
            ]
            """
            message = Message(
                [
                    MessageSegment.node_custom(user_id=10086, nickname="消息发送者A", content=Message([MessageSegment.text("test")])),
                    MessageSegment.node_custom(
                        user_id=10087,
                        nickname="消息发送者B",
                        content=Message(
                            [
                                MessageSegment.node_custom(user_id=10086, nickname="消息发送者A", content=Message([MessageSegment.text("test")])),
                                MessageSegment.node_custom(user_id=10087, nickname="消息发送者B", content=Message(
                                    [
                                        MessageSegment.text("test"),
                                    ]
                                )),
                            ]
                        )
                    ),
                ]
            )
            print(MessageSegment.text("test"))
            print(MessageSegment.node_custom(user_id=10086, nickname="消息发送者A", content=Message([MessageSegment.text("test")])))
            res_id = await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=[
                {
                    "type": "node",
                    "data": {
                        "user_id": "10086",
                        "nickname": "消息发送者A",
                        "content": [
                            {
                                "type": "text",
                                "data": {
                                    "text": "test",
                                    "summary": "您的猫娘已送到,请注意查收~"
                                }
                            }
                        ],
                        "summary": "您的猫娘已送到,请注意查收~"
                    },
                },
                {
                    "type": "node",
                    "data": {
                        "user_id": "10087",
                        "nickname": "消息发送者A",
                        "content": [
                            {
                                "type": "text",
                                "data": {
                                    "text": "test"
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "node",
                    "data": {
                        "user_id": "10087",
                        "nickname": "消息发送者A",
                        "content": [
                            {
                                "type": "node",
                                "data": {
                                    "user_id": "10086",
                                    "nickname": "消息发送者A",
                                    "content": [
                                        {
                                            "type": "text",
                                            "data": {
                                                "text": "test",
                                                "summary": "您的猫娘已送到,请注意查收~",
                                                "title": "您的猫娘已送到,请注意查收~",
                                            }
                                        }
                                    ],
                                },
                            },
                            {
                                "type": "node",
                                "data": {
                                    "user_id": "10087",
                                    "nickname": "消息发送者A",
                                    "content": [
                                        {
                                            "type": "text",
                                            "data": {
                                                "text": "test"
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "type": "node",
                                "data": {
                                    "user_id": "10087",
                                    "nickname": "消息发送者A",
                                    "content": [
                                        {
                                            "type": "image",
                                            "data": {
                                                "summary": "您的猫娘已送到,请注意查收~",
                                                "subType": 1,
                                                "file": "https://p.qpic.cn/qq_expression/1018784768/1018784768_0_0_0_4355FC3B0B4DDB1369C826E5FF69325B_0_0/0"
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "type": "node",
                                "data": {
                                    "id": "121221739",
                                }
                            }
                        ]
                    }
                }
            ])
            print(res_id.get("message_id"))
            print(res_id.get("res_id"))
            print(res_id.get("forward_id"))

            await fake_info.send(res_id.get("message_id"))
            await fake_info.send(res_id.get("res_id"))
            await fake_info.finish(res_id.get("forward_id"))
