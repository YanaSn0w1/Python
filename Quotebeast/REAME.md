# 🔥 AI QUOTE BEAST v9.8

AI Quote Beast is a local Python tool that generates short, punchy one‑liners using your Ollama models. Four modes: **hot**, **boost**, **flirt**, **stoic** — each with strict tone rules and unified.

## Features
- Four distinct modes with handcrafted prompts  
- One‑sentence output, max 20 words  
- Rolling history to avoid repetition  
- Infinite mode with Enter/X control  
- Customizable Ollama model  
- Fallback lines if generation fails
- Saves each quote to clipboard
- Saves last 100 to quote_beast_history.json in the user folder

## Requirements
- Python 3.8+  
- Ollama running locally  
- `pip install requests`

## Usage
# Start ollama in powershell
```bash
ollama serve
```
# Open new tab in powershell then use the commands
```bash
python quote_beast.py -m hot
python quote_beast.py -m boost
python quote_beast.py -m flirt
python quote_beast.py -m stoic
```

## Additional flags
```bash
-n 5
```
```bash
--infinite
```
```bash
--model llama3.1:8b
```

## Full command examples
```bash
python quote_beast.py -m hot -n 5
```
```bash
python quote_beast.py -m hot --infinite
```
```bash
python quote_beast.py -m hot --infinite --model llama3.1:8b
```

## Example Output
```
🔥 HOT #4821 🔥
Most people chase success but run from the work that creates it.
```

## License
MIT
