# image-style

Slash commands for AI image generation. Write a request, add commands, get one finished prompt.

```
a lone lighthouse /storm /dramaticlighting /85mm /8k /16:9 /9:16 /clean /mj
```

Plain English works too:

```
Create me a cinematic album double exposure and Size 16:9 ratio frame both 9:16
```

That gives one prompt per ratio, in the format of the tool you pick.

## What is in it

| Group | Count | Examples |
|---|---|---|
| Style commands | 288 | `/cinematic` `/goldenhour` `/droneview` `/chiaroscuro` `/oilpainting` |
| Camera and lens | 13 | `/85mm` `/f1.4` `/tiltshift` `/macrolens` |
| Video motion | 10 | `/dolly` `/orbit` `/handheld` `/slowmotion` |
| Subject controls | 29 | `/age30s` `/smile` `/walking` `/suit` `/longhair` |
| Reference commands | 6 | `/sameface` `/samestyle` `/samepose` |
| Aspect ratios | 10 | `/16:9` `/9:16` `/square` `/4:5` (also `/16x9`) |
| Avoid-lists | 8 | `/clean` `/nodeform` `/nopeople` `/notext` |
| Presets | 12 | `/productshot` `/linkedinheadshot` `/moviepost` `/youtubethumb` |
| Target models | 8 | `/mj` `/sd` `/flux` `/dalle` `/gemini` `/flow` `/kling` `/generic` |

Rules the skill applies:

- Subject first, then angle, camera, light, style, quality last.
- At most 8 style modifiers (reference commands do not count). Extras are dropped, quality first.
- One winner per slot: resolution, realism, focal length, aperture, age, expression, pose. The last one given wins.
- Several ratios in one request produce one prompt per ratio.
- Unknown `/words` are kept as plain text and reported.

## Install

Everything is pre-built in `dist/`.

### Claude Code: plugin

```bash
claude plugin marketplace add ./dist/marketplace
claude plugin install image-style@image-style-market
```

Plugin commands are namespaced: `/image-style:goldenhour a quiet harbor`.
The skill also reads bare tokens in normal messages.

### Claude Code: standalone skill

Copy `dist/image-style/` to `~/.claude/skills/image-style/`.

### Claude.ai

Settings, Capabilities, Skills, Upload skill: `dist/platforms/claude-ai/image-style.zip`.
Claude.ai has no image generator, so it returns the final prompt.

### ChatGPT

Create a Custom GPT. Paste `dist/platforms/chatgpt/instructions.txt` into Instructions, upload
`image-style-knowledge.md` under Knowledge, enable Image Generation.
Without GPT access, paste `custom-instructions-short.txt` into Custom instructions.

### Gemini

Create a Gem. Paste `dist/platforms/gemini/instructions.txt` into Instructions and add
`image-style-knowledge.md` under Knowledge.

### Google Flow, Kling, anything else

These have no skill or plugin system. Open `dist/platforms/flow-kling-anywhere/expander.html`
in a browser (works offline). Type a request, pick the target, copy the result.
It has a command browser, a "what each command added" panel, and one-click copy-and-open buttons.
The Generate image button uses a free third-party service and is often rate-limited.

## Edit and rebuild

Data lives in `src/`:

| File | Format |
|---|---|
| `modifiers.txt` | `name\|category\|phrase` |
| `aspect.txt` | `name\|ratio\|pixels\|note` (note may list `aliases: ...`) |
| `negatives.txt` | `name\|terms to avoid` |
| `models.txt` | `name\|label\|formatting rules` |
| `presets.txt` | `name\|label\|tokens\|default ratio` |

```bash
python build.py   # regenerates dist/
python test.py    # checks names, presets, outputs, page script
```

Names are lowercase `a-z`, `0-9` and `.` only, and must be unique across all files.
Bump `VERSION` in `build.py` after changes so Claude Code sees the plugin update.

## Notes

- Model-specific formats (Midjourney flags, Flux sentences, Kling negative field) follow general
  knowledge of those tools and are not benchmarked. Please report outputs that look wrong.
- No commands name living artists or studios. `test.py` enforces a small blocklist.
- Reference commands need an image you own or have permission to use.

## License

MIT
