---
description: "Format output for Gemini / Imagen"
argument-hint: "<what to draw> [more /modifiers]"
---
Use the image-style skill. Subject and any extra /modifiers: $ARGUMENTS

Apply this modifier: target model Gemini / Imagen. Natural English paragraph. State the aspect ratio in words and pass it as the tool's aspect_ratio parameter if one exists. Negatives become positive phrasing.

Then follow the image-style skill: expand any other /tokens in the arguments, merge, resolve
conflicts, and generate the image (or output the final prompt if no image tool is available).
