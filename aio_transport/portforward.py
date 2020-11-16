"""
ref:
    Python 3.6:
        18.5.4.3.2. TCP echo server protocol
        https://docs.python.org/3.6/library/asyncio-protocol.html

    Python 3.7
        asyncio 使用了新的运行方式

        ```py3.7
        async def main():
            loop = asyncio.get_running_loop()
            server = await loop.create_server(
                lambda: EchoServerProtocol(),
                '127.0.0.1', 8888)

            async with server:
                await server.serve_forever()
        asyncio.run(main())
        ```

方法：
    传输层协议进行端口转发 参考Twisted
    connection_made: 初始化连接成功后的生命周期
    data_received: 收到数据
    connection_lost: 连接丢失

测试：
    使用http://httpbin.org/测试

使用asyncio debug
    doc:
        https://docs.python.org/3.6/library/asyncio-dev.html#debug-mode-of-asyncio
    PYTHONASYNCIODEBUG to 1
"""

import asyncio
import argparse


class ForwardedProtocol(asyncio.Protocol):
    """
    协议
    connection_made 发生在data_received之前
    """

    def __init__(self, peer):
        self.peer = peer
        self.transport = None
        self.buffers = []  # 用于缓存数据

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        if len(self.buffers):
            self.transport.writelines(self.buffers)
            self.buffers = []

    def data_received(self, data):
        print('对端返回的数据resp', data)
        message = data.decode()  # noqa
        print("resp message", message)
        self.peer.write(data)

    def connection_lost(self, exc):
        """
        关闭连接
        """
        self.peer.close()


class PortForwarded(asyncio.Protocol):
    """
    端口转发
    """

    def __init__(self, host, port, loop):
        self.host = host
        self.port = port
        self.loop = loop

    def connection_made(self, transport):
        """
        create_connection
            需要lambda
        """
        self.local_port = transport.get_extra_info('sockname')[1]  # 获取本端端口
        self.conn = ForwardedProtocol(transport)
        coro = self.loop.create_connection(lambda: self.conn, self.host, self.port)  # 参考client实现一个协程 需要lambda
        asyncio.ensure_future(coro)  # 将协程封装成一个Task

    def data_received(self, data):
        """
        中间转发 接受本地请求
        """
        print("接收本地请求", data.decode())  # data is bytes
        data = data.decode().replace(f'localhost:{self.local_port}', f'{self.host}:{self.port}').encode()  # 替换请求中的本地地址
        if self.conn.transport is None:
            self.conn.buffers.append(data)
        else:
            self.conn.transport.write(data)

    def connection_lost(self, exc):
        self.conn.transport.close()


parser = argparse.ArgumentParser(description='A port forward command tool using asyncio')
parser.add_argument('-l', dest='local_port', action='store', default=8888, help='The port to bind to.')
parser.add_argument('-s', dest='source', action='store', help='Forward source-address')
parser.add_argument('-p', dest='port', action='store', default=80, help='Forward source-port')

args = parser.parse_args()

if args.source is None:
    print('Plz specify `-s` argumnet!')
    exit()

# python 3.6

# loop = asyncio.get_event_loop()
#
# """
# create_server
#     指定的参数PortForwarded 是个protocol_factory
#     loop.create_server(PortForwarded, '127.0.0.1', 8888)
# """
# coro = loop.create_server(lambda: PortForwarded('httpbin.org', 80), '127.0.0.1', 8888)
#
# server = loop.run_until_complete(coro)
# print('Serving on {}'.format(server.sockets[0].getsockname()))
# try:
#     loop.run_forever()
# except KeyboardInterrupt:
#     pass
#
# server.close()
# loop.run_until_complete(server.wait_closed())
# loop.close()

"""
Python3.7
"""


async def main():
    loop = asyncio.get_running_loop()
    # server = await loop.create_server(lambda: PortForwarded('httpbin.org', 80, loop), '127.0.0.1', 8888)
    server = await loop.create_server(lambda: PortForwarded(args.source, args.port, loop), '127.0.0.1', args.local_port)

    async with server:
        await server.serve_forever()


asyncio.run(main())

