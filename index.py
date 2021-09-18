import json
import asyncio
import logging
import time
import random

from quart import Quart, request, send_file, abort
from utils.chrome import Chrome


app = Quart(__name__)
loop = asyncio.get_event_loop()
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

with open("./config.json", "r", encoding="utf8") as f:
    config = json.load(f)

chrome = Chrome(
    chromedriver=config["chromedriver_path"],
    proxy=random.choice(config["proxies"]) if config["proxies"] else None
)


def debug_print(message: str):
    if config["debug"]:
        print(message)


@app.route("/", methods=["GET"])
async def index():
    return {"hello": "world"}


@app.route("/", methods=["POST"])
async def html_engine():
    data = await request.json

    html = data.get("html", None)
    css = data.get("css", None)

    if not html:
        abort(400, "No HTML provided")

    before_ping = time.monotonic()
    image_output = asyncio.ensure_future(
        chrome.screenshot(html, css), loop=loop
    )

    try:
        await image_output
    except SystemError:
        abort(400, "Failed to render image...")

    after_ping = int((time.monotonic() - before_ping) * 1000)
    debug_print(f"Took {after_ping}ms to produce the image")

    return await send_file(
        image_output.result(),
        mimetype="image/png",
        attachment_filename="htmlcss.png"
    )

app.run(
    port=config["port"],
    debug=config["debug"],
    loop=loop
)
