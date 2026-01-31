"""
系统信息使用 Sqlite 存储
"""
from pathlib import Path
from datetime import datetime
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.internal.params import ArgPlainText
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from ...unit.sqlite import SQLiteDatabase


class Settings:

    def command(self):
        """
        初始化系统信息
        """
        init_system_info = on_command(cmd="初始化系统", permission=SUPERUSER)

        # 定义命令处理函数装饰器
        @init_system_info.handle()
        # 异步处理函数，接收bot实例和事件对象
        async def handle_init_system_info(args: Message = CommandArg()):
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
                    CREATE TABLE IF NOT EXISTS `system_info`
                    (
                        `id`           INTEGER PRIMARY KEY AUTOINCREMENT,
                        `key`          TEXT    NOT NULL DEFAULT ''     COMMENT '信息键名',
                        `value`        TEXT    NULL     DEFAULT NULL   COMMENT '信息值',
                        `description`  TEXT    NULL     DEFAULT NULL   COMMENT '描述',
                        `status`       TEXT    NOT NULL DEFAULT 'normal' COMMENT '状态 (normal, disable)',
                        `created_time` TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')) COMMENT '创建时间',
                        `updated_time` TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')) COMMENT '更新时间',
                        `deleted_time` TEXT    NULL     DEFAULT NULL   COMMENT '删除时间',
                        UNIQUE(`key`)
                    );
                    -- 创建索引
                    CREATE INDEX IF NOT EXISTS `system_info_key_index` ON `system_info`(`key`);
                    CREATE INDEX IF NOT EXISTS `system_info_status_index` ON `system_info`(`status`);
                    CREATE INDEX IF NOT EXISTS `system_info_created_time_index` ON `system_info`(`created_time`);
                    CREATE INDEX IF NOT EXISTS `system_info_updated_time_index` ON `system_info`(`updated_time`);
                    """
                    sqlite_db.create_table(create_table_sql)
                    await init_system_info.send("系统信息表创建成功")
                else:
                    # 表已存在
                    await init_system_info.send("系统信息表已存在")
                # 插入默认配置信息
                # 获取当前系统时间
                current_time = datetime.now()
                # 格式化时间为指定格式
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                # mysql 配置信息
                # mysql-host
                data = {
                    "key": "mysql-host",
                    "value": "127.0.0.1",
                    "description": "mysql 主机地址",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)
                # mysql-port
                data = {
                    "key": "mysql-port",
                    "value": "3306",
                    "description": "mysql 端口号",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)
                # mysql-user
                data = {
                    "key": "mysql-user",
                    "value": "root",
                    "description": "mysql 用户名",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)
                # mysql-password
                data = {
                    "key": "mysql-password",
                    "value": "123456",
                    "description": "mysql 密码",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)
                # mysql-database
                data = {
                    "key": "mysql-database",
                    "value": "nonebot",
                    "description": "mysql 数据库名称",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)

                # redis 配置信息
                # redis-host
                data = {
                    "key": "redis-host",
                    "value": "127.0.0.1",
                    "description": "redis 主机地址",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)
                # redis-port
                data = {
                    "key": "redis-port",
                    "value": "6379",
                    "description": "redis 端口号",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)
                # redis-password
                data = {
                    "key": "redis-password",
                    "value": "",
                    "description": "redis 密码（可为空）",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)
                # redis-database
                data = {
                    "key": "redis-database",
                    "value": "0",
                    "description": "redis 数据库编号",
                    "status": "normal",
                    "created_time": formatted_time,
                    "updated_time": formatted_time,
                    "deleted_time": None
                }
                sqlite_db.insert(table="system_info", data=data)

                await init_system_info.send(
                    f"系统信息初始化完成:"
                    f"MySql"
                    f"mysql-host: mysql 主机地址"
                    f"mysql-port: mysql 端口号"
                    f"mysql-user: mysql 用户名"
                    f"mysql-password: mysql 密码"
                    f"mysql-database: mysql 数据库名称"
                    f"Redis"
                    f"redis-host: redis 主机地址"
                    f"redis-port: redis 端口号"
                    f"redis-password: redis 密码（可为空）"
                    f"redis-database: redis 数据库编号"
                    f"请检查并修改配置信息,修改用户名和密码为真实配置"
                )

            # 处理异常
            except Exception as e:
                await init_system_info.finish(f"检查或创建表时出错: {str(e)}")

        @init_system_info.got("info", prompt="""请输入需要修改的配置信息:
例如: mysql-host 127.0.0.1
输入"完成"结束修改""")
        async def got_location(info: str = ArgPlainText()):
            """
            处理命令
            """
            # 如果输入完成，则直接输出修改完成并结束方法
            if info.strip() == "完成":
                await init_system_info.finish("修改已完成！")

            await init_system_info.send(f"信息为: {info}")

            # 继续提示用户输入更多信息，直到用户输入"完成"
            await init_system_info.reject("""请输入需要修改的配置信息:
例如: mysql-host 127.0.0.1
输入"完成"结束修改""")
