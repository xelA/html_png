const client = require('next/dist/cli/next-start')
const config = require("../config.json")

client.nextStart([
  "-p", config.port || "3000",
  "-H", config.host || "localhost",
])
