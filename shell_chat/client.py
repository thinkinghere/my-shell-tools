import json
import readline
import struct
import socket
import sys
import time
from threading import Thread

HOST = '127.0.0.1'
PORT = 9001
MSG_SIZE = 4096


class ChatClient:
    name = ''
    user_list = []

    def __init__(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        self.sock = sock

    def send_msg(self, message):
        message = struct.pack('>I', len(message)) + bytes(message, 'utf-8')  # 前4个字节是数据长度+后面的内容 I代表4字节无符号整数
        self.sock.send(message)
        # response = self.sock.recv(1024)  # 这里会造成阻塞
        # return response

    def recv_handle(self):
        """接收服务端数据"""
        while 1:
            data = self.sock.recv(MSG_SIZE)
            if data:
                data = data.decode('utf-8')
                # 反序列化数据
                if data.startswith('['):
                    self.user_list = json.loads(data)
                    # print(self.user_list)
                elif data.startswith('/set'):
                    # /set 用于接受处理服务端返回的数据
                    self.name = data.split()[1]  # 获取数据中的姓名
                else:
                    print(data)  # 展示返回的数据
            time.sleep(0.5)

    def send_handle(self):
        """向服务端发送用户数据"""
        # 自动补全
        readline.set_completer(self._completer)  # 自动补全函数
        readline.parse_and_bind('tab: complete')
        while 1:
            text = input(f'{self.name} > ')
            self.send_msg(text)
            if text == '/quit':
                sys.exit(0)

    def update_user_list(self):
        """定期更新userlist"""
        while 1:
            time.sleep(3)  # 修改相应的时间 让用户名显示
            self.send_msg('/list')

    def run(self):
        """
        多线程运行
        recv_handle
        update_user_list
        """
        threads = []
        # 将recv_handle 和 update_user_list 添加到多线程中
        for func in (self.recv_handle, self.update_user_list):
            t = Thread(target=func)
            t.setDaemon(True)
            t.start()
            threads.append(t)

        while 1:
            nick_name = input("Please input Your Name:")
            if nick_name:
                break

        self.send_msg(f'/set {nick_name}')  # 数据拼接/set 头,增加5个字节
        self.name = nick_name
        self.send_handle()
        for t in threads:
            t.join()

    # 自动补全
    def _completer(self, word, index):
        if not word:
            return
        matches = [c for c in self.user_list if c.startswith(word)]
        try:
            return matches[index]
        except IndexError:
            pass


if __name__ == '__main__':
    client = ChatClient(HOST, PORT)
    client.run()
