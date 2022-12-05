# For testing the UI without launcvching the webdriver

from scrappy import RequestBrowser
from curses import wrapper
requests = ["Placeholder"]

#requests = [[f"args{x}", "vargs", "whatever"] for x in range(300)]
requests = {f"yo{x}":[f"args{x}", {"test": ["test1", "test2"]}, "whatever"] for x in range(300)}
browser = RequestBrowser(requests)
wrapper(browser.render_loop)

