

[Quote_Beast.py](https://github.com/YanaSn0w1/Python/blob/main/Quotebeast/Quote_beast.py "Quote_Beast.py") 

[PayPal-Donate](https://www.paypal.com/donate/?hosted_button_id=9LWWH273HEVC4 "Donate to YanaHeat") 

### Generates short, punchy one-liners. Use with [Quote_beast.ahk](https://github.com/YanaSn0w1/AutoHotkey#quote_beastahk-%EF%B8%8F "Quote_beast.ahk") or powershell.

---

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
- 4 API key set as Windows environment variable.

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

---

# Powershell usage examples
```
python quote_beast.py [options]
```
```bash
python quote_beast.py -m hot -n 5
```
```bash
python quote_beast.py -m hot --infinite
```

---

# Options

| Flag | Description |
|------|-------------|
| `-m`, `--mode` | `hot`, `boost`, `flirt`, or `stoic`. Defaults to last used mode. |
| `-n`, `--number` | Generate multiple lines (skips clipboard context after the first). |
| `--short` | Short mode — output under ~10 words. |
| `--blind` | Ignore clipboard content, generate without context. |

---

# Modes

| Mode | Style |
|------|-------|
| `hot` | Bold hot takes that contradict popular opinion. Blunt and punchy. |
| `boost` | Grounded, practical motivation. No fluff or clichés. |
| `flirt` | Matches the energy of whatever was copied — hype, warm, or witty. |
| `stoic` | Calm, detached one-liners in the style of a stoic philosopher. |
| `debug_last_run.txt` | Logs the mode, context, and clipboard from the most recent run. |

---

# License
MIT
