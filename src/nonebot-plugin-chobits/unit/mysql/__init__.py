"""
MySQL 数据库操作类
效果: 对数据库的增删改查
配置相关方法
    init: 初始化数据库配置，设置连接参数
    configure: 重新配置数据库连接参数
连接管理方法
    create_connection: 创建并返回数据库连接
SQL语句构建方法
    create_field_string: 创建字段字符串（用于INSERT语句的字段部分）
    create_variable_string: 创建变量字符串（用于INSERT语句的值部分）
    create_key_value_pair: 创建键值对字符串（用于UPDATE语句的SET部分）
    create_where_clause: 创建WHERE子句，支持多种条件操作
    create_order_by_clause: 创建ORDER BY排序子句
数据库操作方法
    create_table: 执行SQL创建表
    insert: 单条数据插入
    insert_all: 批量数据插入
    delete: 根据条件删除数据
    update: 根据条件更新数据
    select: 查询数据，返回原始结果
    select_column: 查询数据，返回带有列名的字典格式结果
    find_info: 查询单条数据，返回字典格式
    has_info: 检查指定条件的数据是否存在

功能说明:
- 提供数据库连接管理功能
- 支持表的创建操作
- 支持数据的增删改查操作
- 支持单条和批量数据插入
- 支持复杂查询条件（WHERE子句），包括等值、范围、模糊匹配、IN等操作
- 支持查询结果排序
- 提供多种数据返回格式（原始列表、字典格式等）
- 具备事务管理、异常处理和资源释放功能

使用类库:
    MySQL Connector:
        安装: pip install mysql-connector
"""
import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection


