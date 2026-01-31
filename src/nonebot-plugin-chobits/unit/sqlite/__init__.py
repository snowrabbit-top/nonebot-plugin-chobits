"""
SQLite 数据库操作类
效果: 对数据库的增删改查

配置相关方法
    init: 初始化数据库配置，设置数据库文件路径
    configure: 重新配置数据库文件路径
连接管理方法
    create_connection: 创建并返回数据库连接
SQL语句构建方法
    create_field_string: 创建字段字符串（用于 INSERT 语句）
    create_variable_string: 创建值占位符字符串（用于 INSERT 语句，使用参数化查询）
    create_key_value_pair: 创建 SET 子句的键值对（用于 UPDATE 语句）
    create_where_clause: 创建 WHERE 子句和对应的参数列表，支持等值、NULL、IN、LIKE、BETWEEN 等操作
    create_order_by_clause: 生成 ORDER BY 子句
数据库操作方法
    create_table: 执行 SQL 创建表
    insert: 插入单条数据，返回新插入行的 rowid
    insert_all: 批量插入数据，返回最后插入的 rowid
    delete: 根据条件删除数据
    update: 根据条件更新数据
    _execute_select: 通用查询方法（内部使用）
    select: 查询数据，返回元组列表
    select_column: 查询数据，返回带字段名的字典列表
    find_info: 查询一条数据，返回字典格式
    has_info: 判断是否存在满足条件的数据

功能说明:
- 提供 SQLite 数据库连接管理功能
- 支持表的创建操作
- 支持数据的增删改查操作
- 支持单条和批量数据插入
- 支持复杂查询条件（WHERE 子句），包括等值、范围、模糊匹配、IN 等操作
- 支持查询结果排序和限制返回数量
- 提供多种数据返回格式（元组列表、字典格式等）
- 采用参数化查询防止 SQL 注入
- 具备异常处理和资源释放功能
"""
import sqlite3
from typing import Dict, List, Optional, Union, Any


