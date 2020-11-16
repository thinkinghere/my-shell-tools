import os
import signal

from base import BaseCommand


class Command(BaseCommand):
    help = 'Stop MongoDB Process'
    color = 'blue'

    def handle(self, *args, **kwargs):
        cfg = kwargs.pop('cfg')
        server_cfg = cfg['Server']
        pid_path = server_cfg.get('pidfilepath')
        if not os.path.exists(pid_path):
            return 'Not Start Yet'
        with open(pid_path) as f:
            pid = int(f.read().strip())
        # 通常是先kill -15 sleep 之后kill -9 参考：https://github.com/mongodb/mongo/blob/master/debian/init.d
        os.kill(pid, signal.SIGTERM)  # 信号15  not kill -15
        try:
            os.kill(pid, signal.SIGKILL)  # kill -9
        except ProcessLookupError:
            pass
        os.remove(pid_path)  # 删除pid文件
        return 'MongoDB Killed'
