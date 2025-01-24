# import sqlite3
# import json
# import time

# class SQLiteClient:
#     def __init__(self, db_name='data.db'):
#         """初始化客户端，连接到 SQLite 数据库"""
#         self.db_name = db_name
#         self.conn = sqlite3.connect(self.db_name)
#         self.cursor = self.conn.cursor()

#     def create_table(self):
#         """创建表"""
#         self.cursor.execute('''
#         CREATE TABLE IF NOT EXISTS cache_data (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             cache_key TEXT NOT NULL,
#             data TEXT NOT NULL,
#             timestamp INTEGER NOT NULL,
#             expiration INTEGER NOT NULL
#         )
#         ''')
#         self.conn.commit()

#     def insert_cache(self, cache_key, data, expiration):
#         """插入缓存数据"""
#         timestamp = int(time.time())  # 获取当前时间戳
#         self.cursor.execute('''
#         INSERT INTO cache_data (cache_key, data, timestamp, expiration)
#         VALUES (?, ?, ?, ?)
#         ''', (cache_key, json.dumps(data), timestamp, expiration))
#         self.conn.commit()

#     def get_cache(self, cache_key):
#         """查询缓存数据"""
#         self.cursor.execute('''
#         SELECT data, timestamp, expiration FROM cache_data
#         WHERE cache_key = ?
#         ''', (cache_key,))
#         result = self.cursor.fetchone()

#         if result:
#             data, timestamp, expiration = result
#             current_time = int(time.time())
#             if current_time - timestamp > expiration:
#                 # 缓存过期，删除缓存
#                 self.cursor.execute('DELETE FROM cache_data WHERE cache_key = ?', (cache_key,))
#                 self.conn.commit()
#                 return None  # 缓存过期，返回空
#             else:
#                 return json.loads(data)  # 返回缓存的数据
#         return None  # 没有缓存

#     def update_cache(self, cache_key, data, expiration):
#         """更新缓存数据"""
#         timestamp = int(time.time())  # 获取当前时间戳
#         self.cursor.execute('''
#         UPDATE cache_data
#         SET data = ?, timestamp = ?, expiration = ?
#         WHERE cache_key = ?
#         ''', (json.dumps(data), timestamp, expiration, cache_key))
#         self.conn.commit()

#     def delete_cache(self, cache_key):
#         """删除缓存数据"""
#         self.cursor.execute('DELETE FROM cache_data WHERE cache_key = ?', (cache_key,))
#         self.conn.commit()

#     def close(self):
#         """关闭数据库连接"""
#         self.conn.close()


# # 使用示例
# if __name__ == "__main__":
#     client = SQLiteClient()

#     # 创建表
#     client.create_table()

#     # 插入缓存
#     cache_key = 'user:123'
#     data = {'name': 'John Doe', 'age': 30}
#     expiration = 3600  # 1小时
#     client.insert_cache(cache_key, data, expiration)

#     # 查询缓存
#     cached_data = client.get_cache(cache_key)
#     print("查询缓存:", cached_data)

#     # 更新缓存
#     updated_data = {'name': 'John Smith', 'age': 31}
#     client.update_cache(cache_key, updated_data, expiration)

#     # 再次查询更新后的缓存
#     cached_data = client.get_cache(cache_key)
#     print("更新后的缓存:", cached_data)

#     # 删除缓存
#     client.delete_cache(cache_key)

#     # 查询已删除的缓存
#     cached_data = client.get_cache(cache_key)
#     print("删除后的缓存:", cached_data)

#     # 关闭连接
#     client.close()
