import socket
import crayons
from base import BaseCommand


class Command(BaseCommand):
    help = 'Show MongoDB"s status'
    color = 'magenta'

    def handle(self, *args, **kwargs):
        cfg = kwargs.pop('cfg')
        server_cfg = cfg['Server']
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 通过socket连接判断服务运行情况
        bind_ip = server_cfg.get('bind_ip')
        port = int(server_cfg.get('port'))
        try:
            s.connect(
                (bind_ip, port)
            )
            return f'Running on {bind_ip}:{port}'
        except ConnectionRefusedError as e:
            print(crayons.red(f'connect err: {e}'))
            return f"Mongodb Stopped"

