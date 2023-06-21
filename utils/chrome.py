import asyncio
import urllib
import re
import json
import htmlmin
import os

from bs4 import BeautifulSoup
from bs4.element import Comment
from PIL import Image
from io import BytesIO
from utils import svg_elements
from selenium import webdriver
from selenium.common import exceptions


class Chrome:
    def __init__(
        self,
        chromedriver: str = "",
        proxy: str = None,
        headless: bool = True,
        timeout: int = 5,
        window_size: list = [1920, 1080]
    ):
        self.chromedriver = chromedriver
        self.timeout = timeout

        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument("--headless")

        if not isinstance(window_size, list):
            raise TypeError("window_size must be a list")
        x_size, y_size = window_size

        for g in ["--log-level=3", f"--window-size={x_size}x{y_size}"]:
            self.options.add_argument(g)

        if proxy and isinstance(proxy, str):
            self.options.add_argument(f"--proxy-server={proxy}")

        self.driver = webdriver.Chrome(
            executable_path=self.chromedriver, options=self.options
        )

        self.driver.set_page_load_timeout(self.timeout)

        # This will make the default #FFFFFF background transparent with screenshots
        self.send(
            self.driver, "Emulation.setDefaultBackgroundColorOverride",
            {"color": {"r": 0, "g": 0, "b": 0, "a": 0}}
        )

        self.session_id = self.driver.session_id
        self.executor_url = self.driver.command_executor._url

    def sanitize(self, untrusted_html: str) -> str:
        """ Check HTML for bad attempts """
        tag_whitelist = [
            "a", "abbr", "address", "b", "code",
            "cite", "em", "i", "ins", "kbd",
            "q", "samp", "small", "strike", "strong",
            "sub", "var", "p", "span", "div", "h1", "br",
            "h2", "h3", "h4", "h5", "h6", "pre", "img", "style",
            "table", "tbody", "thead", "th", "tr", "td", "footer",
            "section", "main", "svg", "path", "g", "foreignObject",
            "rect", "ul", "ol", "li"
        ]

        tag_blacklist = ["script", "iframe"]

        attributes_with_urls = ["href", "src"]
        safe_attributes = ["alt", "title", "id", "class", "name", "style", "viewBox", "fill"]

        attr_whitelist = {
            "a": ["href", "title"],
            "img": ["src", "alt", "width", "height", "title"]
        }

        soup = BeautifulSoup(untrusted_html, features="html.parser")
        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        for tag in soup.findAll():
            tag_name = tag.name.lower()
            if tag_name in tag_blacklist:
                tag.extract()
            elif tag_name not in tag_whitelist and tag_name not in svg_elements.elements:
                tag.hidden = True
            else:
                for attr, value in list(tag.attrs.items()):
                    if attr.lower() in safe_attributes:
                        continue  # This one is 100% safe

                    if tag_name in svg_elements.elements:
                        if attr.lower() not in svg_elements.attributes:
                            del tag.attrs[attr]
                    elif tag_name in attr_whitelist and attr.lower() in attr_whitelist[tag_name]:
                        if attr.lower() in attributes_with_urls:
                            if not re.match(r"(https?|ftp)://", value.lower()):
                                del tag.attrs[attr]
                    else:
                        del tag.attrs[attr]

        if os.name == "nt":
            return str(soup)
        else:
            return htmlmin.minify(
                str(soup),
                remove_empty_space=True,
                remove_comments=True
            )

    async def screenshot(self, driver: webdriver.Chrome) -> bytes:
        """ Screenshot from driver """
        image = driver.get_screenshot_as_png()
        return image

    def send(self, driver, cmd, params={}) -> dict:
        resource = f"/session/{driver.session_id}/chromium/send_command_and_get_result"
        url = driver.command_executor._url + resource
        body = json.dumps({"cmd": cmd, "params": params})
        response = driver.command_executor._request("POST", url, body)
        if response.get("status", None):
            raise Exception(response.get("value"))
        return response.get("value")

    async def kill(self):
        self.driver.quit()

    async def render(self, html: str, css: str) -> bytes:
        """ Make Chrome get a website and screenshot it """
        # Check for bad arguments
        html = self.sanitize(html)

        # Create a sanitized HTML string
        html_website = (
            f"<html><body>"
            f'<div id="capture">{html or "placeholder"}</div><style>{css or ""}</style>'
            "<style>html, body { margin: auto 0; overflow: hidden; }"
            "#capture { display: inline-block; height: auto; width: auto; position: relative; overflow: hidden; }"
            "</style></body></html>"
        )

        # Fetch HTML/CSS and screenshot it
        driver = self.driver

        try:
            driver.get(f"data:text/html;charset=utf-8,{urllib.parse.quote(html_website)}")
        except exceptions.TimeoutException:
            return await self.render("<h1>Timeout</h1><p>Took too long to fetch content...", None)

        element = driver.find_element("id", "capture")
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
