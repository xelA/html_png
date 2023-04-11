import json
import asyncio
import logging
import time
import random

from quart import Quart, request, send_file, abort
from utils.chrome import Chrome


app = Quart(__name__)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

with open("./config.json", "r", encoding="utf8") as f:
    config = json.load(f)

chrome = Chrome(
    chromedriver=config.get("chromedriver_path", ""),
    proxy=random.choice(config["proxies"]) if config.get("proxies", None) else None,
    headless=config.get("chrome_headless", True),
    timeout=config.get("chrome_timeout", 5),
    window_size=config.get("chrome_window_size", [1920, 1080])
)


def debug_print(message: str):
    if config.get("debug", False):
        print(message)


@app.route("/", methods=["GET"])
async def index():
    return {"hello": "world"}


@app.route("/", methods=["POST"])
async def html_engine():
    print(1)
    data = await request.json
    print(2)
    html = data.get("html", None)
    css = data.get("css", None)
    print(3)
    if not html:
        abort(400, "No HTML provided")
    print(4)
    before_ping = time.monotonic()
    image_output = asyncio.ensure_future(
        chrome.render(html, css), loop=loop
    )
    print(5)
    await image_output
    print(6)
    after_ping = int((time.monotonic() - before_ping) * 1000)
    debug_print(f"Took {after_ping}ms to produce the image")
    print(7)
    return await send_file(
        image_output.result(),
        mimetype="image/png",
        attachment_filename="htmlcss.png"
    )

app.run(
    port=config.get("port", 8080),
    debug=config.get("debug", False),
    loop=loop
)
