### [Quote_Beast.py](https://github.com/YanaSn0w1/Python/blob/main/Quotebeast/Quote_beast.py "Quote_Beast.py") 

A command-line tool that generates short, punchy one-liners using the Groq API (Llama 3.3 70B).

Designed to be triggered with mouse hotkeys [Quote_beast.ahk](https://github.com/YanaSn0w1/AutoHotkey#quote_beastahk-%EF%B8%8F "Quote_beast.ahk") 

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

1. Set your Groq API key in powershell permanently.
 ```ps1
   $env:GROQ_API_KEY = "Your_API_Key_Here"
   [Environment]::SetEnvironmentVariable("GROQ_API_KEY", "Your_API_Key_Here", "User")
   ```
2. Optional - Permanently set in Windows. 
- Search for “Edit the system environment variables”  
- Click Environment Variables button  
Under User variables (or System variables if you want it for all users), click New…  
Variable name: GROQ_API_KEY  
Variable value: paste your real Groq key  
Click OK on everything
After doing either of the above, restart PowerShell (or log out/in).
3. Optional - You can see your key with:
```ps1
$env:GROQ_API_KEY
```
4. Optional - Check if Groq models are online
```ps1
$headers = @{ "Authorization" = "Bearer $env:GROQ_API_KEY" }

Invoke-RestMethod -Uri "https://api.groq.com/openai/v1/models" `
                  -Headers $headers `
                  -Method Get | 
    Select-Object -ExpandProperty data | 
    Select-Object id, created, owned_by | 
    Format-Table -AutoSize
```
5. Place `quote_beast.py` in the same folder as `quote_beast.ahk` and run as administrator.

---

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

## How It Works

1. Reads the clipboard and sanitizes it into a clean context string.
2. Builds a lean system + user prompt based on the selected mode.
3. Calls the Groq API (primary: `llama-3.3-70b-versatile`, fallback: `llama-3.1-8b-instant`).
4. Validates the response — rejects anything too long, banned words, duplicates, or AI tells.
5. Retries up to 12 times with increasing temperature if the output is rejected.
6. Copies the final result to clipboard and saves it to history.

## License
MIT
