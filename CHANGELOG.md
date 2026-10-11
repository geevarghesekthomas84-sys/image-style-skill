# Changelog

## 1.6.0
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
