#     -*-    coding: utf-8   -*-
# @File     :       saved_info.py
# @Time     :       2023/5/17 13:02
# Author    :       摸鱼呀阿凡
# Contact   :       f2095522823@gmail.com
# License   :       MIT LICENSE
import sqlite3
import os


class SavedInfoManager:
    def __init__(self,log):
        self.log = log
        self.db_file = 'dbs/saved_info.db'
        #如果不存在dbs文件夹就创建一个
        if not os.path.exists('dbs'):
            os.makedirs('dbs')
        if not os.path.exists(self.db_file):
            # 如果数据库文件不存在，则创建一个新的数据库文件
            try:
                conn = sqlite3.connect(self.db_file)
                conn.close()
                self.add_table()
            except Exception as e:
                self.log.error(f'创建数据库文件错误：{str(e)}')

    def add_table(self):
        # 连接到数据库
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            # 创建 saved_info 表
            cursor.execute('''CREATE TABLE IF NOT EXISTS saved_info
                              (ip TEXT, username TEXT, password TEXT)''')
            # 提交更改并关闭连接
            conn.commit()
            conn.close()
        except Exception as e:
            self.log.error(f'创建数据库表错误：{str(e)}')
    def get_saved_info(self):
        saved_info = []
        try:
            connection = sqlite3.connect(self.db_file)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM saved_info")
            saved_info = cursor.fetchall()
            connection.close()
        except Exception as e:
            self.log.error(f'获取保存的信息错误：{str(e)}')
        return saved_info

    def add_saved_info(self, ip, username, password):
        try:
            connection = sqlite3.connect(self.db_file)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO saved_info (ip, username, password) VALUES (?, ?, ?)", (ip, username, password))
            connection.commit()
            connection.close()
        except Exception as e:
            self.log.error(f'添加保存的信息错误：{str(e)}')

    def remove_saved_info(self, ip, username, password):
        try:
            connection = sqlite3.connect(self.db_file)
            cursor = connection.cursor()
            cursor.execute("DELETE FROM saved_info WHERE ip=? AND username=? AND password=?", (ip, username, password))
            connection.commit()
            connection.close()
        except Exception as e:
            self.log.error(f'移除保存的信息错误：{str(e)}')
