# ComfyUI-ImageStyle

Type short `/commands` in a ComfyUI node and get a full positive prompt, a matching negative prompt and an image size.

```
a lone lighthouse on a cliff /storm /dramaticlighting /24mm /16:9 /clean
```

becomes

| Output | Value |
|---|---|
| positive | `a lone lighthouse on a cliff, 24mm wide lens, environmental context with natural perspective, violent storm, dark roiling clouds, lightning, wind, dramatic lighting, strong contrast between light and shadow` |
| negative | `lowres, blurry, bad anatomy, watermark, text, logo, signature, caption, username` |
| width, height | `1344`, `768` |
| report | one line per command used, dropped (conflicts, over the 8-modifier limit) or unknown |

The node only writes text and numbers. It does not load a model or make images itself.

## Install

1. Copy the `ComfyUI-ImageStyle` folder into ComfyUI's `custom_nodes` folder
   (or unzip `ComfyUI-ImageStyle.zip` there). ComfyUI Desktop: `<install folder>/ComfyUI/custom_nodes`.
2. Restart ComfyUI.
3. Right-click the canvas, **Add Node, image-style, Image Style Prompt**.

No extra Python packages are needed.

## The nodes

**Image Style Prompt**: one request, one prompt, one size.

| Input | What it does |
|---|---|
| `request` | Your text with `/commands`, for example `/storm /85mm /9:16 /clean`. |
| `style` | `keywords` (comma-separated, for SD, SDXL, Pony) or `sentences` (plain sentences, for Flux, SD3, Qwen-Image). |
| `default_ratio` | Used only when the request has no ratio. |
| `megapixels` | Scales the size. `1.0` is about 1 MP (SDXL, Flux). Use about `0.25` to `0.5` for SD 1.5. At `1.0` you get the project's table sizes (multiples of 32); other values are scaled to multiples of 64. |
| `ratio_pick` | If the request lists several ratios, which one to use (0 is the first). |
| `extra_negative` | Extra terms appended to the negative prompt. |
| `add_base_negative` | Adds `lowres, blurry, bad anatomy, watermark` (keywords style only). |
| `fold_negatives_into_prompt` | Sentences style only: appends "Clean image without ..." to the prompt, because Flux ignores negatives. |
| `plain_english` | Also recognises style words and ratios written without slashes. Off by default, so your own words are never removed. |

Outputs: `positive`, `negative`, `width`, `height`, `report`.

**Image Style Prompt (all ratios)**: the same, but if you ask for `/16:9 /9:16` it returns one item per ratio, so the nodes after it run once for each.

## Wiring it up

- `positive` and `negative` go into your **CLIP Text Encode** nodes. In newer frontends you can drag the link straight onto the text box; in older ones, right-click the text widget and choose **Convert to input** first.
- `width` and `height` go into **Empty Latent Image**.
- `report` can go to **Preview Any** to see what each command did.

## Commands

402 commands, including styles, camera and lens (`/85mm`, `/f1.4`), subject controls, couple and wedding, avoid-lists (`/clean`, `/nodeform`), aspect ratios (`/16:9`, `/9:16`, `/4:5`) and presets (`/productshot`, `/portraitpro`). The full list is in the [cheat sheet](https://github.com/geevarghesekthomas84-sys/image-style-skill#-cheat-sheet) of the main project. Target-tool commands such as `/mj` or `/kling` are accepted but ignored here, because this node chooses its format with `style`.

## Tested

- Loads and runs in **ComfyUI 0.39.0** (CPU mode): both nodes register, run, and their width and height reach Empty Latent Image and Empty Image (sizes read back as 1344x768, 768x1344, 1024x1024, 896x1120). The all-ratios node ran four times for four ratios. Invalid input is rejected by ComfyUI.
- 16 unit tests, including exact agreement with the project's web page on 28 recorded requests (`python tests/test_core.py`).
- **Not tested:** older ComfyUI versions, other operating systems, and combining it with other custom node packs.

## License

MIT
