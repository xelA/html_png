import satori from "satori"
import fs from "fs/promises"
import config from "../../config.json"

import { renderAsync } from "@resvg/resvg-js"
import { html } from "satori-html"

const cache_fonts = []

async function load_fonts() {
  if (cache_fonts.length) return cache_fonts

  const files = await fs.readdir("./fonts")
  const sortedFiles = files.sort((a, b) => {
    if (a === config.default_font) return -1
    if (b === config.default_font) return 1
    return a.localeCompare(b)
  })

  for (const filename of sortedFiles) {
    if (!filename.endsWith(".ttf")) continue
    cache_fonts.push({
      data: await fs.readFile(`./fonts/${filename}`),
      name: filename.replace(/\.ttf$/, ""),
      style: "normal",
      weight: 400
    })
  }

  return cache_fonts
}

export default async function handler(req, res) {
  const errors = []
  let svg, png_buffer

  if (req.method !== "POST")
    errors.push("Method must be POST")
  if (req.headers["content-type"] !== "text/plain")
    errors.push("Content-Type must be text/plain")

  if (config.token) {
    if (!req.headers.authorization)
      errors.push("Missing authorization header")
    else if (req.headers.authorization !== config.token)
      errors.push("Invalid authorization header")
  }

  if (errors.length) {
    res.status(400).json({ error: errors })
    return
  }

  let rawhtml = typeof req.body === "string" ? req.body : null
  if (!rawhtml) rawhtml = "Missing body"

  try {
    const markup = html(rawhtml)

    svg = await satori(markup, {
      width: req.headers["x-width"] || undefined,
      height: req.headers["x-height"] || undefined,
      fonts: await load_fonts(),
    })

    const opts = {
      background: "rgba(0, 0, 0, 0)",
      font: { loadSystemFonts: false },
      logLevel: "off",
    }

    const png_data = await renderAsync(svg, opts)
    png_buffer = png_data.asPng()

  } catch (e) {
    // console.error(e)
    res.status(500).json({ error: e.message })
    return
  }

  res.setHeader("Content-Type", "image/png")
  res.status(200).end(png_buffer)
}
