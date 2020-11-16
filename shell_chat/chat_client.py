from curses import wrapper

from chat_ui import ChatUI

HOST = 'localhost'
PORT = 9001


def main(stdscr):
    stdscr.clear()
    ui = ChatUI(HOST, PORT, stdscr)
    ui.run_forever()


if __name__ == '__main__':
    wrapper(main)
