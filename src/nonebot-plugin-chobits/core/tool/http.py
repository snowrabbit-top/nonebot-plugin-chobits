"""
HTTP 接口相关处理
"""

import json
import inspect
import os
import shutil
from urllib.parse import parse_qs
from collections.abc import Sequence
from pathlib import Path

from nonebot import get_bots, get_driver
from nonebot.drivers import Request, Response

from ...unit.sqlite import SQLiteDatabase


class ToolHTTPMixin:
    """
    HTTP handlers
    """

    HTTP_ROUTES: Sequence[tuple[str, str, str]] = (
        # (HTTP_METHOD, PATH, ROUTE_NAME)
        ("GET", "/chobits/ping", "chobits_http_ping"),
        ("GET", "/chobits/status", "chobits_http_status"),
        ("GET", "/chobits/command", "chobits_http_command"),
        ("GET", "/chobits/page", "chobits_http_page"),
        ("GET", "/chobits/static", "chobits_http_static"),
        ("GET", "/chobits/home", "chobits_http_home"),
        ("POST", "/chobits/login", "chobits_http_login"),
    )

    async def http_ping(self, _: Request) -> Response:
        """
        HTTP 健康检查接口

        路由：
        - GET /chobits/ping

        用途：
        - 用于探测服务是否存活、路由是否成功注册

        参数：
        - _: Request（未使用）

        返回：
        - Response：200 + "pong"
        """
        return Response(200, content="pong")

    async def http_status(self, _: Request) -> Response:
        """
        HTTP 状态查询接口

        路由：
        - GET /chobits/status

        用途：
        - 返回当前 driver 类型、已连接 bot 列表等信息

        参数：
        - _: Request（未使用）

        返回：
        - Response：200 + JSON
          {
            "ok": true,
            "driver_type": "...",
            "bots": [...]
          }
        """
        payload = {
            "ok": True,
            "driver_type": getattr(get_driver(), "type", None),
            "bots": list(get_bots().keys()),
        }
        return self._json(payload)

    async def http_command(self, request: Request) -> Response:
        """
        HTTP 命令执行入口（示例占位）

        路由：
        - GET /chobits/command?cmd=xxx

        用途：
        - 作为“管理命令”统一入口（目前示例只是回显）
        - 真实使用请务必加鉴权/白名单/签名校验等安全措施

        参数：
        - request: Request
          用于读取 query 参数 cmd

        返回：
        - Response：
          - 400：缺少 cmd 参数
          - 200：返回 {"ok": True, "cmd": "...", "result": "..."}
        """
        cmd = self._query(request, "cmd")
        if not cmd:
            return self._json({"ok": False, "error": "missing query param: cmd"}, status=400)

        # TODO: 替换为你的真实逻辑（强烈建议加鉴权/白名单）
        return self._json({"ok": True, "cmd": cmd, "result": f"received: {cmd}"})

    async def http_page(self, request: Request) -> Response:
        """
        页面服务入口

        路由：
        - GET /chobits/page?name=xxx

        用途：
        - 返回指定的 HTML 页面
        """
        name = self._query(request, "name") or "login"
        template_file = self._resolve_template_file("html", name)
        if template_file is None:
            return self._json({"ok": False, "error": "page not found"}, status=404)
        return self._file_response(template_file)

    async def http_static(self, request: Request) -> Response:
        """
        静态资源服务入口

        路由：
        - GET /chobits/static?path=css/common.css
        """
        path_value = self._query(request, "path")
        if not path_value:
            return self._json({"ok": False, "error": "missing query param: path"}, status=400)
        template_file = self._resolve_template_file("static", path_value)
        if template_file is None:
            return self._json({"ok": False, "error": "asset not found"}, status=404)
        return self._file_response(template_file)

    async def http_login(self, request: Request) -> Response:
        """
        登录接口

        路由：
        - POST /chobits/login

        用途：
        - 校验系统配置中的 admin-user/admin-password

        参数：
        - request: Request
          JSON body: {account, password}

        返回：
        - Response:
          - 200: {"status": "success"}
          - 400: {"status": "error", "message": "..."}
        """
        payload = await self._read_json_body(request)
        account = str(payload.get("account", "")).strip()
        password = str(payload.get("password", "")).strip()

        if not account or not password:
            return self._json({"status": "error", "message": "账号或密码不能为空"}, status=400)

        current_file_dir = Path(__file__).parent
        parent_dir = current_file_dir.parent.parent
        database_file = parent_dir / "database" / "database.db"
        sqlite_db = SQLiteDatabase(database=database_file)

        try:
            conn = sqlite_db.create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_info';")
            table_exists = cursor.fetchone() is not None
            conn.close()
        except Exception:
            return self._json({"status": "error", "message": "系统配置读取失败"}, status=500)

        if not table_exists:
            return self._json({"status": "error", "message": "系统配置未初始化"}, status=400)

        admin_user = sqlite_db.find_info(table="system_info", where={"key": "admin-user"}) or {}
        admin_password = sqlite_db.find_info(table="system_info", where={"key": "admin-password"}) or {}
        expected_user = str(admin_user.get("value", "")).strip()
        expected_password = str(admin_password.get("value", "")).strip()

        if account == expected_user and password == expected_password:
            return self._json({"status": "success"})

        return self._json({"status": "error", "message": "账号或密码错误"}, status=400)

    async def http_home(self, _: Request) -> Response:
        """
        首页数据接口

        路由：
        - GET /chobits/home

        返回：
        - Response:
          - 200: {"status": "success", "data": {...}}
        """
        cpu_usage = self._get_cpu_usage()
        memory_usage = self._get_memory_usage()
        disk_usage = self._get_disk_usage()
        metrics = self._get_home_metrics()
        activities = self._get_home_activities()

        payload = {
            "status": "success",
            "data": {
                "system_status": {
                    "server": "online",
                    "cpu_usage": cpu_usage,
                    "memory": memory_usage,
                    "disk": disk_usage,
                },
                "metrics": metrics,
                "activities": activities,
            },
        }
        return self._json(payload)

    async def _read_json_body(self, request: Request) -> dict:
        """
        尝试从请求中读取 JSON body
        """
        json_attr = getattr(request, "json", None)
        if json_attr is not None:
            try:
                json_payload = await self._maybe_await(json_attr)
                if isinstance(json_payload, dict):
                    return json_payload
            except Exception:
                pass

        form_attr = getattr(request, "form", None)
        if callable(form_attr):
            try:
                form_data = await self._maybe_await(form_attr)
                form_payload = self._normalize_form_data(form_data)
                if form_payload:
                    return form_payload
            except Exception:
                pass

        body = None
        body_attr = getattr(request, "body", None)
        if body_attr is not None and callable(body_attr):
            try:
                body = await self._maybe_await(body_attr)
            except Exception:
                body = None
        elif isinstance(body_attr, (bytes, bytearray, str)):
            body = body_attr

        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", errors="ignore")
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            payload = self._parse_urlencoded(body)
            return payload

    async def _maybe_await(self, value: object) -> object:
        if callable(value):
            value = value()
        if inspect.isawaitable(value):
            return await value
        return value

    def _get_cpu_usage(self) -> float | None:
        try:
            load_1, _, _ = os.getloadavg()
            cpu_count = os.cpu_count() or 1
            usage = min(load_1 / cpu_count * 100, 100.0)
            return round(usage, 1)
        except Exception:
            return None

    def _get_memory_usage(self) -> dict | None:
        meminfo = Path("/proc/meminfo")
        if not meminfo.exists():
            return None
        try:
            info = {}
            for line in meminfo.read_text(encoding="utf-8").splitlines():
                parts = line.split(":")
                if len(parts) != 2:
                    continue
                key = parts[0].strip()
                value = parts[1].strip().split()[0]
                if value.isdigit():
                    info[key] = int(value)
            total = info.get("MemTotal")
            available = info.get("MemAvailable", info.get("MemFree"))
            if not total or available is None:
                return None
            used = total - available
            percent = round(used / total * 100, 1)
            return {
                "used_gb": round(used / 1024 / 1024, 1),
                "total_gb": round(total / 1024 / 1024, 1),
                "percent": percent,
            }
        except Exception:
            return None

    def _get_disk_usage(self) -> dict | None:
        try:
            total, used, _ = shutil.disk_usage("/")
            if total == 0:
                return None
            percent = round(used / total * 100, 1)
            return {
                "used_gb": round(used / 1024 / 1024 / 1024, 1),
                "total_gb": round(total / 1024 / 1024 / 1024, 1),
                "percent": percent,
            }
        except Exception:
            return None

    def _get_home_metrics(self) -> dict:
        return {
            "users": 0,
            "roles": 0,
            "commands": 0,
            "active_today": 0,
            "alerts": 0,
            "tasks": 0,
        }

    def _get_home_activities(self) -> list[dict]:
        return [
            {
                "icon": "👤",
                "text": "用户 admin 从 192.168.1.100 登录系统",
                "time": "2分钟前",
            },
            {
                "icon": "🎭",
                "text": "管理员修改了 \"超级管理员\" 角色权限",
                "time": "15分钟前",
            },
            {
                "icon": "💬",
                "text": "新增命令 \"/system/restart\" 到命令库",
                "time": "1小时前",
            },
            {
                "icon": "⚠️",
                "text": "磁盘使用率超过 65%，建议清理空间",
                "time": "2小时前",
            },
        ]

    def _normalize_form_data(self, form_data: object) -> dict:
        if form_data is None:
            return {}
        items = getattr(form_data, "items", None)
        if not callable(items):
            return {}
        normalized: dict[str, object] = {}
        for key, value in items():
            if isinstance(value, (list, tuple)):
                normalized[str(key)] = value[0] if value else ""
            else:
                normalized[str(key)] = value
        if normalized:
            return normalized
        getlist = getattr(form_data, "getlist", None)
        if callable(getlist):
            keys = getattr(form_data, "keys", None)
            if callable(keys):
                for key in keys():
                    values = getlist(key)
                    normalized[str(key)] = values[0] if values else ""
        return normalized

    def _parse_urlencoded(self, body: str) -> dict:
        if not body:
            return {}
        parsed = parse_qs(body, keep_blank_values=True)
        if not parsed:
            return {}
        return {key: value[0] if value else "" for key, value in parsed.items()}

    def _resolve_template_file(self, mode: str, name: str) -> Path | None:
        templates_dir = Path(__file__).parent / "templates"
        safe_name = name.strip().lstrip("/")
        if mode == "html":
            allowed_pages = {
                "login",
                "home",
                "monitor",
                "roles",
                "settings",
                "users",
                "functions",
            }
            page_key = safe_name.replace(".html", "")
            if page_key not in allowed_pages:
                return None
            candidate = templates_dir / f"{page_key}.html"
            return candidate if candidate.exists() else None

        if mode == "static":
            candidate = (templates_dir / safe_name).resolve()
            if templates_dir.resolve() not in candidate.parents:
                return None
            if candidate.suffix not in {".css", ".js"}:
                return None
            return candidate if candidate.exists() else None
        return None

    def _file_response(self, path: Path) -> Response:
        content = path.read_text(encoding="utf-8")
        return Response(
            200,
            content=content,
            headers={"Content-Type": self._content_type(path)},
        )

    def _content_type(self, path: Path) -> str:
        if path.suffix == ".css":
            return "text/css; charset=utf-8"
        if path.suffix == ".js":
            return "application/javascript; charset=utf-8"
        return "text/html; charset=utf-8"