class MySQLDatabase:
    """
    MySQL数据库操作类
    """

    def __init__(self, user="", password="", host="localhost", database="", port="3306"):
        """
        初始化数据库配置
        """
        self.config = {
            "user": user,
            "password": password,
            "host": host,
            "database": database,
            "port": port,
        }

    def configure(self, user, password, host, database, port):
        """
        重新配置数据库
        """
        self.config["user"] = user
        self.config["password"] = password
        self.config["host"] = host
        self.config["database"] = database
        self.config["port"] = port

    def create_connection(self) -> PooledMySQLConnection | MySQLConnectionAbstract | None:
        """
        创建并返回数据库连接
        """
        connect = None
        # 建立连接
        try:
            connect = mysql.connector.connect(
                raise_on_warnings=True,
                autocommit=False,
                **self.config
            )
            print("创建连接成功")
        except mysql.connector.Error as e:
            print(f"数据库连接错误: {e}")
        return connect

    def create_field_string(self, data) -> str:
        """
        创建字段字符串
        """
        field_string = ""
        for index, row in enumerate(data):
            if index:
                field_string += ', '
            field_string += f"`{row}`"
        return field_string

    def create_variable_string(self, data) -> str:
        """
        创建变量字符串
        """
        variable_string = ""
        for index, row in enumerate(data):
            if index:
                variable_string += ', '
            if data[row] == 'NULL':
                variable_string += 'NULL'
            else:
                variable_string += f"'{data[row]}'"
        return variable_string

    def create_key_value_pair(self, data) -> str:
        """
        创建键值对字符串
        """
        key_value_pair = ""
        for index, row in enumerate(data):
            if index:
                key_value_pair += ', '
            if data[row] == 'NULL':
                key_value_pair += f"`{row}` = NULL"
            else:
                key_value_pair += f"`{row}` = '{data[row]}'"
        return key_value_pair

    def create_where_clause(self, where_list) -> str:
        """
        创建where子句
        """
        if where_list:
            where_clause = " WHERE "
            for index, key in enumerate(where_list):
                if index:
                    where_clause += ' AND '
                if type(where_list[key]) is list:
                    if len(where_list[key]) == 2:
                        where_clause += f"`{key}` {where_list[key][0]} "
                        if where_list[key][0] == 'between':
                            where_clause += f" '{where_list[key][1][0]}' AND '{where_list[key][1][1]}' "
                        elif where_list[key][0] == 'like':
                            where_clause += f" '%{where_list[key][1]}%' "
                        elif where_list[key][0] == 'in':
                            where_clause += " ('" + "', '".join([str(item) for item in where_list[key][1]]) + "') "
                        else:
                            where_clause += f" '{where_list[key][1]}' "
                else:
                    if where_list[key] == 'NULL':
                        where_clause += f"`{key}` IS NULL"
                    else:
                        where_clause += f"`{key}` = '{where_list[key]}'"
            return where_clause
        else:
            return ""

    def create_order_by_clause(self, order_list):
        """
        生成排序SQL语句
        """
        if order_list:
            order_by_clause = ' ORDER BY '
            for key, value in order_list.items():
                order_by_clause += f'`{key}` {value}, '
            order_by_clause = order_by_clause[:-2]
            return order_by_clause
        else:
            return ''

    def create_table(self, sql) -> bool:
        """
        创建表
        """
        # 创建连接
        connection = self.create_connection()
        # 声明游标
        cursor = None
        try:
            # 创建游标
            cursor = connection.cursor()
            # 执行SQL语句
            cursor.execute(sql)
            # 提交事务
            connection.commit()
            print("创建表成功")
            return True
        except mysql.connector.Error as e:
            # 回滚事务
            connection.rollback()
            print(f"创建表失败: {e}")
            return False
        finally:
            # 关闭游标
            if cursor is not None:
                cursor.close()
                print("关闭游标")
            # 关闭连接
            if connection.is_connected():
                connection.close()
                print("关闭连接")

    def insert(self, table, data) -> int | bool:
        """
        保存数据
        """
        # 创建连接
        connection = self.create_connection()
        # 声明游标
        cursor = None
        try:
            # 创建游标
            cursor = connection.cursor()
            # 创建SQL语句
            sql = "INSERT INTO `" + table + "` (" + self.create_field_string(data) + ") VALUES (" + self.create_variable_string(data) + ")"
            # 执行SQL语句
            cursor.execute(sql)
            # 提交事务
            connection.commit()
            # 获取新插入行的ID
            last_row_id = cursor.lastrowid
            print("保存数据成功")
            return last_row_id
        except mysql.connector.Error as e:
            # 回滚事务
            connection.rollback()
            print(f"保存数据失败: {e}")
            return False
        finally:
            # 关闭游标
            if cursor is not None:
                cursor.close()
                print("关闭游标")
            # 关闭连接
            if connection.is_connected():
                connection.close()
                print("关闭连接")

    def insert_all(self, table, data) -> int | bool:
        """
        批量保存数据
        """
        # 创建连接
        connection = self.create_connection()
        # 声明游标
        cursor = None
        try:
            # 创建游标
            cursor = connection.cursor()
            # 初始化SQL语句
            sql = "INSERT INTO `" + table + "` (" + self.create_field_string(data[0]) + ") VALUES "
            # 循环遍历数据
            for index, row in enumerate(data):
                if index:
                    sql += ', '
                sql += "(" + self.create_variable_string(row) + ")"
            # 执行SQL语句
            cursor.execute(sql)
            # 提交事务
            connection.commit()
            # 获取新插入行的ID
            last_row_id = cursor.lastrowid
            print("保存数据成功")
            return last_row_id
        except mysql.connector.Error as e:
            # 回滚事务
            connection.rollback()
            print(f"保存数据失败: {e}")
            return False
        finally:
            # 关闭游标
            if cursor is not None:
                cursor.close()
                print("关闭游标")
            # 关闭连接
            if connection.is_connected():
                connection.close()
                print("关闭连接")

    def delete(self, table, where) -> bool:
        """
        删除数据
        """
        # 创建连接
        connection = self.create_connection()
        # 声明游标
        cursor = None
        try:
            # 创建游标
            cursor = connection.cursor()
            # 创建SQL语句
            sql = "DELETE FROM `" + table + "`" + self.create_where_clause(where)
            print(sql)
            # 执行SQL语句
            cursor.execute(sql)
            # 提交事务
            connection.commit()
            print("删除数据成功")
            return True
        except mysql.connector.Error as e:
            # 回滚事务
            connection.rollback()
            print(f"删除数据失败: {e}")
            return False
        finally:
            # 关闭游标
            if cursor is not None:
                cursor.close()
                print("关闭游标")
            # 关闭连接
            if connection.is_connected():
                connection.close()
                print("关闭连接")

    def update(self, table, data, where) -> bool:
        """
        更新数据
        """
        # 创建连接
        connection = self.create_connection()
        # 声明游标
        cursor = None
        try:
            # 创建游标
            cursor = connection.cursor()
            # 创建SQL语句
            sql = "UPDATE `" + table + "` SET " + self.create_key_value_pair(data) + self.create_where_clause(where)
            print(sql)
            # 执行SQL语句
            cursor.execute(sql)
            # 提交事务
            connection.commit()
            print("更新数据成功")
            return True
        except mysql.connector.Error as e:
            # 回滚事务
            connection.rollback()
            print(f"更新数据失败: {e}")
            return False
        finally:
            # 关闭游标
            if cursor is not None:
                cursor.close()
                print("关闭游标")
            # 关闭连接
            if connection.is_connected():
                connection.close()
                print("关闭连接")

    def select(self, table, where=None, order=None, limit=None) -> list | None:
        """
        查询数据
        """
        # 创建连接
        connection = self.create_connection()
        # 声明游标
        cursor = None
        try:
            # 创建游标
            cursor = connection.cursor()
            # 创建SQL语句
            sql = "SELECT * FROM `" + table + "`" + self.create_where_clause(where)
            # 执行SQL语句
            cursor.execute(sql)
            # 获取查询结果
            result = cursor.fetchall()
            print("查询数据成功")
            return result
        except mysql.connector.Error as e:
            print(f"查询数据失败: {e}")
            return None
        finally:
            # 关闭游标
            if cursor is not None:
                cursor.close()
                print("关闭游标")
            # 关闭连接
            if connection.is_connected():
                connection.close()
                print("关闭连接")

    def select_column(self, table, where=None, order=None, limit=None) -> list | None:
        """
        查询数据,返回带键名格式
        """
        # 创建连接
        connection = self.create_connection()
        # 声明游标
        cursor = None
        try:
            # 创建游标
            cursor = connection.cursor()
            # 创建SQL语句
            sql = "SELECT * FROM `" + table + "`" + self.create_where_clause(where) + self.create_order_by_clause(order)
            # 执行SQL语句
            cursor.execute(sql)
            # 获取查询结果的列名
            column_names = cursor.description
            # 获取查询结果
            result = cursor.fetchall()
            # 合并字段名
            all_result = []
            for row in result:
                info = {}
                for index, cell in enumerate(row):
                    info[column_names[index][0]] = cell
                all_result.append(info)
            print("查询数据成功")
            return all_result
        except mysql.connector.Error as e:
            print(f"查询数据失败: {e}")
            return None
        finally:
            # 关闭游标
            if cursor is not None:
                cursor.close()
                print("关闭游标")
            # 关闭连接
            if connection.is_connected():
                connection.close()
                print("关闭连接")

    def find_info(self, table, where=None) -> dict | None:
        """
        查询一条数据
        """
        # 创建连接
        connection = self.create_connection()
        # 声明游标
        cursor = None
        try:
            # 创建游标
            cursor = connection.cursor()
            # 创建SQL语句
            sql = "SELECT * FROM `" + table + "`" + self.create_where_clause(where)
            print(sql)
            # 执行SQL语句
            cursor.execute(sql)
            # 获取查询结果的列名
            column_names = cursor.description
            # 获取查询结果
            result = cursor.fetchall()
            if len(result) <= 0:
                return None
            # 合并字段名
            all_result = []
            for row in result:
                info = {}
                for index, cell in enumerate(row):
                    info[column_names[index][0]] = cell
                all_result.append(info)
            print("查询数据成功")
            return all_result[0]
        except mysql.connector.Error as e:
            print(f"查询数据失败: {e}")
            return None
        finally:
            # 关闭游标
            if cursor is not None:
                cursor.close()
                print("关闭游标")
            # 关闭连接
            if connection.is_connected():
                connection.close()
                print("关闭连接")

    def has_info(self, table, where=None) -> bool:
        """
        查询信息是否存在
        """
        info_list = self.select(table, where)
        if len(info_list):
            return True
        else:
            return False
