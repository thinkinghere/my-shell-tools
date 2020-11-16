import curses
import sys
import json
import time
import struct
import socket
from threading import Thread

MSG_SIZE = 4096


class ChatUI:
    name = ''
    user_list = []

    def __init__(self, host, port, stdscr, userlist_width=24):
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i, i, -1)
        self.stdscr = stdscr
        self.inputbuffer = ""
        self.linebuffer = []
        self.chatbuffer = []

        # Curses, why must you confuse me with your height, width, y, x
        # userlist_hwyx = (curses.LINES - 2, userlist_width - 1, 0, 0)
        # chatbuffer_hwyx = (curses.LINES - 2, curses.COLS - userlist_width - 1, 0, userlist_width + 1)

        userlist_hwyx = (curses.LINES - 2, userlist_width - 1, 0, curses.COLS - userlist_width + 1)
        chatbuffer_hwyx = (curses.LINES - 2, curses.COLS - userlist_width - 2, 0, 0)
        chatline_yx = (curses.LINES - 1, 0)
        self.win_userlist = stdscr.derwin(*userlist_hwyx)
        self.win_chatline = stdscr.derwin(*chatline_yx)
        self.win_chatbuffer = stdscr.derwin(*chatbuffer_hwyx)

        self.redraw_ui()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        self.sock = sock

    def resize(self):
        """Handles a change in terminal size"""
        u_h, u_w = self.win_userlist.getmaxyx()
        h, w = self.stdscr.getmaxyx()

        self.win_chatline.mvwin(h - 1, 0)
        self.win_chatline.resize(1, w)

        self.win_userlist.resize(h - 2, u_w)
        self.win_chatbuffer.resize(h - 2, w - u_w - 2)

        self.linebuffer = []
        for msg in self.chatbuffer:
            self._linebuffer_add(msg)

        self.redraw_ui()

    def redraw_ui(self):
        """Redraws the entire UI"""
        h, w = self.stdscr.getmaxyx()
        # u_h, u_w = self.win_userlist.getmaxyx()  # 用户列表
        u_h, u_w = self.win_chatbuffer.getmaxyx()  # 消息列表
        self.stdscr.clear()
        self.stdscr.vline(0, u_w + 1, "|", h - 2)
        self.stdscr.hline(h - 2, 0, "-", w)
        self.stdscr.refresh()

        self.redraw_userlist()
        self.redraw_chatbuffer()
        self.redraw_chatline()

    def redraw_chatline(self):
        """Redraw the user input textbox"""
        h, w = self.win_chatline.getmaxyx()
        self.win_chatline.clear()
        start = len(self.inputbuffer) - w + 1
        if start < 0:
            start = 0
        self.win_chatline.addstr(0, 0, self.inputbuffer[start:])
        self.win_chatline.refresh()

    def redraw_userlist(self):
        """Redraw the userlist"""
        self.win_userlist.clear()
        h, w = self.win_userlist.getmaxyx()
        for i, name in enumerate(self.user_list):
            if i >= h:
                break
            # name = name.ljust(w - 1) + "|"
            self.win_userlist.addstr(i, 0, name[:w - 1])
        self.win_userlist.refresh()

    def redraw_chatbuffer(self):
        """Redraw the chat message buffer"""
        self.win_chatbuffer.clear()
        h, w = self.win_chatbuffer.getmaxyx()
        j = len(self.linebuffer) - h
        if j < 0:
            j = 0
        for i in range(min(h, len(self.linebuffer))):
            self.win_chatbuffer.addstr(i, 0, self.linebuffer[j])
            j += 1
        self.win_chatbuffer.refresh()

    def chatbuffer_add(self, msg):
        """

        Add a message to the chat buffer, automatically slicing it to
        fit the width of the buffer

        """
        self.chatbuffer.append(msg)
        self._linebuffer_add(msg)
        self.redraw_chatbuffer()
        self.redraw_chatline()
        self.win_chatline.cursyncup()

    def _linebuffer_add(self, msg):
        h, w = self.stdscr.getmaxyx()
        u_h, u_w = self.win_userlist.getmaxyx()
        w = w - u_w - 2
        while len(msg) >= w:
            self.linebuffer.append(msg[:w])
            msg = msg[w:]
        if msg:
            self.linebuffer.append(msg)

    def prompt(self, msg):
        """Prompts the user for input and returns it"""
        self.inputbuffer = msg
        self.redraw_chatline()
        res = self.wait_input()
        res = res[len(msg):]
        return res

    def wait_input(self, prompt=""):
        """

        Wait for the user to input a message and hit enter.
        Returns the message

        """
        self.inputbuffer = prompt
        self.redraw_chatline()
        self.win_chatline.cursyncup()
        last = -1
        index = 0
        while last != ord('\n'):
            last = self.stdscr.getch()
            if last == ord('\n'):
                tmp = self.inputbuffer
                self.inputbuffer = ""
                self.redraw_chatline()
                self.win_chatline.cursyncup()
                return tmp[len(prompt):]
            elif last == curses.KEY_BACKSPACE or last == 127:
                if len(self.inputbuffer) > len(prompt):
                    self.inputbuffer = self.inputbuffer[:-1]
            elif last == curses.KEY_RESIZE:
                self.resize()
            elif 32 <= last <= 126:
                self.inputbuffer += chr(last)
            elif last == 9:  # tab 的值是9
                if '@' not in self.inputbuffer:
                    continue
                parts = self.inputbuffer.split('@')
                # 自动补全 取值的时候注意IndexError
                try:
                    word = parts[1].split()[0]
                except IndexError:
                    continue

                matches = [c for c in self.user_list if c.startswith(word)]
                if matches:
                    try:
                        self.inputbuffer = f'{parts[0]}@{matches[index]}'
                    except IndexError:
                        pass
                    index += 1
            self.redraw_chatline()

    def send_msg(self, message):
        message = struct.pack('>I', len(message)) + bytes(message, 'utf-8')  # 前4个字节是数据长度+后面的内容
        self.sock.send(message)

    def recv_handle(self):
        while 1:
            data = self.sock.recv(MSG_SIZE)
            if data:
                data = data.decode('utf-8')
                if data.startswith('['):
                    self.user_list = json.loads(data)
                    self.redraw_userlist()
                elif data.startswith('/set'):
                    self.name = data.split()[1]
                else:
                    self.chatbuffer_add(data)  # inputbuffer 显示聊天内容
            time.sleep(0.5)

    def send_handle(self):
        while 1:
            text = self.wait_input(f'{self.name} > ')  # wait_input获取输入
            self.send_msg(text)
            self.chatbuffer_add(text)
            if text == '/quit':
                sys.exit(0)

    def update_user_list(self):
        while 1:
            time.sleep(3)
            self.send_msg('/list')

    def _run(self):

        threads = []
        for func in (self.recv_handle, self.update_user_list):
            t = Thread(target=func)
            t.setDaemon(True)
            t.start()
            threads.append(t)

        while 1:
            nick_name = self.wait_input('Username: ')  # wait_input获取输入
            if nick_name:
                break

        self.send_msg(f'/set {nick_name}')
        self.name = nick_name

        self.send_handle()

        for t in threads:
            t.join()

    def run_forever(self):
        try:
            self._run()
        except (EOFError, KeyboardInterrupt):  # 获取退出的信号
            self.send_msg('/quit')
