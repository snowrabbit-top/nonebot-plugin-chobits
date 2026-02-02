"""
工具通用辅助方法
"""

import json
from collections.abc import Mapping

from nonebot.drivers import Request, Response


class ToolCommonMixin:
    """
    公共辅助方法
    """

    def _json(self, payload: object, status: int = 200) -> Response:
        """
        将 Python 对象序列化为 JSON 响应

        参数：
        - payload: object
          任意可 JSON 序列化对象
        - status: int
          HTTP 状态码，默认 200

        返回：
        - Response：JSON 字符串 + UTF-8 content-type
        """
        return Response(
            status,
            content=json.dumps(payload, ensure_ascii=False),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    def _query(self, request: Request, key: str) -> str | None:
        """
        从 Request 中读取 query 参数（兼容不同 driver 的 query 表达）

        参数：
        - request: Request
          nonebot driver 的 Request 抽象
        - key: str
          query 参数名

        返回：
        - str | None：找到则返回字符串；否则返回 None

        说明：
        - 某些 driver 的 request.url.query 是 Mapping
        - 某些是 MultiDict 风格（提供 .get）
        - 因此此处做了兼容处理
        """
        query = getattr(request.url, "query", None)
        if query is None:
            return None

        if isinstance(query, Mapping):
            v = query.get(key)
            return str(v) if v is not None else None

        get = getattr(query, "get", None)
        if callable(get):
            v = get(key)
            return str(v) if v is not None else None

        return None

    def _ws_text(self, data: object) -> str:
        """
        将 ws.receive() 的返回值稳妥地转成文本

        参数：
        - data: object
          ws.receive() 返回的任意对象（可能是 str/bytes/dict/...）

        返回：
        - str：可安全拼接/发送的字符串

        策略：
        - bytes：按 utf-8 解码（无法解码时替换异常字符）
        - str：原样返回
        - 其他：尽量 json.dumps，失败则 str()
        """
        if data is None:
            return ""
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return str(data)
