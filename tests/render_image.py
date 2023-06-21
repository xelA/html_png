import requests
import time

html = """
<div class="container">
    <h1>Hello, world 2</h1>
</div>
"""

css = """
.container {
    align-items: center;
    background-color: red;
    display: flex;
    justify-content: center;
    padding: .5em 1em;
}

h1 {
    font-size: 3em;
    font-family: Arial;
    color: #fff;
    margin: 0;
}
"""

start_time = time.time()

r = requests.post(
    "http://127.0.0.1:8575", json={
        "html": html.replace("\n", ""),
        "css": css.replace("\n", "")
    }
)

print(f"Rendered in {time.time() - start_time} seconds")

# Save the HTML and CSS to disk
with open("./render_image_output.png", "wb") as f:
    f.write(r.content)

print(f"Saved to ./render_image_output.png in {time.time() - start_time} seconds")
