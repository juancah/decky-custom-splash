import { readFileSync } from 'fs'
import deckyPlugin from '@decky/rollup'
import path from "path";

export default deckyPlugin({
  output: {
    dir: path.resolve(
      process.cwd(),
      "releases/SDH-CustomSplash/dist"
    ),
    assetFileNames: '[name]-[hash][extname]'
  }
})
