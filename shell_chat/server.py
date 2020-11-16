import re
import json
import struct
import socket
import selectors

HOST = '127.0.0.1'
PORT = 9001
SERIAL_ID = 1000
USER_MAP = {}
MENTION_REGEX = re.compile(r'@(.*?)\W+(.*)')  # 匹配@

sel = selectors.DefaultSelector()


class ChatServer:
    def __init__(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)  # 设置非阻塞
        sock.bind((host, port))  # 元组
        sock.listen(5)
        self.sock = sock

    def read(self, conn, mask):
        try:
            chunk = conn.recv(4)  # 数据长度
        except ConnectionError:
            return
        if len(chunk) < 4:
            return
        addr = conn.getpeername()  # 获取对端的地址 端口 例子：('127.0.0.1', 65406)
        # print('conn.getpeername():', conn.getpeername())  # 获取的是客户端的信息
        # print('conn.getsockname()', conn.getsockname())  # 获取当前sock对象的连接

        # 数据的前4字节是数据的长度
        # print(f"读取到的数据长度:", struct.unpack('>L', chunk))
        slen = struct.unpack('>L', chunk)[0]  # [0] 是数据的长度 >:字节顺序采用大端 L:unsigned long 如：5hello-> 5 slen = 5
        # print(f'read data unpack slen is: {slen}')
        chunk = conn.recv(slen)  # conn.recv(5)
        while len(chunk) < slen:
            # 当前已经获取的 + 剩余的数据
            chunk = chunk + conn.recv(slen - len(chunk))  # chunk + conn.recv(5 - len(chunk)) # 处理接收大文件

        chunk = chunk.decode('utf-8')  # 字节流转换成str

        # 设置默认的用户 开始是从1000 之后自增
        if addr not in USER_MAP:
            global SERIAL_ID
            self.set_username(addr, f'User{SERIAL_ID}')
            SERIAL_ID += 1

        # 解析数据
        if chunk.startswith('/set'):  # 设置用户昵称
            name = chunk.split()[1]
            self.set_username(addr, name)
            conn.sendall(bytes(chunk, 'utf8'))  # 将数据返回客户端  客户端进行处理  conn.sendall(bytes(chunk, 'utf-8'))  # 必须要返回数据 否则会夯住
        elif chunk == '/list':
            send_data = json.dumps(self.get_user_list()).encode('utf-8')
            conn.sendall(send_data)  # 将用户列表转换成字节
        elif chunk == '/quit':  # 退出
            print('==================quit==================')
            sel.unregister(conn)  # 取消注册
            conn.close()
        else:
            # 在不是以上命令时候判读是否是@别人
            match = MENTION_REGEX.search(chunk)
            if match:
                # print(USER_MAP, 111)  # {('127.0.0.1', 64417): 'aa'}
                username, content = match.groups()  # @的用户及内容
                # print(f're match:  {username}, {content}')
                if username == 'all':  # @所有人 广播
                    self.broadcast(f'@all {content}')
                else:
                    sock = self.get_socket(username)  # 拿到用户的socket
                    if not sock:
                        conn.sendall(b'User not exists')
                    else:
                        sock.sendall(bytes(f'@{self.get_username(addr)} Say: {content}', 'utf-8'))

    @staticmethod
    def set_username(addr, name):
        """
        /set
        设置用户的用户名
        """
        USER_MAP[addr] = name

    @staticmethod
    def get_user_list():
        """
        /list
        获取用户列表
        """
        return list(USER_MAP.values())  # Python3中values() 默认不是列表

    @staticmethod
    def get_username(conn):
        res = next((name for conn_, name in USER_MAP.items() if conn_ == conn), None)
        return res

    def get_socket(self, username):
        """
        参考register保存sock的关系
        socket就是fileobj
        """
        addr = next((conn for conn, name in USER_MAP.items() if name == username), None)
        for fd in sel._fd_to_key.values():  # values
            sock = fd.fileobj
            if sock == self.sock:
                continue  # 把自身的sock忽略
            addr_ = sock.getpeername()  # 获取地址
            if addr == addr_:
                return sock

    def broadcast(self, content):
        """发送广播"""
        if not isinstance(content, bytes):
            content = bytes(content, 'utf8')  # 将数据转换为bytes
        for fd in sel._fd_to_key.values():
            sock = fd.fileobj
            if sock == self.sock:
                continue  # 把自身的sock忽略
            fd.fileobj.sendall(content)  # fd.fileobj == sock

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        print(f'Connected by {addr}')
        conn.setblocking(0)
        sel.register(conn, selectors.EVENT_READ, self.read)

    def serve_forever(self):
        sel.register(self.sock, selectors.EVENT_READ, self.accept)

        while 1:
            events = sel.select(0.5)
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)


if __name__ == '__main__':
    print(f'Server start at {HOST}:{PORT}')
    server = ChatServer(HOST, PORT)
    server.serve_forever()
