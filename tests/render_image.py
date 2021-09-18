import requests

html = """
<div class="container">
    <h1>Hello, world</h1>
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

r = requests.post(
    "http://localhost:8080", json={
        "html": html.replace("\n", ""),
        "css": css.replace("\n", "")
    }
)

# Save the HTML and CSS to disk
with open("./render_image_output.png", "wb") as f:
    f.write(r.content)
