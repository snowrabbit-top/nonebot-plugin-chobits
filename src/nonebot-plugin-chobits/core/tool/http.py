"""
HTTP 接口相关处理
"""

import json
import inspect
import os
import random
import shutil
from datetime import datetime
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
        ("GET", "/chobits/monitor", "chobits_http_monitor"),
        ("GET", "/chobits/settings", "chobits_http_settings"),
        ("GET", "/chobits/users", "chobits_http_users"),
        ("GET", "/chobits/roles", "chobits_http_roles"),
        ("GET", "/chobits/functions", "chobits_http_functions"),
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
            return self._json({"status": "success", "data": {"account": account}})

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

    async def http_monitor(self, _: Request) -> Response:
        """
        系统监控数据接口

        路由：
        - GET /chobits/monitor
        """
        payload = {
            "status": "success",
            "data": self._get_monitor_snapshot(),
        }
        return self._json(payload)

    async def http_settings(self, _: Request) -> Response:
        """
        系统设置数据接口

        路由：
        - GET /chobits/settings
        """
        payload = {
            "status": "success",
            "data": {
                "items": self._get_settings_list(),
            },
        }
        return self._json(payload)

    async def http_users(self, _: Request) -> Response:
        """
        用户管理数据接口

        路由：
        - GET /chobits/users
        """
        payload = {
            "status": "success",
            "data": {
                "items": self._get_users_list(),
            },
        }
        return self._json(payload)

    async def http_roles(self, _: Request) -> Response:
        """
        角色管理数据接口

        路由：
        - GET /chobits/roles
        """
        payload = {
            "status": "success",
            "data": {
                "items": self._get_roles_list(),
            },
        }
        return self._json(payload)

    async def http_functions(self, _: Request) -> Response:
        """
        命令管理数据接口

        路由：
        - GET /chobits/functions
        """
        payload = {
            "status": "success",
            "data": {
                "items": self._get_functions_list(),
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
        content = None
        content_attr = getattr(request, "content", None)
        if content_attr is not None:
            try:
                content = await self._maybe_await(content_attr)
            except Exception:
                content = None
        data_attr = getattr(request, "data", None)
        if data_attr is not None:
            try:
                content = await self._maybe_await(data_attr)
            except Exception:
                content = content
        body_attr = getattr(request, "body", None)
        if body_attr is not None and callable(body_attr):
            try:
                body = await self._maybe_await(body_attr)
            except Exception:
                body = None
        elif isinstance(body_attr, (bytes, bytearray, str)):
            body = body_attr
        if body is None and content is not None:
            body = content

        if isinstance(body, dict):
            return body
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
        users = self._get_users_list()
        roles = self._get_roles_list()
        functions = self._get_functions_list()
        return {
            "users": len(users),
            "roles": len(roles),
            "commands": len(functions),
            "active_today": 12,
            "alerts": 3,
            "tasks": 4,
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

    def _get_monitor_snapshot(self) -> dict:
        cpu_usage = self._get_cpu_usage()
        memory_usage = self._get_memory_usage() or {}
        disk_usage = self._get_disk_usage() or {}
        if cpu_usage is None:
            cpu_usage = round(random.uniform(12, 38), 1)
        cpu_series = self._build_series(cpu_usage, 60, 2, 98)
        net_in_series = self._build_series(random.uniform(8, 18), 60, 0.5, 80)
        net_out_series = self._build_series(random.uniform(5, 12), 60, 0.5, 80)
        processes = [
            {"pid": 1842, "name": "chobits-api", "cpu": 12.4, "mem": 4.8, "user": "root"},
            {"pid": 2211, "name": "postgres", "cpu": 6.2, "mem": 8.3, "user": "postgres"},
            {"pid": 987, "name": "redis-server", "cpu": 2.8, "mem": 2.5, "user": "redis"},
            {"pid": 3021, "name": "nginx", "cpu": 1.4, "mem": 1.1, "user": "www-data"},
            {"pid": 4112, "name": "node-exporter", "cpu": 0.6, "mem": 0.4, "user": "nobody"},
        ]
        services = [
            {"name": "chobits-api", "ok": True, "latency": 22, "note": "HTTP 200 /health"},
            {"name": "postgres", "ok": True, "latency": 4, "note": "连接正常"},
            {"name": "redis", "ok": True, "latency": 2, "note": "PONG"},
            {"name": "prometheus", "ok": True, "latency": 35, "note": "抓取正常"},
            {"name": "grafana", "ok": True, "latency": 48, "note": "登录可用"},
        ]
        return {
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu": {"percent": cpu_usage, "cores": os.cpu_count() or 1},
            "memory": memory_usage,
            "disk": disk_usage,
            "network": {
                "in_now": round(net_in_series[-1], 1),
                "out_now": round(net_out_series[-1], 1),
            },
            "series": {
                "cpu": cpu_series,
                "net_in": net_in_series,
                "net_out": net_out_series,
            },
            "processes": processes,
            "services": services,
        }

    def _build_series(self, base: float, count: int, min_value: float, max_value: float) -> list[float]:
        series = []
        value = base
        for _ in range(count):
            jitter = random.uniform(-4, 4)
            value = max(min_value, min(max_value, value + jitter))
            series.append(round(value, 1))
        return series

    def _get_settings_list(self) -> list[dict]:
        return [
            {
                "id": 1,
                "key": "bot_name",
                "value": "Chobits",
                "description": "机器人名称",
                "status": "normal",
                "created_time": "2023-01-15 10:35:22",
                "updated_time": "2023-12-01 14:22:45",
                "deleted_time": None,
            },
            {
                "id": 2,
                "key": "admin_qq",
                "value": "123456789",
                "description": "管理员QQ号",
                "status": "normal",
                "created_time": "2023-01-15 10:36:15",
                "updated_time": "2023-11-20 09:18:33",
                "deleted_time": None,
            },
            {
                "id": 3,
                "key": "auto_reply",
                "value": "true",
                "description": "是否启用自动回复功能",
                "status": "normal",
                "created_time": "2023-02-10 08:25:44",
                "updated_time": "2023-12-10 11:42:18",
                "deleted_time": None,
            },
            {
                "id": 4,
                "key": "max_users",
                "value": "1000",
                "description": "最大用户数量限制",
                "status": "normal",
                "created_time": "2023-02-10 08:26:30",
                "updated_time": "2023-10-28 16:37:52",
                "deleted_time": None,
            },
            {
                "id": 5,
                "key": "log_level",
                "value": "info",
                "description": "日志级别 (debug/info/warn/error)",
                "status": "normal",
                "created_time": "2023-03-01 12:15:27",
                "updated_time": "2023-09-14 08:55:19",
                "deleted_time": None,
            },
            {
                "id": 6,
                "key": "backup_interval",
                "value": "86400",
                "description": "备份间隔时间（秒），默认24小时",
                "status": "disable",
                "created_time": "2023-04-18 21:35:11",
                "updated_time": "2023-12-15 13:28:44",
                "deleted_time": None,
            },
            {
                "id": 7,
                "key": "api_timeout",
                "value": "30",
                "description": "API请求超时时间（秒）",
                "status": "normal",
                "created_time": "2023-05-28 14:50:38",
                "updated_time": "2023-11-30 17:12:05",
                "deleted_time": None,
            },
            {
                "id": 8,
                "key": "maintenance_mode",
                "value": "false",
                "description": "维护模式开关",
                "status": "normal",
                "created_time": "2023-05-28 14:51:22",
                "updated_time": "2023-08-22 10:44:37",
                "deleted_time": None,
            },
            {
                "id": 9,
                "key": "cache_ttl",
                "value": "3600",
                "description": "缓存过期时间（秒）",
                "status": "normal",
                "created_time": "2023-06-15 09:30:45",
                "updated_time": "2023-12-05 15:20:18",
                "deleted_time": None,
            },
            {
                "id": 10,
                "key": "webhook_url",
                "value": "https://example.com/webhook",
                "description": "Webhook回调地址",
                "status": "disable",
                "created_time": "2023-07-22 16:45:33",
                "updated_time": "2023-11-18 12:33:27",
                "deleted_time": None,
            },
        ]

    def _get_users_list(self) -> list[dict]:
        return [
            {
                "id": 1,
                "qq": "123456789",
                "avatar": None,
                "register_time": "2023-01-15 10:30:00",
                "status": "normal",
                "token": "abc123def456ghi789jkl012mno345p",
                "created_time": "2023-01-15 10:35:22",
                "updated_time": "2023-12-01 14:22:45",
                "deleted_time": None,
            },
            {
                "id": 2,
                "qq": "987654321",
                "avatar": "https://q1.qlogo.cn/g?b=qq&nk=987654321&s=100",
                "register_time": "2022-08-22 15:45:00",
                "status": "ban",
                "token": "xyz987uvw654rst321qpo098nml765k",
                "created_time": "2022-08-22 16:00:12",
                "updated_time": "2023-11-15 09:18:33",
                "deleted_time": None,
            },
            {
                "id": 3,
                "qq": "111222333",
                "avatar": "https://q1.qlogo.cn/g?b=qq&nk=111222333&s=100",
                "register_time": "2023-05-10 08:20:00",
                "status": "normal",
                "token": "mno345pqr678stu901vwx234yz567ab",
                "created_time": "2023-05-10 08:25:44",
                "updated_time": "2023-12-10 11:42:18",
                "deleted_time": None,
            },
            {
                "id": 4,
                "qq": "444555666",
                "avatar": None,
                "register_time": "2023-03-05 19:15:00",
                "status": "normal",
                "token": "cde890fgh123ijk456lmn789opq012r",
                "created_time": "2023-03-05 19:20:33",
                "updated_time": "2023-10-28 16:37:52",
                "deleted_time": None,
            },
            {
                "id": 5,
                "qq": "777888999",
                "avatar": "https://q1.qlogo.cn/g?b=qq&nk=777888999&s=100",
                "register_time": "2022-12-01 12:10:00",
                "status": "ban",
                "token": "stu345vwx678yz901abc234def567g",
                "created_time": "2022-12-01 12:15:27",
                "updated_time": "2023-09-14 08:55:19",
                "deleted_time": None,
            },
            {
                "id": 6,
                "qq": "123123123",
                "avatar": None,
                "register_time": "2023-07-18 21:30:00",
                "status": "normal",
                "token": "hij890klm123nop456qrs789tuv012w",
                "created_time": "2023-07-18 21:35:11",
                "updated_time": "2023-12-15 13:28:44",
                "deleted_time": None,
            },
            {
                "id": 7,
                "qq": "456456456",
                "avatar": "https://q1.qlogo.cn/g?b=qq&nk=456456456&s=100",
                "register_time": "2023-02-28 14:45:00",
                "status": "normal",
                "token": "xyz345abc678def901ghi234jkl567m",
                "created_time": "2023-02-28 14:50:38",
                "updated_time": "2023-11-30 17:12:05",
                "deleted_time": None,
            },
            {
                "id": 8,
                "qq": "789789789",
                "avatar": None,
                "register_time": "2022-11-11 09:20:00",
                "status": "ban",
                "token": "nop890qrs123tuv456wxy789zab012c",
                "created_time": "2022-11-11 09:25:19",
                "updated_time": "2023-08-22 10:44:37",
                "deleted_time": None,
            },
        ]

    def _get_roles_list(self) -> list[dict]:
        return [
            {
                "id": 1,
                "name": "超级管理员",
                "permissions": "user.*, role.*, command.*, setting.*, file.*, log.*",
                "status": "normal",
                "created_time": "2023-01-15 10:35:22",
                "updated_time": "2023-12-01 14:22:45",
                "deleted_time": None,
            },
            {
                "id": 2,
                "name": "管理员",
                "permissions": "user.view, user.edit, command.*, setting.view, log.view",
                "status": "normal",
                "created_time": "2023-01-15 10:36:15",
                "updated_time": "2023-11-20 09:18:33",
                "deleted_time": None,
            },
            {
                "id": 3,
                "name": "审核员",
                "permissions": "user.view, command.view, log.*",
                "status": "normal",
                "created_time": "2023-02-10 08:25:44",
                "updated_time": "2023-12-10 11:42:18",
                "deleted_time": None,
            },
            {
                "id": 4,
                "name": "普通用户",
                "permissions": "command.view, log.view",
                "status": "normal",
                "created_time": "2023-02-10 08:26:30",
                "updated_time": "2023-10-28 16:37:52",
                "deleted_time": None,
            },
            {
                "id": 5,
                "name": "访客",
                "permissions": "command.view",
                "status": "disable",
                "created_time": "2023-03-01 12:15:27",
                "updated_time": "2023-09-14 08:55:19",
                "deleted_time": None,
            },
            {
                "id": 6,
                "name": "开发者",
                "permissions": "user.*, role.*, command.*, setting.*, file.*, log.*, system.*",
                "status": "normal",
                "created_time": "2023-04-18 21:35:11",
                "updated_time": "2023-12-15 13:28:44",
                "deleted_time": None,
            },
            {
                "id": 7,
                "name": "安全审计员",
                "permissions": "user.view, role.view, command.view, log.*",
                "status": "normal",
                "created_time": "2023-05-28 14:50:38",
                "updated_time": "2023-11-30 17:12:05",
                "deleted_time": None,
            },
            {
                "id": 8,
                "name": "测试员",
                "permissions": "command.*, setting.view, log.view",
                "status": "disable",
                "created_time": "2023-05-28 14:51:22",
                "updated_time": "2023-08-22 10:44:37",
                "deleted_time": None,
            },
        ]

    def _get_functions_list(self) -> list[dict]:
        return [
            {
                "id": 1,
                "name": "ping",
                "description": "测试机器人是否在线，返回pong响应",
                "status": "normal",
                "created_time": "2023-01-15 10:35:22",
                "updated_time": "2023-12-01 14:22:45",
                "deleted_time": None,
            },
            {
                "id": 2,
                "name": "help",
                "description": "显示所有可用命令的帮助信息",
                "status": "normal",
                "created_time": "2023-01-15 10:36:15",
                "updated_time": "2023-11-20 09:18:33",
                "deleted_time": None,
            },
            {
                "id": 3,
                "name": "ban",
                "description": "封禁指定用户，禁止其使用机器人功能",
                "status": "disable",
                "created_time": "2023-02-10 08:25:44",
                "updated_time": "2023-12-10 11:42:18",
                "deleted_time": None,
            },
            {
                "id": 4,
                "name": "unban",
                "description": "解封被封禁的用户",
                "status": "normal",
                "created_time": "2023-02-10 08:26:30",
                "updated_time": "2023-10-28 16:37:52",
                "deleted_time": None,
            },
            {
                "id": 5,
                "name": "stats",
                "description": "显示系统统计信息和用户活跃度",
                "status": "normal",
                "created_time": "2023-03-01 12:15:27",
                "updated_time": "2023-09-14 08:55:19",
                "deleted_time": None,
            },
            {
                "id": 6,
                "name": "reload",
                "description": "重新加载配置文件和命令模块",
                "status": "disable",
                "created_time": "2023-04-18 21:35:11",
                "updated_time": "2023-12-15 13:28:44",
                "deleted_time": None,
            },
            {
                "id": 7,
                "name": "backup",
                "description": "创建系统数据备份",
                "status": "normal",
                "created_time": "2023-05-28 14:50:38",
                "updated_time": "2023-11-30 17:12:05",
                "deleted_time": None,
            },
            {
                "id": 8,
                "name": "restore",
                "description": "从备份恢复系统数据",
                "status": "normal",
                "created_time": "2023-05-28 14:51:22",
                "updated_time": "2023-08-22 10:44:37",
                "deleted_time": None,
            },
            {
                "id": 9,
                "name": "clear",
                "description": "清理缓存和临时文件",
                "status": "normal",
                "created_time": "2023-06-15 09:30:45",
                "updated_time": "2023-12-05 15:20:18",
                "deleted_time": None,
            },
            {
                "id": 10,
                "name": "update",
                "description": "检查并应用系统更新",
                "status": "disable",
                "created_time": "2023-07-22 16:45:33",
                "updated_time": "2023-11-18 12:33:27",
                "deleted_time": None,
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
