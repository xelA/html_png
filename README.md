# html_png
An API that renders HTML/CSS content to PNG using Chromium

# Disclaimer
I am **not** responsible if you happen to make your own instance of this API, have it public and get your IP leaked because someone really wanted to put a nice, little `<img>` which tracks your IP or any other methods.

Heavily recommend to only run this on **localhost** where your services and scripts are the only authorized users/programs to take advantage of the rendering API.

# Requirements
- Python 3.7 or above
- Chrome

# Usage
POST Request: `http://localhost:PORT`<br>
JSON args:
  - html (Required: The HTML that API should render)
  - css (Optional: The CSS that API should render)

# LICENSE
Please provide credits if you're going to take usage of this :)
