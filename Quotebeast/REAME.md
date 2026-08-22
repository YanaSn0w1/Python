### [Quote_Beast.py](https://github.com/YanaSn0w1/Python/blob/main/Quotebeast/Quote_beast.py "Quote_Beast.py") 

## A command-line tool that generates short, punchy one-liners.

## Use with mouse hotkeys [Quote_beast.ahk](https://github.com/YanaSn0w1/AutoHotkey#quote_beastahk-%EF%B8%8F "Quote_beast.ahk") Or works in powershell.

# How It Works

1. Reads the clipboard and sanitizes it into a clean context string.
2. Builds a lean system + user prompt based on the selected mode.
3. Calls Groq and Gemini API (primary: `gemini-3.5-flash-lite`, fallback: `qwen/qwen3.6-27b`).
4. Validates the response — rejects anything too long, banned words, duplicates, or AI tells.
5. Retries up to 12 times with increasing temperature if the output is rejected.
6. Copies the final result to clipboard and saves it to history.
7. Uses 2 of each key, 4 total, changes every time and uses Groq 2 times Gemini 1 time to avoid rate limit with free tier.

---

## Requirements

- Python 3.8+
- `In powershell install requests` library
```
pip install requests
```
- A Groq API key set as a Windows environment variable: `GROQ_API_KEY`

---

## Setup

1. Set API keys in powershell (run as admin).
 ```ps1
   $env:GEMINI_API_KEY = "Your_API_Key_Here"
   $env:GEMINI_API_KEY_2 = "Your_API_Key_Here"
   $env:GROQ_API_KEY = "Your_API_Key_Here"
   $env:GROQ_API_KEY_2 = "Your_API_Key_Here"
   [Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "Your_API_Key_Here", "User")
   [Environment]::SetEnvironmentVariable("GEMINI_API_KEY_2", "Your_API_Key_Here", "User")
   [Environment]::SetEnvironmentVariable("GROQ_API_KEY", "Your_API_Key_Here", "User")
   [Environment]::SetEnvironmentVariable("GROQ_API_KEY_2", "Your_API_Key_Here", "User")
   ```

2. Place `quote_beast.py` in the same folder as `quote_beast.ahk` then run `quote_beast.ahk` as administrator.

## Powershell usage examples
```
python quote_beast.py [options]
```
```bash
python quote_beast.py -m hot -n 5
```
```bash
python quote_beast.py -m hot --infinite
```

### Options

| Flag | Description |
|------|-------------|
| `-m`, `--mode` | `hot`, `boost`, `flirt`, or `stoic`. Defaults to last used mode. |
| `-n`, `--number` | Generate multiple lines (skips clipboard context after the first). |
| `--short` | Short mode — output under ~10 words. |
| `--blind` | Ignore clipboard content, generate without context. |

---

## Modes

| Mode | Style |
|------|-------|
| `hot` | Bold hot takes that contradict popular opinion. Blunt and punchy. |
| `boost` | Grounded, practical motivation. No fluff or clichés. |
| `flirt` | Matches the energy of whatever was copied — hype, warm, or witty. |
| `stoic` | Calm, detached one-liners in the style of a stoic philosopher. |

---

## Clipboard Context

If you copy text (via the AHK hotkey) within 10 seconds before triggering generation, the script uses that text as context for the output. It sanitizes the clipboard content — stripping @mentions, URLs, and Twitter shorthand (GM, GN, etc.) — before sending it to the model.

Greeting shorthands are detected and handled:

| Shorthand | Expands to |
|-----------|------------|
| GM | Good Morning |
| GA | Good Afternoon |
| GE | Good Evening |
| GN | Good Night |

---

## Files

| File | Purpose |
|------|---------|
| `last_mode.txt` | Persists the last used mode across runs. |
| `last_ai_quotes.txt` | Stores the last 10 generated lines to avoid repetition. |
| `debug_api.txt` | Logs every API attempt and rejection reason. |
| `debug_last_run.txt` | Logs the mode, context, and clipboard from the most recent run. |

---

## License
MIT
