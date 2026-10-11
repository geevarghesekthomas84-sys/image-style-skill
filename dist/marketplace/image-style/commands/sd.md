---
description: "Format output for Stable Diffusion / SDXL"
argument-hint: "<what to draw> [more /modifiers]"
---
Use the image-style skill. Subject and any extra /modifiers: $ARGUMENTS

Apply this modifier: target model Stable Diffusion / SDXL. Comma-separated keywords. Output two lines: `Prompt:` and `Negative prompt:` (always include "lowres, blurry, bad anatomy, watermark" plus any /no-commands). Output `Size: WxH` from the pixel column. May weight key terms like `(golden hour:1.2)`.

Then follow the image-style skill: expand any other /tokens in the arguments, merge, resolve
conflicts, and generate the image (or output the final prompt if no image tool is available).
