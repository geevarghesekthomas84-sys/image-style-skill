---
description: "Format output for Midjourney"
argument-hint: "<what to draw> [more /modifiers]"
---
Use the image-style skill. Subject and any extra /modifiers: $ARGUMENTS

Apply this modifier: target model Midjourney. Comma-separated phrases. Append `--ar W:H` for aspect, `--no a, b, c` for negatives, and `--style raw` when /rawphoto, /photorealistic or /ultrarealistic is used. No pixel sizes.

Then follow the image-style skill: expand any other /tokens in the arguments, merge, resolve
conflicts, and generate the image (or output the final prompt if no image tool is available).
