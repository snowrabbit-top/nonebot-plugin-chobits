"""
音乐点歌功能
"""
import httpx
from nonebot import on_command
from nonebot.typing import T_State
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment


class Music:
    """
    音乐点歌功能主类
    整合了数据获取、处理和命令处理等功能
    """

    def __init__(self):
        """初始化音乐点歌功能"""
        self.headers = {"referer": "http://music.163.com"}
        self.cookies = {"appver": "2.0.2"}

    # 数据获取相关方法
    async def _search(self, song_name: str):
        """
        搜索接口，用于由歌曲名查找id
        :param song_name: 歌曲名称
        :return: 搜索结果
        """
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"http://music.163.com/api/search/get/web",
                data={"s": song_name, "limit": 5, "type": 1, "offset": 0},
                headers=self.headers,
                cookies=self.cookies
            )
        jsonified_r = r.json()
        if "result" not in jsonified_r:
            return None
        return jsonified_r

    async def _get_hot_comments(self, song_id: int):
        """
        获取热评
        :param song_id: 歌曲ID
        :return: 热评数据
        """
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"https://music.163.com/weapi/v1/resource/hotcomments/R_SO_4_{song_id}?csrf_token=",
                data={
                    # 不知道从哪毛来的key
                    "params": 'D33zyir4L/58v1qGPcIPjSee79KCzxBIBy507IYDB8EL7jEnp41aDIqpHBhowfQ6iT1Xoka8jD+0p44nRKNKUA0dv+n5RWPOO57dZLVrd+T1J/sNrTdzUhdHhoKRIgegVcXYjYu+CshdtCBe6WEJozBRlaHyLeJtGrABfMOEb4PqgI3h/uELC82S05NtewlbLZ3TOR/TIIhNV6hVTtqHDVHjkekrvEmJzT5pk1UY6r0=',
                    "encSecKey": '45c8bcb07e69c6b545d3045559bd300db897509b8720ee2b45a72bf2d3b216ddc77fb10daec4ca54b466f2da1ffac1e67e245fea9d842589dc402b92b262d3495b12165a721aed880bf09a0a99ff94c959d04e49085dc21c78bbbe8e3331827c0ef0035519e89f097511065643120cbc478f9c0af96400ba4649265781fc9079'
                },
                headers=self.headers,
                cookies=self.cookies
            )
        jsonified_r = r.json()
        if "hotComments" not in jsonified_r:
            return None
        return jsonified_r

    async def _get_song_info(self, song_id: int):
        """
        获取歌曲信息
        :param song_id: 歌曲ID
        :return: 歌曲详细信息
        """
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"http://music.163.com/api/song/detail/?id={song_id}&ids=%5B{song_id}%5D",
            )
        jsonified_r = r.json()
        if "songs" not in jsonified_r:
            return None
        return jsonified_r

    # 数据处理相关方法
    async def _get_song_ids(self, song_name: str, amount=5) -> list:
        """
        根据用户输入的songName 获取候选songId列表 [默认songId数量：5]
        :param song_name: 歌曲名称
        :param amount: 返回歌曲数量，默认为5
        :return: 歌曲ID列表
        """
        song_ids = list()
        r = await self._search(song_name=song_name)
        if r is None:
            return []
        id_range = amount if amount < len(
            r["result"]["songs"]) else len(r["result"]["songs"])
        for i in range(id_range):
            song_ids.append(r["result"]["songs"][i]["id"])
        return song_ids

    async def _get_song_comments(self, song_id: int, amount=3) -> dict:
        """
        根据传递的单一song_id，获取song_comments dict [默认评论数量上限：3]
        :param song_id: 歌曲ID
        :param amount: 评论数量，默认为3
        :return: 评论字典，键为用户名，值为评论内容
        """
        song_comments = dict()
        r = await self._get_hot_comments(song_id)
        if r is None:
            return {}
        comments_range = amount if amount < len(
            r['hotComments']) else len(r['hotComments'])
        for i in range(comments_range):
            song_comments[r['hotComments'][i]['user']
            ['nickname']] = r['hotComments'][i]['content']
        return song_comments

    async def _get_song_info_dict(self, song_id: int) -> dict:
        """
        根据传递的songId，获取歌曲名、歌手、专辑等信息，作为dict返回
        :param song_id: 歌曲ID
        :return: 包含歌曲信息的字典
        """
        song_info = dict()
        r = await self._get_song_info(song_id)
        if r is None:
            return {}
        song_info["songName"] = r["songs"][0]["name"]
        song_artists = list()
        for ars in r["songs"][0]["artists"]:
            song_artists.append(ars["name"])
        song_artists_str = "、".join(song_artists)
        song_info["songArtists"] = song_artists_str

        song_info["songAlbum"] = r["songs"][0]["album"]["name"]

        return song_info

    @staticmethod
    async def _merge_song_info(song_infos: list) -> str:
        """
        将歌曲信息list处理为字符串，供用户点歌
        :param song_infos: 歌曲信息列表
        :return: 格式化的歌曲信息字符串
        """
        song_info_message = "请输入欲点播歌曲的序号：\n"
        num_id = 0
        for song_info in song_infos:
            song_info_message += f"{num_id}："
            song_info_message += song_info["songName"]
            song_info_message += "-"
            song_info_message += song_info["songArtists"]
            song_info_message += " 专辑："
            song_info_message += song_info["songAlbum"]
            song_info_message += "\n"
            num_id += 1
        return song_info_message

    @staticmethod
    async def _merge_song_comments(song_comments: dict) -> str:
        """
        将歌曲评论字典格式化为字符串
        :param song_comments: 歌曲评论字典
        :return: 格式化的评论字符串
        """
        song_comments_message = '\n'.join(
            ['%s： %s' % (key, value) for (key, value) in song_comments.items()])
        return song_comments_message

    def command(self):
        """
        定义音乐点歌命令处理器
        """
        # 创建音乐点歌命令，触发词为"点歌"
        music_picker = on_command("音乐", aliases={"yy"})

        @music_picker.handle()
        async def handle_music_picker(state: T_State, args: Message = CommandArg()):
            """
            音乐点歌命令
            :param state: 状态对象
            :param args: 命令参数
            """
            args = str(args).split(" ")
            if len(args) > 0 and args[0]:
                state["song_name"] = args[0]
                # TODO: add config option for default choice
            if len(args) > 1 and args[1]:
                state["choice"] = args[1]

        @music_picker.got("song_name", prompt="请输入歌名:")
        async def got_music_picker_song_name(state: T_State):
            """
            处理音乐点歌命令的歌名输入
            :param state: 状态对象
            """
            song_name = state["song_name"]
            song_ids = await self._get_song_ids(song_name=song_name)
            if not song_ids:
                await music_picker.finish("没有找到这首歌，请重新点歌！")
            song_infos = list()
            for song_id in song_ids:
                song_info = await self._get_song_info_dict(song_id=song_id)
                if song_info:
                    song_infos.append(song_info)

            if not song_infos:
                await music_picker.finish("获取歌曲信息失败，请稍后再试！")

            song_infos = await self._merge_song_info(song_infos=song_infos)
            if not "choice" in state:
                await music_picker.send(song_infos)
            state["song_ids"] = song_ids

        @music_picker.got("choice")
        async def got_music_picker_choice(state: T_State):
            """
            处理音乐点歌命令的选择输入
            :param state: 状态对象
            """
            song_ids = state["song_ids"]
            choice = state["choice"]
            try:
                choice = int(str(choice))
            except ValueError:
                await music_picker.finish("选项只能是数字，请重新点歌！")
            if choice >= len(song_ids):
                await music_picker.finish("选项超出可选范围，请重新点歌！")

            selected_song_id = song_ids[choice]
            """
            {
                "type": "music",
                "data": {
                    "type": "custom",
                    "url": "http://baidu.com",
                    "audio": "http://baidu.com/1.mp3",
                    "title": "音乐标题",
                    "content": "发送时可选, 内容描述",
                    "image": "发送时可选, 图片 URL"
                }
            }
            """
            await music_picker.send(MessageSegment.music("163", int(selected_song_id)))

            song_comments = await self._get_song_comments(song_id=selected_song_id)
            if not song_comments:
                await music_picker.finish("点歌成功，暂无热评信息。")

            song_comments = await self._merge_song_comments(song_comments=song_comments)
            song_comments = "下面为您播送热评：\n" + song_comments

            await music_picker.finish(song_comments)