class SQLiteDatabase:
    """
    SQLite数据库操作类
    """

    def __init__(self, database=""):
        """
        初始化数据库配置（SQLite 只需数据库文件路径）
        """
        self.database = database

    def configure(self, database: str):
        """
        重新配置数据库文件路径
        """
        self.database = database

    def create_connection(self) -> sqlite3.Connection:
        """
        创建并返回数据库连接
        """
        try:
            conn = sqlite3.connect(self.database)
            print("创建连接成功")
            return conn
        except sqlite3.Error as e:
            print(f"数据库连接错误: {e}")
            raise

    def create_field_string(self, data: Dict[str, Any]) -> str:
        """
        创建字段字符串（用于 INSERT）
        """
        return ", ".join([f"`{key}`" for key in data.keys()])

    def create_variable_string(self, data: Dict[str, Any]) -> str:
        """
        创建值占位符字符串（用于 INSERT）
        使用参数化查询，此处仅生成占位符
        """
        return ", ".join(["?" for _ in data])

    def create_key_value_pair(self, data: Dict[str, Any]) -> str:
        """
        创建 SET 子句的键值对（用于 UPDATE）
        """
        return ", ".join([f"`{key}` = ?" for key in data.keys()])

    def create_where_clause(self, where_list: Dict[str, Any]) -> tuple:
        """
        创建 WHERE 子句和对应的参数列表
        支持：
          - 简单等值：{"name": "Alice"}
          - NULL：{"status": None}
          - 列表形式的高级条件（扩展用，此处简化处理）
        注意：为安全起见，SQLite 中强烈建议使用参数化查询，避免拼接值
        返回：(where_clause_str, params_list)
        """
        if not where_list:
            return "", []

        conditions = []
        params = []

        for key, value in where_list.items():
            if value is None:
                conditions.append(f"`{key}` IS NULL")
            elif isinstance(value, list):
                # 简单支持 IN 查询：{"id": ["in", [1,2,3]]}
                if len(value) == 2 and value[0] == "in":
                    placeholders = ",".join(["?" for _ in value[1]])
                    conditions.append(f"`{key}` IN ({placeholders})")
                    params.extend(value[1])
                elif len(value) == 2 and value[0] == "like":
                    conditions.append(f"`{key}` LIKE ?")
                    params.append(f"%{value[1]}%")
                elif len(value) == 3 and value[0] == "between":
                    conditions.append(f"`{key}` BETWEEN ? AND ?")
                    params.extend([value[1], value[2]])
                else:
                    # 未知格式，忽略或报错
                    raise ValueError(f"Unsupported where condition format for key: {key}")
            else:
                conditions.append(f"`{key}` = ?")
                params.append(value)

        where_clause = " WHERE " + " AND ".join(conditions)
        return where_clause, params

    def create_order_by_clause(self, order_list: Optional[Dict[str, str]]) -> str:
        """
        生成 ORDER BY 子句
        order_list 示例: {"id": "ASC", "name": "DESC"}
        """
        if not order_list:
            return ""
        order_parts = [f"`{col}` {direction.upper()}" for col, direction in order_list.items()]
        return " ORDER BY " + ", ".join(order_parts)

    def create_table(self, sql: str) -> bool:
        """
        创建表
        """
        conn = None
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            print("创建表成功")
            return True
        except sqlite3.Error as e:
            print(f"创建表失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
                print("关闭连接")

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        插入单条数据，返回新插入行的 rowid
        """
        conn = None
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            fields = self.create_field_string(data)
            placeholders = self.create_variable_string(data)
            sql = f"INSERT INTO `{table}` ({fields}) VALUES ({placeholders})"
            cursor.execute(sql, list(data.values()))
            conn.commit()
            last_row_id = cursor.lastrowid
            print("保存数据成功")
            return last_row_id
        except sqlite3.Error as e:
            print(f"保存数据失败: {e}")
            return -1
        finally:
            if conn:
                conn.close()
                print("关闭连接")

    def insert_all(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """
        批量插入数据，返回最后插入的 rowid
        """
        if not data_list:
            return 0

        conn = None
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            sample = data_list[0]
            fields = self.create_field_string(sample)
            placeholders = self.create_variable_string(sample)
            sql = f"INSERT INTO `{table}` ({fields}) VALUES ({placeholders})"

            # 批量执行
            values_list = [list(row.values()) for row in data_list]
            cursor.executemany(sql, values_list)
            conn.commit()
            last_row_id = cursor.lastrowid
            print("批量保存数据成功")
            return last_row_id
        except sqlite3.Error as e:
            print(f"批量保存数据失败: {e}")
            return -1
        finally:
            if conn:
                conn.close()
                print("关闭连接")

    def delete(self, table: str, where: Dict[str, Any]) -> bool:
        """
        删除数据
        """
        conn = None
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            where_clause, params = self.create_where_clause(where)
            sql = f"DELETE FROM `{table}`{where_clause}"
            print(sql)
            cursor.execute(sql, params)
            conn.commit()
            print("删除数据成功")
            return True
        except sqlite3.Error as e:
            print(f"删除数据失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
                print("关闭连接")

    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """
        更新数据
        """
        conn = None
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            set_clause = self.create_key_value_pair(data)
            where_clause, where_params = self.create_where_clause(where)
            sql = f"UPDATE `{table}` SET {set_clause}{where_clause}"
            params = list(data.values()) + where_params
            print(sql)
            cursor.execute(sql, params)
            conn.commit()
            print("更新数据成功")
            return True
        except sqlite3.Error as e:
            print(f"更新数据失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
                print("关闭连接")

    def _execute_select(self, table: str, where: Optional[Dict[str, Any]] = None, order: Optional[Dict[str, str]] = None, limit: Optional[int] = None, fetchone: bool = False, with_column_names: bool = False):
        """
        通用查询方法
        """
        conn = None
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            where_clause, params = self.create_where_clause(where) if where else ("", [])
            order_clause = self.create_order_by_clause(order)
            limit_clause = f" LIMIT {limit}" if limit else ""

            sql = f"SELECT * FROM `{table}`{where_clause}{order_clause}{limit_clause}"
            print(sql)
            cursor.execute(sql, params)

            if fetchone:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()

            if with_column_names and result is not None:
                column_names = [desc[0] for desc in cursor.description]
                if fetchone and result:
                    return dict(zip(column_names, result))
                elif not fetchone and result:
                    return [dict(zip(column_names, row)) for row in result]
                else:
                    return [] if not fetchone else None
            else:
                return result
        except sqlite3.Error as e:
            print(f"查询数据失败: {e}")
            return None
        finally:
            if conn:
                conn.close()
                print("关闭连接")

    def select(self, table: str, where: Optional[Dict[str, Any]] = None,
               order: Optional[Dict[str, str]] = None, limit: Optional[int] = None) -> Optional[List[tuple]]:
        """
        查询数据（返回元组列表）
        """
        return self._execute_select(table, where, order, limit, fetchone=False, with_column_names=False)

    def select_column(self, table: str, where: Optional[Dict[str, Any]] = None, order: Optional[Dict[str, str]] = None, limit: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """
        查询数据，返回带字段名的字典列表
        """
        return self._execute_select(table, where, order, limit, fetchone=False, with_column_names=True)

    def find_info(self, table: str, where: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        查询一条数据，返回字典
        """
        return self._execute_select(table, where, fetchone=True, with_column_names=True)

    def has_info(self, table: str, where: Optional[Dict[str, Any]] = None) -> bool:
        """
        判断是否存在满足条件的数据
        """
        conn = None
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            where_clause, params = self.create_where_clause(where) if where else ("", [])
            sql = f"SELECT 1 FROM `{table}`{where_clause} LIMIT 1"
            cursor.execute(sql, params)
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"检查数据存在性失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
                print("关闭连接")
