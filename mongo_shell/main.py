import os
import sys
import readline
import configparser
import crayons
import pkgutil
from importlib import import_module
import functools
from difflib import get_close_matches


def find_commands(dir):
    # 获取commands路径下的文件
    # Django的写法https://github.com/django/django/blob/master/django/core/management/__init__.py#L123
    command_dir = os.path.join(dir, 'commands')
    return [name for _, name, is_pkg in pkgutil.iter_modules([command_dir])
            if not is_pkg and not name.startswith('_')]


def load_command_class(name):
    # 通过名字导入类
    module = import_module(f'commands.{name}')  # 导入commands/start等命令的文件
    return module.Command()


@functools.lru_cache(maxsize=None)  # 添加缓存
def get_commands():
    # help 不用添加help.py
    commands = [name for name in find_commands(
        os.path.abspath(os.path.dirname(__file__)))] + ['help']
    return commands


def print_help():
    # help子命令
    # 查看全部的名令
    print(crayons.green(f'Command List: {",".join(get_commands())}', bold=True))


class CommandUtility:
    """
    处理子命令
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.commands = get_commands()  # 获取全部的命令

    def fetch_command(self, subcommand):
        """
        匹配传入的命令并返回相应命令的类klass
        """
        commands = self.commands  # 全部的命令
        if subcommand not in commands:
            print(crayons.red(f'Unknown command: {subcommand}'))  # 在整体的命令列表中未发现当前命令
            possible_matches = get_close_matches(subcommand, commands)  # 模糊匹配命令
            if possible_matches:
                print(f'Did you mean {possible_matches[0]}?')  # 打印最佳匹配
            print('Type help for usage.')
            return False
        klass = load_command_class(subcommand)  # 通过文件名称加载类
        return klass

    def execute(self, argv):
        """
        argv 传入的是命令的列表
        """
        try:
            subcommand = argv[0]
        except IndexError:  # 对列表索引处理
            subcommand = 'help'

        if subcommand == 'help':
            if len(argv) == 1:
                print_help()
            else:
                cmd_cls = self.fetch_command(argv[1])  # ['help', 'status'] 用于处理多个命令 help status/start/stop
                if cmd_cls:
                    # 打印子命令的帮助信息
                    cmd_cls.print_help()  # 每个命令继承的basecommand中实现的 print(cmd_cls.help) # 默认会打印命令中的help的值 == cmd_cls.help
        else:
            cmd_cls = self.fetch_command(subcommand)
            if cmd_cls:
                # print('cmd_cls argv:', argv)
                print(cmd_cls.execute(argv[1:], cfg=self.cfg))  # cfg=self.cfg 重新将类传入


class Shell:
    """
    MongoDB Shell Manager:
    """

    # 终端提示
    PROMPT = crayons.green('root', bold=True) + crayons.red('#MongoDB: ', bold=True)

    def __init__(self, config_file='config.ini'):
        self.cfg = configparser.ConfigParser()
        self.cfg.read(config_file)  # 读配置文件
        self.utility = CommandUtility(self.cfg)  # 初始化加载CommandUtility
        self.subcommands = self.utility.commands  # 命令行输入的命令

    def sereve_forver(self):
        """
        一直运行
        :return:
        """

        # 自动补全
        readline.set_completer(self._completer)  # 自动补全函数
        readline.parse_and_bind('tab: complete')
        while 1:
            # cmd = '' 后面添加了continue
            try:
                cmd = input(self.PROMPT)
            except EOFError:  # 捕获Ctrl+D
                print(crayons.green('\nExit!'))
                sys.exit(0)  # 使用sys中的exit退出
            except KeyboardInterrupt:  # Ctrl+C
                print(crayons.yellow('\ntype ctrl+D to exit MongoDB Shell'))
                continue
            if cmd:
                # 执行命令
                # print("cmd is:{}".format(cmd))
                self.utility.execute(cmd.split())  # split 生成列表传入

    def _completer(self, word, index):
        """
        自动补全函数
        readline.set_completer ipython 也是同样如此
        :return:
        """
        matches = [c for c in self.subcommands if c.startswith(word)]  # 通过字母开头匹配命令
        try:
            return matches[index] + ''  # 拼接tab
        except IndexError:  # 检查索引错误
            pass


if __name__ == '__main__':
    shell = Shell()
    shell.sereve_forver()
