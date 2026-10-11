---
description: "Format output for Google Flow (Veo / Imagen)"
argument-hint: "<what to draw> [more /modifiers]"
---
Use the image-style skill. Subject and any extra /modifiers: $ARGUMENTS

Apply this modifier: target model Google Flow (Veo / Imagen). Natural English: subject, setting, camera/angle, lighting, style as one flowing paragraph. Aspect is chosen in Flow settings (video: 16:9 or 9:16 only), so print `Set aspect ratio to X` as a separate line. Negatives become positive phrasing, or go in Flow's negative field if shown.

Then follow the image-style skill: expand any other /tokens in the arguments, merge, resolve
conflicts, and generate the image (or output the final prompt if no image tool is available).
