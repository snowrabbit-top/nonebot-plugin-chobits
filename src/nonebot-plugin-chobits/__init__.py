from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from .core import LifeCycle
from .core import Settings
from .core import Test
from .core import Wish
from .core import SetQQAvatar
from .core import SetGroupPortrait
from .core import SetQQProfile
from .core import FetchCustomFace
from .core import Music
# from .core import RandomImage

# from .core import HA

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-chobits",
    description="小叽，在都市传说中流传的可以不依靠程式就能活动和产生情感的Chobits系列人型电脑中的其中一台。",
    usage="查看菜单 ^help",
    config=Config,
)

config = get_plugin_config(Config)

# 生命周期
LifeCycle().command()
# 设置
Settings().command()
# 测试
Test().command()
# 愿望
Wish().command()
# 设置QQ头像
SetQQAvatar().command()
# 设置群头像
SetGroupPortrait().command()
# 设置QQ账户信息
SetQQProfile().command()
# 获取自定义表情
FetchCustomFace().command()
# 音乐点歌
Music().command()
# 随机图片
# RandomImage().command()

# 哈
# HA().command()
