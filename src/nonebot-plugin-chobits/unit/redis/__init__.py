"""
Redis 操作类
效果: 对 Redis 进行增删改查操作

配置相关方法
    init: 初始化 Redis 配置，设置连接参数（主机、端口、密码、数据库编号）
    configure: 重新配置 Redis 连接参数
连接管理方法
    create_connection: 创建并返回 Redis 连接实例
通用键值操作方法
    set_value: 设置键值对，可设置过期时间
    get_value: 获取键对应的值
    delete_key: 删除指定键
    exists: 检查键是否存在
列表操作方法
    lpush: 向列表左侧添加元素
    rpush: 向列表右侧添加元素
    lrange: 获取列表范围内的元素
特殊功能方法
    cache_image_list: 将 MySQL 数据库中的图片列表缓存到 Redis 列表中
    flush_db: 清空当前数据库

功能说明:
- 提供 Redis 连接管理功能
- 支持键值对的基本操作（设置、获取、删除、检查存在性）
- 支持 Redis 列表数据结构的操作（左推、右推、范围查询）
- 支持键的过期时间设置
- 提供数据库清空功能
- 包含特定业务功能：将 MySQL 图片列表缓存到 Redis
- 具备异常处理和资源释放功能

使用类库:
    redis-py:
        安装: pip install redis
"""
import json
import redis


class RedisDatabase:
    """
    Redis数据库操作类
    """

    def __init__(self, host="localhost", port=6379, password=None, db=0):
        """
        初始化Redis配置
        """
        self.config = {
            "host": host,
            "port": port,
            "password": password,
            "db": db,
        }

    def configure(self, host, port, password, db):
        """
        配置数据库
        """
        self.config["host"] = host
        self.config["port"] = port
        self.config["password"] = password
        self.config["db"] = db

    def create_connection(self) -> redis.Redis:
        """
        创建 Redis 连接
        """
        connection = redis.Redis(**self.config)
        return connection

    def cache_image_list(self, mysql_db):
        """
        缓存图片列表
        :param mysql_db: MySQL数据库实例
        """
        connection = self.create_connection()
        # 检查连接
        if connection.ping():
            print("Connection to Redis is successful!")
        image_list = mysql_db.select_column('image')
        print(len(image_list))
        for image in image_list:
            # 将字典转换为JSON字符串
            image = json.dumps(image)
            connection.lpush('image_list', image)
        else:
            print("Connection to Redis failed!")

    def set_value(self, key, value, expire=None):
        """
        设置键值对
        :param key: 键
        :param value: 值
        :param expire: 过期时间（秒）
        :return: 是否成功
        """
        connection = self.create_connection()
        try:
            result = connection.set(key, value)
            if expire:
                connection.expire(key, expire)
            return result
        except Exception as e:
            print(f"设置键值对失败: {e}")
            return False
        finally:
            connection.close()

    def get_value(self, key):
        """
        获取键对应的值
        :param key: 键
        :return: 值
        """
        connection = self.create_connection()
        try:
            value = connection.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            print(f"获取键值失败: {e}")
            return None
        finally:
            connection.close()

    def delete_key(self, key):
        """
        删除键
        :param key: 键
        :return: 删除的键数量
        """
        connection = self.create_connection()
        try:
            result = connection.delete(key)
            return result
        except Exception as e:
            print(f"删除键失败: {e}")
            return 0
        finally:
            connection.close()

    def exists(self, key):
        """
        检查键是否存在
        :param key: 键
        :return: 是否存在
        """
        connection = self.create_connection()
        try:
            result = connection.exists(key)
            return bool(result)
        except Exception as e:
            print(f"检查键是否存在失败: {e}")
            return False
        finally:
            connection.close()

    def lpush(self, key, value):
        """
        向列表左侧添加元素
        :param key: 键
        :param value: 值
        :return: 列表长度
        """
        connection = self.create_connection()
        try:
            result = connection.lpush(key, value)
            return result
        except Exception as e:
            print(f"向列表添加元素失败: {e}")
            return 0
        finally:
            connection.close()

    def rpush(self, key, value):
        """
        向列表右侧添加元素
        :param key: 键
        :param value: 值
        :return: 列表长度
        """
        connection = self.create_connection()
        try:
            result = connection.rpush(key, value)
            return result
        except Exception as e:
            print(f"向列表添加元素失败: {e}")
            return 0
        finally:
            connection.close()

    def lrange(self, key, start=0, end=-1):
        """
        获取列表范围内的元素
        :param key: 键
        :param start: 开始位置
        :param end: 结束位置
        :return: 元素列表
        """
        connection = self.create_connection()
        try:
            result = connection.lrange(key, start, end)
            return [item.decode('utf-8') for item in result]
        except Exception as e:
            print(f"获取列表元素失败: {e}")
            return []
        finally:
            connection.close()

    def flush_db(self):
        """
        清空当前数据库
        :return: 是否成功
        """
        connection = self.create_connection()
        try:
            result = connection.flushdb()
            return result
        except Exception as e:
            print(f"清空数据库失败: {e}")
            return False
        finally:
            connection.close()
