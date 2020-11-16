import struct
import socket
import time

HOST = '127.0.0.1'
PORT = 9001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))


def send_msg(self, message):
    print(f'send message is : {message}')
    message = struct.pack('>I', len(message)) + bytes(message, 'utf-8')  # 前4个字节是数据长度+后面的内容
    print(f'pack message is : {message}')
    sock.send(message)
    response = sock.recv(1024)
    return response


def client():
    # while 1:
    #     nick_name = input("Please input")
    #     if nick_name:
    #         break
    # resp = send_msg(sock, f'/set {nick_name}')  # 数据拼接/set 头,增加5个字节
    # print(resp)
    while 1:
        resp = send_msg(sock, f'/list')
        print(resp)
        time.sleep(0.5)
    #
    # resp = send_msg(sock, f'/quit')
    # print(resp)
    # try:
    #     resp = send_msg(sock, f'/set hello')
    #     print(resp)
    # except ConnectionError as e:
    #     print('connect err is: {e}')


if __name__ == '__main__':
    client()
