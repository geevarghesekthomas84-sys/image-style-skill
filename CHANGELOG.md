# Changelog

## 1.3.0
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
