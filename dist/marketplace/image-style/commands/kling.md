---
description: "Format output for Kling AI"
argument-hint: "<what to draw> [more /modifiers]"
---
Use the image-style skill. Subject and any extra /modifiers: $ARGUMENTS

Apply this modifier: target model Kling AI. Descriptive natural English in this order: subject, environment, camera, lighting, style (under 2500 chars). Print a separate `Negative prompt:` line for Kling's negative field. Print `Aspect ratio:` (16:9, 9:16 or 1:1 only; map others to the nearest). For video requests also add one line of motion and camera movement.

Then follow the image-style skill: expand any other /tokens in the arguments, merge, resolve
conflicts, and generate the image (or output the final prompt if no image tool is available).
