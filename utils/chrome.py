import asyncio
import urllib
import re
import htmlmin

from bs4 import BeautifulSoup
from bs4.element import Comment
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.remote.webdriver import WebDriver


class Chrome:
    def __init__(self, chromedriver: str = "", proxy: str = None, headless: bool = True, timeout: int = 5):
        self.chromedriver = chromedriver
        self.timeout = timeout

        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")

        for g in ["--log-level=3", "--window-size=1500x1500"]:
            options.add_argument(g)

        if proxy and isinstance(proxy, str):
            options.add_argument(f"--proxy-server={proxy}")

        self.driver = webdriver.Chrome(
            executable_path=self.chromedriver, options=options
        )

        self.driver.set_page_load_timeout(self.timeout)

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

    def sanitize(self, untrusted_html: str):
        """ Check HTML for bad attempts """
        tag_whitelist = [
            "a", "abbr", "address", "b", "code",
            "cite", "pre", "em", "i", "ins", "kbd",
            "q", "samp", "small", "strike", "strong",
            "sub", "var", "p", "span", "div", "h1", "br",
            "h2", "h3", "h4", "h5", "h6", "pre", "img", "style",
            "table", "tbody", "thead", "th", "tr", "td", "link"
        ]

        tag_blacklist = ["script", "iframe"]

        attributes_with_urls = ["href", "src"]
        safe_attributes = ["alt", "title", "id", "class", "name", "style"]

        attr_whitelist = {
            "a": ["href", "title"],
            "img": ["src", "alt", "width", "height", "title"],
            "link": ["rel", "href"],
        }

        soup = BeautifulSoup(untrusted_html, features="html.parser")
        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        for tag in soup.findAll():
            tag_name = tag.name.lower()
            if tag_name in tag_blacklist:
                tag.extract()
            elif tag_name not in tag_whitelist:
                tag.hidden = True
            else:
                for attr, value in list(tag.attrs.items()):
                    if attr.lower() in safe_attributes:
                        continue  # This one is 100% safe

                    if tag_name in attr_whitelist and attr.lower() in attr_whitelist[tag_name]:
                        if attr.lower() in attributes_with_urls:
                            if not re.match(r"(https?|ftp)://", value.lower()):
                                del tag.attrs[attr]
                    elif attr == "rel" and value == "stylesheet":
                        continue
                    else:
                        del tag.attrs[attr]

        return htmlmin.minify(
            str(soup),
            remove_empty_space=True,
            remove_comments=True
        )

    async def screenshot(self, driver):
        """ Screenshot from driver """
        image = driver.get_screenshot_as_png()
        return image

    async def render(self, html: str, css: str):
        """ Make Chrome get a website and screenshot it """
        # Check for bad arguments
        html = self.sanitize(html)

        # Create a sanitized HTML string
        html_website = f"<html><body>" \
                       f'<div id="capture">{html or "placeholder"}</div><style>{css or ""}</style>' \
                       "<style>html, body { margin: auto 0; }" \
                       "#capture { display: inline-block; height: auto; width: auto; }" \
                       "</style></body></html>"

        # Fetch HTML/CSS and screenshot it
        driver = self.recycled_driver()

        try:
            driver.get(f"data:text/html;charset=utf-8,{urllib.parse.quote(html_website)}")
        except exceptions.TimeoutException:
            return await self.render("<h1>Timeout</h1><p>Took too long to fetch content...", None)

        element = driver.find_element_by_id("capture")
        location = element.location
        size = element.size

        async def create_png():
            image_output = asyncio.ensure_future(self.screenshot(driver))
            await image_output
            return image_output.result()

        try:
            png = await asyncio.wait_for(create_png(), timeout=self.timeout)
        except asyncio.TimeoutError:
            return await self.render("<h1>Timeout</h1><p>Took too long to render...", None)

        # Now render screenshot Bytes
        try:
            b = BytesIO()
            im = Image.open(BytesIO(png))
            left = location["x"]
            top = location["y"]
            right = location["x"] + size["width"]
            bottom = location["y"] + size["height"]
            im = im.crop((left, top, right, bottom))
        except Image.DecompressionBombError:
            return await self.render("<h1>Detected decompression bomb DOS attack, stopping...</h1>", None)
        except Image.DecompressionBombWarning:
            return await self.render("<h1>Possible decompression bomb DOS attack, stopping...</h1>", None)

        try:
            im.save(b, "PNG")
        except SystemError:
            return await self.render("<h1>placeholder...</h1>", None)

        b.seek(0)
        return b
