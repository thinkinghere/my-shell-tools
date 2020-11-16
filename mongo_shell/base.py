import crayons


# 不同的命令不同的颜色

class CommandError(Exception):
    ...


class BaseCommand:
    """
    Command基类
    """
    help = 'Default Help Message'
    color = 'white'

    @property
    def color_cls(self):
        return getattr(crayons, self.color)

    def print_help(self):
        print(self.help)

    def execute(self, *args, **kwargs):
        output = self.handle(*args, **kwargs)
        bold = kwargs.pop('bold', False)
        return self.color_cls(output, bold=bold)

    def handle(self, *args, **kwargs):
        """
        在子类中去实现
        """
        raise NotImplementedError(
            'subclass of BaseCommand must provide a handle() method')
