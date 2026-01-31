"""
完美许愿器
https://wish.closeai.moe/
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.params import CommandArg
import httpx
import json


class Wish:

    def command(self):
        """
        开始监听调用完美许愿器命令
        """
        init_wish = on_command(cmd="许愿", aliases={"xy"})

        # 定义命令处理函数装饰器
        @init_wish.handle()
        # 异步处理函数，接收bot实例和事件对象
        async def handle_init_system_info(bot: Bot, event: Event, args: Message = CommandArg()) -> None:
            """
            处理命令
            """
            await init_wish.send("收到你的愿望,正在处理中...")

            url = "https://wish.closeai.moe/api/validateWish"

            payload = {
                "wish": args.extract_plain_text(),
            }

            headers = {
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
                'Accept-Encoding': "gzip, deflate, br, zstd",
                'Content-Type': "application/json",
                'pragma': "no-cache",
                'cache-control': "no-cache",
                'sec-ch-ua-platform': "\"Windows\"",
                'accept-language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Microsoft Edge\";v=\"144\"",
                'sec-ch-ua-mobile': "?0",
                'priority': "u=1, i",
                'origin': "https://wish.closeai.moe",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty"
            }

            # 使用httpx发送异步请求
            async with httpx.AsyncClient(timeout=httpx.Timeout(None), verify=False) as client:
                try:
                    response = await client.post(url, headers=headers, json=payload)

                    # 打印响应信息
                    print(f"Status Code: {response.status_code}")
                    print(f"Response Headers: {dict(response.headers)}")
                    print(f"Response Content: {response.text}")

                    # 解析响应JSON
                    response_data = response.json()

                    if response_data.get("status") == "success":
                        result = response_data.get("result", {})
                        confirmed_wish = result.get("confirmed_wish", "无")
                        scenario = result.get("scenario", "无")

                        # 格式化响应消息
                        formatted_response = f"许愿成功！\r\n\r\n确认的愿望: {confirmed_wish}\r\n\r\n实现场景: {scenario}"
                        await init_wish.finish(formatted_response)
                    else:
                        await init_wish.finish(f"许愿失败: {response}")

                except httpx.RequestError as e:
                    print(f"请求错误: {e}")
                    await init_wish.finish(f"许愿失败: {str(e)}")
                except httpx.HTTPStatusError as e:
                    print(f"HTTP状态错误: {e}")
                    await init_wish.finish(f"许愿失败: 状态码 {e.response.status_code}")
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    await init_wish.finish(f"许愿失败: 响应格式错误")
