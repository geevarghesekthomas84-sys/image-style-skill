# Changelog

## 1.10.6
- ComfyUI: new example workflow `image-style-qwen-image-edit.json` (Qwen Image 2.1 instruction edit with the Image Style prompt node feeding the edit instruction). Built from ComfyUI's own Qwen Image 2.1 edit template; the template's prompt-enhancer loader pointed at a model file most people do not have, so it now points at an installed file and the enhancer stays off. Loads with no missing nodes and every list value checked against the installed files; the model itself was not run (no GPU in my test setup).

## 1.10.5
- ComfyUI image-to-image workflow: the picture is now scaled to the width and height the Image Style node gives, so `/16:9` and other ratio commands change the output shape (before, the output always kept the uploaded picture's shape and a ratio command did nothing). Added a how-to note in the workflow: describe what is in the picture in the request, because a request like `/14mm /16:9` alone has no subject. Checked in ComfyUI 0.39.0: `/16:9` gave 1344x768 from the node and the scaled picture; the model itself was not run.

## 1.10.4
- ComfyUI: new example workflow `image-style-z-image-turbo-img2img.json`: upload a picture, write the change with /commands, and Z-Image-Turbo redraws it (Load Image, Scale to 1 megapixel, VAE Encode into the KSampler at denoise 0.6). Loads with no missing nodes; the upload and scale steps were run in ComfyUI 0.39.0; the model itself was not run (no GPU).

## 1.10.3
- ComfyUI Upload & Convert: new **Download last result** button on the node. After a run it saves the produced file(s) (SVG, PNG, ...) through the browser, so you don't have to dig in the `output` folder. Checked in the ComfyUI front end: run, press the button, the SVG downloaded (10 KB, valid `<svg>`). Pressing it before a run shows a short hint.

## 1.10.2
- ComfyUI Upload & Convert: no more empty "(none)" picker that showed "Image failed to load". A small sample picture (`image-style-sample.png`) is copied into ComfyUI's `input` folder and selected by default, so pressing Run works at once; "choose file to upload" uses your own picture, and a connected `images` input still wins. Run through the ComfyUI front end: sample picture to SVG saved with previews. Example workflows updated.

## 1.10.1
- ComfyUI: two more example workflows. `image-style-upload-to-svg.json` (upload a picture, save it as SVG, preview the path) ran end to end in ComfyUI 0.39.0. `image-style-z-image-turbo-svg.json` is the Z-Image-Turbo workflow plus a step that also saves every picture as SVG; it loads with no missing nodes but the model was not run on a GPU.

## 1.10.0
- ComfyUI: new node **Image Style Upload & Convert**. Upload an image (or connect one) and save it as PNG, JPG, WebP, BMP, TIFF, GIF, SVG (traced to flat-colour vector paths) or SVG (picture embedded). The tracer is plain NumPy and Pillow, with no extra installs. Photos come out posterised; best for logos, icons and flat art. Run end to end in ComfyUI 0.39.0; 28 unit tests.

## 1.9.0
- Fix: lens and camera phrases no longer name equipment. `/200mm` used to say "200mm telephoto lens", and some models then drew a lens or camera (even with "300 mm" written on it) into the picture. 19 phrases now describe the look instead, for example "200mm look, extreme background compression, isolated subject" and "85mm portrait framing". Affected: the focal lengths (`/14mm` to `/200mm`), `/tiltshift`, `/telephoto`, `/macrolens`, `/wideangle`, `/fisheye`, `/anamorphic`, `/lensflare`, `/topdown`, `/highangle`, `/lowangle`, `/wildlifephotography`, `/disposablecamera`.
- New avoid-list `/nogear` (camera, lens, DSLR, lens markings). 403 commands.
- Tests: the web page and the ComfyUI node were re-checked against each other on 28 requests (0 mismatches).

## 1.8.1
- ComfyUI: example workflow `example_workflows/image-style-z-image-turbo.json` (Z-Image-Turbo with the Image Style node wired in). Loads with no missing nodes; not run end to end on a GPU.

## 1.8.0
- ComfyUI node: browser extension `web/imagestyle.js`. Typing `/` in the request box shows command autocomplete (arrows, Tab or Enter to insert) and a live preview of the positive prompt, negative prompt, size and report. Backed by two small routes (`/imagestyle/commands`, `/imagestyle/expand`) that reuse the node's Python code. Tried with real input in ComfyUI frontend 1.55.14; 20 unit tests.

## 1.7.0
- ComfyUI node pack `comfyui/ComfyUI-ImageStyle`: **Image Style Prompt** (positive, negative, width, height, report) and **Image Style Prompt (all ratios)** (one item per ratio). Python port of the expander, checked against the web page on 28 recorded requests; runs in ComfyUI 0.39.0. Zip in `dist/platforms/comfyui/`.

## 1.6.0
- README: animated typing demo (`docs/demo.svg`, pure SVG + CSS, no scripts; shows the finished frame when the viewer prefers reduced motion).
- Shareable links: `#r=<request>&t=<target>` fills the page in; a **Copy link** button (shown on web addresses only) makes one. The address bar follows what you type. Saved recipes are expanded into plain commands in the link. Link text is only ever placed in the text box as plain text.

## 1.5.2
- The hosted demo page (`docs/`) is a trimmed copy: no localhost helper call, no Copy-and-open buttons, no image generation. The downloadable page keeps all of them. (Chrome flagged the first, fuller hosted version.)

## 1.5.1
- Live demo on GitHub Pages (served from `docs/`): the expander page and cheat sheet.

## 1.5.0
- Couple and wedding commands (16, adults only): `/couple` `/prewedding` `/engagement` `/wedding` `/anniversary` `/romantic` `/holdinghands` `/embrace` `/foreheadtouch` `/walkingtogether` `/dancingcouple` `/laughingtogether` `/backtoback` `/candidcouple` `/silhouettecouple` `/sunsetcouple`.
- Presets `/couplepro` and `/weddingclassic`. 402 commands in total.

## 1.4.1
- Root `.claude-plugin/marketplace.json`: the plugin installs straight from GitHub with `claude plugin marketplace add geevarghesekthomas84-sys/image-style-skill`.

## 1.4.0
- Expander page: save your own recipes (`/mylook`), kept in the browser, with a Mine tab and delete.

## 1.3.0
- `dist/cheatsheet.html`: searchable, printable list of all commands.
- GitHub Actions check runs `build.py` and `test.py` on every push.
- `imagegen.py`: local helper so Generate image can use your own OpenAI or Gemini key (key stays in an environment variable, not the page). Falls back to the free service.

## 1.2.0
- Subject controls: age, expression, pose, gaze, outfit, hair (29).
- Reference commands: `/sameface`, `/samestyle`, `/samepose`, `/samecomposition`, `/samecolors`, `/samelighting`.
- Expander page: "what each command added" panel.
- Reference commands no longer count toward the 8-modifier cap.

## 1.1.0
- Camera and lens commands (13) and video motion commands (10).
- 12 presets.
- Cap of 8 style modifiers and one-winner slots.
- Plain-English requests and multiple ratios (one prompt each).
- Platform packages: Claude.ai zip, ChatGPT, Gemini, offline expander page.
- Models `/flow` and `/kling`.
- `test.py`.

## 1.0.0
- 288 style commands, 10 aspect ratios, 8 avoid-lists, 6 target models.
- Claude skill and plugin.
