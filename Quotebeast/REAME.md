# 🔥 AI QUOTE BEAST v9.3

AI Quote Beast is a local Python tool that generates short, punchy one‑liners using your Ollama models. Four modes: **hot**, **boost**, **flirt**, **stoic** — each with strict tone rules and unified cyan output.

## Features
- Four distinct modes with handcrafted prompts  
- One‑sentence output, max 20 words  
- Rolling history to avoid repetition  
- Infinite mode with Enter/X control  
- Customizable Ollama model  
- Fallback lines if generation fails  

## Requirements
- Python 3.8+  
- Ollama running locally  
- `pip install requests`

## Usage
```bash
python quote_beast.py -m hot
python quote_beast.py -m boost
python quote_beast.py -m flirt
python quote_beast.py -m stoic
```

## Additional flags
```bash
python quote_beast.py -n 5
python quote_beast.py --infinite
python quote_beast.py --model llama3.1:8b
```

## Full command example
```bash
python quote_beast.py -m hot -n 5
python quote_beast.py -m hot --infinite --model llama3.1:8b
```

## History
Stores last 20 lines in `hot_takes_history.json` to keep outputs fresh.

## Example Output
```
🔥 HOT #4821 🔥
Most people chase success but run from the work that creates it.
```

## License
MIT
