import urllib

from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


class Chrome:
    def __init__(self, chromedriver: str = "", proxy: str = None):
        self.chromedriver = chromedriver

        options = webdriver.ChromeOptions()
        for g in ["--headless", "--log-level=3", "--window-size=1000x1000"]:
            options.add_argument(g)

        if proxy and isinstance(proxy, str):
            options.add_argument(f"--proxy-server={proxy}")

        self.driver = webdriver.Chrome(
            executable_path=self.chromedriver, options=options
        )

        self.session_id = self.driver.session_id
        self.executor_url = self.driver.command_executor._url

    def recycled_driver(self):
        """ Use the current Chrome instance to load faster """
        original_execute = WebDriver.execute

        def new_command_execute(self, command, params=None):
            if command == "newSession":
                # Mock the response
                return {"success": 0, "value": None, "sessionId": self.session_id}
            else:
                return original_execute(self, command, params)

        # Patch the function before creating the driver object
        WebDriver.execute = new_command_execute
        driver = webdriver.Remote(
            command_executor=self.executor_url,
            desired_capabilities={}
        )
        driver.session_id = self.session_id

        # Replace the patched function with original function
        WebDriver.execute = original_execute
        return driver

    async def screenshot(self, html: str, css: str):
        """ Make Chrome get a website and screenshot it """
        html_website = f"<html><body>" \
                       f'<div id="capture">{html}</div><style>{css}</style>' \
                       "<style>html, body { background: transparent; margin: auto 0; }" \
                       "#capture { display: inline-block; height: auto; width: auto; }" \
                       "</style></body></html>"

        # Fetch HTML/CSS and screenshot it
        driver = self.recycled_driver()
        driver.get(f"data:text/html;charset=utf-8,{urllib.parse.quote(html_website)}")
        element = driver.find_element_by_id("capture")
        location = element.location
        size = element.size
        png = driver.get_screenshot_as_png()

        # Now render screenshot Bytes
        b = BytesIO()
        im = Image.open(BytesIO(png))
        left = location["x"]
        top = location["y"]
        right = location["x"] + size["width"]
        bottom = location["y"] + size["height"]
        im = im.crop((left, top, right, bottom))
        im.save(b, "PNG")
        b.seek(0)
        return b
