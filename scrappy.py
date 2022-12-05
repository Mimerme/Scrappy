import pdb
from curses import wrapper
from seleniumwire import webdriver  # Import from seleniumwire
import argparse
import pickle
import time
import curses
from curses.textpad import Textbox, rectangle

import logging
from logger import setup_log
setup_log()


MAX_LEVEL = 2

class RequestBrowser:
    def __init__(self, nested_dict):
        self.requests = nested_dict
        self.run = True

    def render_loop(self, stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        height, width = stdscr.getmaxyx()
        level = 0
        show_preview = False

        url_pad = curses.newpad(len(self.requests), width)
        url_pad.scrollok(True)
        request_pad = curses.newpad(height, width)
        args_pad = curses.newpad(height, width)

        url_browser = CursesListWidget()
        request_browser = CursesListWidget()
        arg_browser = CursesListWidget()

        url_browser.init_list_widget(self.requests)

        while self.run:
            stdscr.clear()
            url_pad.clear()
            request_pad.clear()
            args_pad.clear()
            selected_url = url_browser.render_list_widget(stdscr, url_pad)

            if not show_preview:
                if level >= 1:
                    if not request_browser.list:
                        request_browser.init_list_widget(selected_url)
                    selected_request = request_browser.render_list_widget(stdscr, request_pad, depth=5)

                    logging.info(selected_request)
                    if level >= 2:
                        if not arg_browser.list:
                            arg_browser.init_list_widget(selected_request)
                        selected_arg = arg_browser.render_list_widget(stdscr, args_pad, depth=10)
                # elif show_preview and level == 0:
                #     request_browser.init_list_widget(selected_url)
                #     request_browser.render_list_widget(stdscr, request_pad, depth=5)
            else:
                if level == 0:
                    request_browser.init_list_widget(selected_url)
                    selected_request = request_browser.render_list_widget(stdscr, request_pad, depth=5)

                elif level== 1:
                    selected_request = request_browser.render_list_widget(stdscr, request_pad, depth=5)
                    arg_browser.init_list_widget(selected_request)
                    selected_arg = arg_browser.render_list_widget(stdscr, args_pad, depth=10)

            key = url_pad.getkey()


            # handle widget movement first
            if key == "/":
                show_preview = not show_preview
            if key == "q":
                self.run = False



            if ord(key) == 10:
                level += 1
                if level > MAX_LEVEL:
                    level = MAX_LEVEL
            elif ord(key) == 27:
                if level == 2:
                    arg_browser.list = None
                elif level == 1:
                    request_browser.list = None

                level -= 1

                if level < 0:
                    level = 0

            if level >= 2:
                arg_browser.input_list_widget(key)
            elif level >= 1:
                request_browser.input_list_widget(key)
            elif level == 0:
                url_browser.input_list_widget(key)




class CursesListWidget:
    def __init__(self):
        self.list = None
        self.selected = 0


    def init_list_widget(self, list):
        self.selected = 0
        self.list = list

    def render_list_widget(self, main, pad, depth=1):
        ret = None
        height, width = main.getmaxyx()

        if type(self.list) == list:
            for i in range(0, len(self.list)):
                r = str(self.list[i])[:width-1]

                if i == self.selected:
                    ret = self.list[i]
                    pad.addstr(i, 0, r, curses.color_pair(1))
                else:
                    pad.addstr(i, 0, r, curses.color_pair(0))
        elif type(self.list) == dict:
            i = 0
            for (k, v) in self.list.items():
                r = str(k)[:width-1]

                if i == self.selected:
                    ret = v
                    pad.addstr(i, 0, r, curses.color_pair(1))
                else:
                    pad.addstr(i, 0, r, curses.color_pair(0))
                i += 1
        else:
            pad.addstr(0, 0, str(self.list), curses.color_pair(1))
            # raise Exception(f"Unsupported value for self.list '{self.list}'")

        rectangle(main, depth, depth - 1, height - 1 - depth, width - 2)
        main.refresh()
        pad.refresh(self.selected, 0, depth + 1, depth, height - 2 - depth, width - 3)
        return ret

    def input_list_widget(self, key):
        if key == 'j':
            self.selected += 1
        elif key == "k":
            if self.selected > 0:
                self.selected -= 1
        elif key == "h":
            return
        elif key == "l":
            return
        else:
            return


class ScrappyCli(pdb.Pdb):
    recording = False
    captured_requests = {}
    def __init__(self, *args, **kwargs):
        super(ScrappyCli, self).__init__(*args, **kwargs)
        self.prompt = "[Scrappy] > "



    def do_startrecord(self, *args):
        self.name = args[0]
        print(f"Starting recording {self.name}")
        self.recording = True
    def do_stoprecord(self, *args):
        print(f"Stopping recording {self.name}. Captured {len(self.captured_requests[self.name])} requests")
        self.name = ""
        self.recording = False
        requests = self.captured_requests[self.name]

    def do_saveproj(self, *args):
        loc = args[0]
        print(f"Saving project to {loc}")
        pickle.dump(self.captured_requests, loc)
    def do_loadproj(self, *args):
        loc = args[0]
        print(f"Loading project from {loc}")
        self.captured_requests = pickle.load(loc)

    def do_browse(self, *args):
        # format the requests into a clean dictionary
        format_reqs = list(map(lambda x: vars(x), self.captured_requests[self.name]))

        browser = RequestBrowser(format_reqs)
        wrapper(browser.render_loop)

    def on_request(self, request):
        if self.recording:
            if not self.name in self.captured_requests:
                self.captured_requests[self.name] = []
            self.captured_requests[self.name].append(request)


parser = argparse.ArgumentParser(
    prog = 'Scrappy',
    description = 'Filter/Charles alternative via Selenium',
    epilog = 'Copyright lolol')
parser.add_argument('-d', '--data-dir')
args = parser.parse_args()

if __name__ == "__main__":
    print("Initializing Scrappy")
    scrappy = ScrappyCli()

    print("Waiting for webdriver...")
    driver = webdriver.Firefox()
    driver.request_interceptor = scrappy.on_request

    scrappy.set_trace()