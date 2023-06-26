# html_png
An API that renders HTML/CSS content to PNG using NextJS with reSVG and Satori

# Disclaimer
I am **not** responsible if you happen to make your own instance of this API, have it public and get your IP leaked because someone really wanted to put a nice, little `<img>` which tracks your IP or any other methods.

Heavily recommend to only run this on **localhost/127.0.0.1** where your services and scripts are the only authorized users/programs to take advantage of the rendering API.

# Requirements
- NodeJS v20 or higher

# Usage
```http
POST /api
Content-Type: text/plain
data='HTML content inside here'
```

# LICENSE
Please provide credits if you're going to take usage of this :)
