"""
系统信息使用 Sqlite 存储
"""
from pathlib import Path
from datetime import datetime
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.internal.params import ArgPlainText
from nonebot.typing import T_State
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from ...unit.sqlite import SQLiteDatabase


class Settings:

    def _parse_input(self, input_str: str):
        """
        解析输入字符串，将其按空格拆分为key和value
        :param input_str: 输入字符串
        :return: tuple (key, value)
        """
        parts = input_str.split(" ", 1)
        if len(parts) >= 2:
            key = parts[0]
            value = parts[1]
        else:
            key = parts[0] if parts else ""
            value = ""
        return key, value

    def _get_default_configs(self, formatted_time: str):
        """
        获取默认配置
        :param formatted_time: 格式化时间
        :return: 默认配置列表
        """
        return [
            {
                "key": "mysql-host",
                "value": "127.0.0.1",
                "description": "mysql 主机地址",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "mysql-port",
                "value": "3306",
                "description": "mysql 端口号",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "mysql-user",
                "value": "root",
                "description": "mysql 用户名",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "mysql-password",
                "value": "123456",
                "description": "mysql 密码",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "mysql-database",
                "value": "nonebot",
                "description": "mysql 数据库名称",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "redis-host",
                "value": "127.0.0.1",
                "description": "redis 主机地址",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "redis-port",
                "value": "6379",
                "description": "redis 端口号",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "redis-password",
                "value": "",
                "description": "redis 密码（可为空）",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "redis-database",
                "value": "0",
                "description": "redis 数据库编号",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "admin-user",
                "value": "admin",
                "description": "管理界面账号",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            },
            {
                "key": "admin-password",
                "value": "123456",
                "description": "管理界面密码",
                "status": "normal",
                "created_time": formatted_time,
                "updated_time": formatted_time,
                "deleted_time": None
            }
        ]

    def _get_default_config_map(self, formatted_time: str):
        """
        获取默认配置映射
        :param formatted_time: 格式化时间
        :return: 默认配置映射
        """
        default_configs = self._get_default_configs(formatted_time)
        return {config["key"]: config for config in default_configs}

    def _parse_overwrite_input(self, input_text: str):
        """
        解析是否覆盖的输入
        :param input_text: 输入文本
        :return: True/False/None
        """
        normalized = input_text.strip().lower()
        if normalized in ["是", "yes", "y", "覆盖", "overwrite", "--force", "-f"]:
            return True
        if normalized in ["否", "no", "n", "不覆盖", "skip", "--skip"]:
            return False
        return None

    async def _apply_default_configs(self, sqlite_db: SQLiteDatabase, default_configs, overwrite: bool):
        """
        应用默认配置（增量初始化）
        :param sqlite_db: 数据库实例
        :param default_configs: 默认配置列表
        :param overwrite: 是否覆盖
        """
        inserted = 0
        updated = 0
        skipped = 0
        for config in default_configs:
            key = config["key"]
            if sqlite_db.has_info(table="system_info", where={"key": key}):
                if overwrite:
                    sqlite_db.update(
                        table="system_info",
                        data={
                            "value": config["value"],
                            "description": config["description"],
                            "status": config["status"],
                            "updated_time": config["updated_time"],
                            "deleted_time": config["deleted_time"]
                        },
                        where={"key": key}
                    )
                    updated += 1
                else:
                    skipped += 1
            else:
                sqlite_db.insert(table="system_info", data=config)
                inserted += 1
        return inserted, updated, skipped

    async def _validate_and_update_setting(self, sqlite_db: SQLiteDatabase, init_system_info, key: str, value: str, default_config_map):
        """
        验证输入并更新系统配置
        :param sqlite_db: 数据库实例
        :param init_system_info: 命令处理器
        :param key: 配置键
        :param value: 配置值
        :param default_config_map: 默认配置映射
        """
        if key == "" or value == "":
            await init_system_info.reject("请提示重新输入！")

        if key not in default_config_map:
            await init_system_info.reject(f"你想修改的信息 {key} 暂不支持修改，请重新输入！")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if sqlite_db.has_info(table="system_info", where={"key": key}):
            sqlite_db.update(
                table="system_info",
                data={
                    "value": value,
                    "updated_time": current_time
                },
                where={"key": key}
            )
        else:
            config = default_config_map[key]
            sqlite_db.insert(
                table="system_info",
                data={
                    "key": key,
                    "value": value,
                    "description": config["description"],
                    "status": config["status"],
                    "created_time": current_time,
                    "updated_time": current_time,
                    "deleted_time": config["deleted_time"]
                }
            )

        await init_system_info.send(f"{key} 已设置为 {value}")

    def _format_settings(self, settings):
        """
        格式化系统配置信息
        :param settings: 配置信息列表
        :return: 格式化字符串
        """
        lines = []
        for setting in settings:
            key = setting.get("key", "")
            value = setting.get("value", "")
            description = setting.get("description", "")
            lines.append(f"{key}: {value} ({description})")
        return "\n".join(lines)

    def command(self):
        """
        初始化系统信息
        """
        init_system_info = on_command(cmd="初始化系统", permission=SUPERUSER)
        view_system_info = on_command(cmd="查看系统配置", permission=SUPERUSER)

        # 定义命令处理函数装饰器
        @init_system_info.handle()
        # 异步处理函数，接收bot实例和事件对象
        async def handle_init_system_info(state: T_State, args: Message = CommandArg()):
            """
            处理命令
            """
            print("正在初始化系统信息...")
            # 当前文件目录
            current_file_dir = Path(__file__).parent
            # 当前文件目录上级的上级的目录
            parent_dir = current_file_dir.parent.parent
            # 当前文件目录上级的上级的 database 目录下的 database.db 文件
            database_file = parent_dir / "database" / "database.db"
            # 创建数据库连接
            sqlite_db = SQLiteDatabase(database=database_file)

            # 检查表是否已存在
            try:
                conn = sqlite_db.create_connection()
                cursor = conn.cursor()
                # 查询sqlite_master表检查系统信息表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_info';")
                table_exists = cursor.fetchone() is not None
                conn.close()

                if not table_exists:
                    # 表不存在，创建表
                    create_table_sql = """
                    -- 系统信息表
                    CREATE TABLE IF NOT EXISTS system_info
                    (
                        id           INTEGER PRIMARY KEY AUTOINCREMENT,
                        key          TEXT    NOT NULL DEFAULT '',
                        value        TEXT    NULL     DEFAULT NULL,
                        description  TEXT    NULL     DEFAULT NULL,
                        status       TEXT    NOT NULL DEFAULT 'normal',
                        created_time TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                        updated_time TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                        deleted_time TEXT    NULL     DEFAULT NULL,
                        UNIQUE(key)
                    );
                    -- 创建索引
                    CREATE INDEX IF NOT EXISTS system_info_key_index ON system_info(key);
                    CREATE INDEX IF NOT EXISTS system_info_status_index ON system_info(status);
                    CREATE INDEX IF NOT EXISTS system_info_created_time_index ON system_info(created_time);
                    CREATE INDEX IF NOT EXISTS system_info_updated_time_index ON system_info(updated_time);
                    """
                    # 根据分号拆分SQL语句并循环执行
                    sql_statements = [stmt.strip() for stmt in create_table_sql.split(';') if stmt.strip()]

                    for sql_stmt in sql_statements:
                        if sql_stmt:  # 确保不是空语句
                            print(f"正在执行SQL语句：{sql_stmt}")
                            sqlite_db.create_table(sql_stmt)

                    print("所有SQL语句执行完成")
                    await init_system_info.send("系统信息表创建成功")
                else:
                    # 表已存在
                    await init_system_info.send("系统信息表已存在")
                # 插入默认配置信息
                current_time = datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                default_configs = self._get_default_configs(formatted_time)
                state["database_file"] = str(database_file)
                state["default_configs"] = default_configs

                args_text = args.extract_plain_text().strip()
                overwrite = None
                if args_text:
                    overwrite = self._parse_overwrite_input(args_text)
                existing_keys = [
                    config["key"]
                    for config in default_configs
                    if sqlite_db.has_info(table="system_info", where={"key": config["key"]})
                ]
                state["existing_keys"] = existing_keys
                if overwrite is None:
                    state["overwrite_required"] = bool(existing_keys)
                else:
                    state["overwrite_required"] = False
                    state["overwrite"] = overwrite

                if existing_keys and state["overwrite_required"]:
                    await init_system_info.send(
                        "检测到已有系统配置，回复“是/否”选择是否覆盖，或使用参数“覆盖”/“不覆盖”。"
                    )
                else:
                    applied_overwrite = state.get("overwrite", False)
                    inserted, updated, skipped = await self._apply_default_configs(
                        sqlite_db=sqlite_db,
                        default_configs=default_configs,
                        overwrite=applied_overwrite
                    )
                    await init_system_info.send(
                        f"系统信息初始化完成: 新增 {inserted} 条，覆盖 {updated} 条，保留 {skipped} 条。"
                    )
                    await init_system_info.send(
                        "当前系统配置:\r\n\r\n"
                        "=== MySQL 配置 ===\r\n"
                        "mysql-host: mysql 主机地址\r\n"
                        "mysql-port: mysql 端口号\r\n"
                        "mysql-user: mysql 用户名\r\n"
                        "mysql-password: mysql 密码\r\n"
                        "mysql-database: mysql 数据库名称\r\n\r\n"
                        "=== Redis 配置 ===\r\n"
                        "redis-host: redis 主机地址\r\n"
                        "redis-port: redis 端口号\r\n"
                        "redis-password: redis 密码（可为空）\r\n"
                        "redis-database: redis 数据库编号\r\n\r\n"
                        "=== 管理界面 配置 ===\r\n"
                        "admin-user: 管理界面账号\r\n"
                        "admin-password: 管理界面密码\r\n"
                        "请检查并修改配置信息，将用户名和密码改为真实配置"
                    )

            # 处理异常
            except Exception as e:
                await init_system_info.finish(f"检查或创建表时出错: {str(e)}")

        @init_system_info.got("overwrite", prompt="检测到已有系统配置，是否覆盖？(是/否)")
        async def got_overwrite(overwrite: str = ArgPlainText(), state: T_State = None):
            """
            处理覆盖确认
            """
            if not state.get("overwrite_required", False):
                return

            overwrite_choice = self._parse_overwrite_input(overwrite)
            if overwrite_choice is None:
                await init_system_info.reject("请输入“是”或“否”以确认是否覆盖已有配置。")

            database_file = state.get("database_file")
            default_configs = state.get("default_configs", [])
            sqlite_db = SQLiteDatabase(database=database_file)
            inserted, updated, skipped = await self._apply_default_configs(
                sqlite_db=sqlite_db,
                default_configs=default_configs,
                overwrite=overwrite_choice
            )
            state["overwrite"] = overwrite_choice
            state["overwrite_required"] = False
            await init_system_info.send(
                f"系统信息初始化完成: 新增 {inserted} 条，覆盖 {updated} 条，保留 {skipped} 条。"
            )
            await init_system_info.send(
                "当前系统配置:\r\n\r\n"
                "=== MySQL 配置 ===\r\n"
                "mysql-host: mysql 主机地址\r\n"
                "mysql-port: mysql 端口号\r\n"
                "mysql-user: mysql 用户名\r\n"
                "mysql-password: mysql 密码\r\n"
                "mysql-database: mysql 数据库名称\r\n\r\n"
                "=== Redis 配置 ===\r\n"
                "redis-host: redis 主机地址\r\n"
                "redis-port: redis 端口号\r\n"
                "redis-password: redis 密码（可为空）\r\n"
                "redis-database: redis 数据库编号\r\n\r\n"
                "=== 管理界面 配置 ===\r\n"
                "admin-user: 管理界面账号\r\n"
                "admin-password: 管理界面密码\r\n"
                "请检查并修改配置信息，将用户名和密码改为真实配置"
            )

        @init_system_info.got("info", prompt="""请输入需要修改的配置信息:
格式: 配置项 新值
例如: mysql-host 192.168.1.100
支持的配置项:
mysql-host
mysql-port
mysql-user
mysql-password
mysql-database
redis-host
redis-port
redis-password
redis-database
admin-user
admin-password
输入"完成"结束修改""")
        async def got_location(info: str = ArgPlainText(), state: T_State = None):
            """
            处理命令
            """
            # 如果输入完成，则直接输出修改完成并结束方法
            if info.strip() == "完成":
                await init_system_info.finish("修改已完成！")

            key, value = self._parse_input(info)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            default_config_map = self._get_default_config_map(current_time)
            database_file = state.get("database_file")
            if not database_file:
                current_file_dir = Path(__file__).parent
                parent_dir = current_file_dir.parent.parent
                database_file = parent_dir / "database" / "database.db"
            sqlite_db = SQLiteDatabase(database=database_file)

            await self._validate_and_update_setting(
                sqlite_db=sqlite_db,
                init_system_info=init_system_info,
                key=key,
                value=value,
                default_config_map=default_config_map
            )

            # 继续提示用户输入更多信息，直到用户输入"完成"
            await init_system_info.reject("""请输入需要修改的配置信息:
格式: 配置项 新值
例如: mysql-host 192.168.1.100
支持的配置项:
mysql-host
mysql-port
mysql-user
mysql-password
mysql-database
redis-host
redis-port
redis-password
redis-database
admin-user
admin-password
输入"完成"结束修改""")

        @view_system_info.handle()
        async def handle_view_system_info():
            """
            查看系统配置
            """
            current_file_dir = Path(__file__).parent
            parent_dir = current_file_dir.parent.parent
            database_file = parent_dir / "database" / "database.db"
            sqlite_db = SQLiteDatabase(database=database_file)

            conn = sqlite_db.create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_info';")
            table_exists = cursor.fetchone() is not None
            conn.close()

            if not table_exists:
                await view_system_info.finish("系统信息表不存在，请先执行初始化系统。")

            settings = sqlite_db.select_column(
                table="system_info",
                order={"key": "ASC"}
            )
            if not settings:
                await view_system_info.finish("当前没有系统配置。")

            formatted_settings = self._format_settings(settings)
            await view_system_info.finish(f"当前系统配置如下:\n{formatted_settings}")
