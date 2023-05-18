#     -*-    coding: utf-8   -*-
# @File     :       logger.py
# @Time     :       2023/5/17 13:04
# Author    :       摸鱼呀阿凡
# Contact   :       f2095522823@gmail.com
# License   :       MIT LICENSE
import logging
from logging.handlers import RotatingFileHandler
import datetime


def setup_logger():
    # 创建日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)

    # 创建按文件大小切割的文件处理器
    date_suffix = datetime.datetime.now().strftime("%Y-%m-%d")
    max_file_size = 5 * 1024 * 1024  # 5 MB
    backup_count = 5
    size_file_handler = RotatingFileHandler(f'log/app.log_{date_suffix}.log', maxBytes=max_file_size, backupCount=backup_count)
    size_file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
    size_file_handler.setFormatter(file_formatter)

    # 将处理器添加到记录器
    logger.addHandler(console_handler)
    logger.addHandler(size_file_handler)


def get():
    import os
    if not os.path.exists('log'):
        os.makedirs('log')
    setup_logger()
    logger = logging.getLogger()
    return logger
