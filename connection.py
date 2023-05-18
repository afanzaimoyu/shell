#     -*-    coding: utf-8   -*-
# @File     :       connection.py
# @Time     :       2023/5/17 13:01
# Author    :       摸鱼呀阿凡
# Contact   :       f2095522823@gmail.com
# License   :       MIT LICENSE
import os
import paramiko
import uuid


class ConnectionManager:
    def __init__(self, log):
        self.log = log
        self.connected = False
        self.ssh = None
        self.current_directory = None

    def connect(self, ip, username, password):
        """连接远程服务器"""
        self.log.info("正在连接中%s%s%s", ip, username, password)
        # 实现连接的具体逻辑
        try:
            # 实例化远程连接的客户端
            self.ssh = paramiko.SSHClient()
            # 设置know_hosts文件添加策略为自动添加（自动输入yes）
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            # 连接远程服务器
            self.ssh.connect(hostname=ip, port=22, username=username, password=password)
            self.connected = True  # 连接成功后设置为True

        except paramiko.AuthenticationException:
            self.log.error("身份验证失败，请检查用户名和密码是否正确")
        except paramiko.SSHException as e:
            self.log.error(f"SSH连接错误：{str(e)}")
        except Exception as e:
            self.log.error(f"连接错误：{str(e)}")
        return self.connected

    def execute_remote_command(self, command):
        """执行远程指令并返回结果"""
        if not self.connected:
            return None

        try:
            if self.current_directory is None:
                # 第一次执行命令时获取当前工作目录
                self.current_directory = self.ssh.exec_command("pwd")[1].read().decode("utf-8").strip()
            # 获取当前用户和主机名
            current_user = self.ssh.exec_command("whoami")[1].read().decode("utf-8").strip()
            hostname = self.ssh.exec_command("hostname")[1].read().decode("utf-8").strip()

            prompt = ""
            if current_user and self.current_directory and hostname:
                if current_user == "root":
                    prompt += f"[root@{hostname} {self.current_directory}]# "
                else:
                    prompt += f"[{current_user}@{hostname} {self.current_directory}]$ "
            else:
                prompt += "$ "  # 默认提示符

            if command.startswith("cd"):
                # 处理cd命令
                cd_directory = command[3:].strip()  # 提取cd命令中的目录部分
                target_directory = os.path.join(self.current_directory, cd_directory).replace("\\", "/")
                full_command = f"cd {target_directory} && pwd"
                stdin, stdout, stderr = self.ssh.exec_command(full_command)
                result = stdout.read().decode("utf-8").strip()
                if result == target_directory:
                    # 目录切换成功，更新当前工作目录
                    self.current_directory = result
                    self.log.info(f"新的工作目录为：{self.current_directory}")
                    self.log.info(f"目录拼接：{self.current_directory}--{cd_directory} ={target_directory}")
                else:
                    # 目录切换失败，保持当前工作目录不变
                    self.log.warning(f"无法切换到目录：{target_directory}")

                resp = prompt + command
            elif command == "clear":
                resp = command
            else:
                # 在每个命令之前都添加cd命令以保持工作目录
                full_command = f"cd {self.current_directory} && {command}"
                stdin, stdout, stderr = self.ssh.exec_command(full_command)
                result = stdout.read().decode("utf-8")

                self.log.info(f"命令已执行: {prompt}{command} -- 结果: {result}")
                resp = prompt + command + "\n" + result
            return resp
        except Exception as e:
            self.log.error(f"执行远程指令时出现错误：{str(e)}")
            return None

    def upload_file(self, local_file, remote_file):
        """上传文件到远程服务器"""
        remote_file += '/' + os.path.basename(local_file)  # 添加文件名称到路径中
        self.log.info(f"本地文件{local_file}:远程文件{remote_file}")
        if not self.connected:
            self.log.warning("未连接到远程服务器")
            return

        try:
            sftp = self.ssh.open_sftp()
            sftp.put(local_file, remote_file)
            sftp.close()
            self.log.info(f"文件上传成功：{local_file} -> {remote_file}")
            return True
        except Exception as e:
            self.log.error(f"文件上传失败：{str(e)}")
            return False
            # # 打印详细的错误信息
            # import traceback
            # traceback.print_exc()

    def download_file(self, remote_file, local_file):
        """从远程服务器下载文件"""
        if not self.connected:
            self.log.warning("未连接到远程服务器")
            return
        self.log.info(f"本地文件{local_file}:远程文件{remote_file}")
        try:
            sftp = self.ssh.open_sftp()
            sftp.get(remote_file, local_file)
            sftp.close()
            self.log.info(f"文件下载成功：{remote_file} -> {local_file}")
            return True
        except Exception as e:
            self.log.error(f"文件下载失败：{str(e)}")
            return False

    def list_files(self, remote_directory):
        """列出远程路径下的文件"""
        if not self.connected:
            self.log.warning("未连接到远程服务器")
            return []

        try:
            sftp = self.ssh.open_sftp()
            file_list = sftp.listdir(remote_directory)
            sftp.close()
            self.log.info(f"成功列出远程路径下的文件：{remote_directory}")
            return file_list
        except Exception as e:
            self.log.error(f"列出远程路径下的文件失败：{str(e)}")
            return []

    def get_file_content(self, remote_file):
        """获取远程服务器上文件的内容"""
        if not self.connected:
            self.log.warning("未连接到远程服务器")
            return None

        try:
            # 使用cat命令获取文件内容
            stdin, stdout, stderr = self.ssh.exec_command(f"cat {remote_file}")
            content = stdout.read().decode("utf-8")
            return content
        except Exception as e:
            self.log.error(f"获取文件内容时出现错误：{str(e)}")
            return None

    def save_file_content(self, content, remote_file):
        """保存编辑后的文件内容到远程服务器"""

        try:
            # 将文件内容写入到临时文件
            temp_file = f"{uuid.uuid4().hex}"
            with open(temp_file, "w",encoding='utf-8') as f:
                f.write(content)

            # 将临时文件复制到远程服务器上的目标文件
            sftp = self.ssh.open_sftp()
            self.log.info(f"保存{temp_file}文件内容到远程服务器时将复制到{remote_file}")
            sftp.put(temp_file, remote_file)

            # 删除临时文件
            os.remove(temp_file)

            self.log.info(f"文件保存成功：{remote_file}")
            return True
        except Exception as e:
            self.log.error(f"保存文件时出现错误：{str(e)}")
            return False

    def disconnect(self):
        """断开连接"""
        self.log.info("正在断开连接")

        # 实现断开连接的具体逻辑
        try:
            if self.connected:
                self.ssh.close()
                self.log.info("连接已断开")
            else:
                self.log.info("未连接到远程服务器")
        except Exception as e:
            self.log.error(f"断开连接时出现错误：{str(e)}")
        self.connected = False
