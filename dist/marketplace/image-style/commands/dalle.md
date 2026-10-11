---
description: "Format output for DALL-E / ChatGPT images"
argument-hint: "<what to draw> [more /modifiers]"
---
Use the image-style skill. Subject and any extra /modifiers: $ARGUMENTS

Apply this modifier: target model DALL-E / ChatGPT images. One or two natural English sentences. No flags. Negatives become positive phrasing ("no text" -> "with no text or lettering"). Aspect: nearest of 1024x1024, 1792x1024 (wide), 1024x1792 (tall).

Then follow the image-style skill: expand any other /tokens in the arguments, merge, resolve
conflicts, and generate the image (or output the final prompt if no image tool is available).
