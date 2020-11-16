import os
import subprocess

import crayons

from base import BaseCommand

MONGODBD_PATH = '/usr/local/mongodb/bin/mongod'


class Command(BaseCommand):
    help = 'Start MongoDB Process'
    color = 'cyan'

    def handle(self, *args, **kwargs):
        cfg = kwargs.pop('cfg')
        server_cfg = dict(cfg['Server'].items())  # 将config对象转换成字典
        pid_path = server_cfg.get('pidfilepath')
        # print(pid_path)
        # print(os.path.exists(pid_path))
        if os.path.exists(pid_path):
            with open(pid_path) as f:
                if f.read():
                    return 'MongoDB Already Started'
        try:
            command = ('{mongod_path} --port={port} --bind_ip={bind_ip} '
                       '--logpath={logpath} --dbpath={dbpath} --fork '
                       '--pidfilepath={pidfilepath}').format(
                       mongod_path=MONGODBD_PATH, **server_cfg)  # 字典解析
            # print(server_cfg)
            subprocess.check_output(command, shell=True)  # 执行命令 返回值不为0抛出异常
            return 'Mongodb Started'
        except subprocess.CalledProcessError as e:
            print(crayons.red(f'Start MongoDB Process err: {e}'))
            return 'Mongodb Failed'


