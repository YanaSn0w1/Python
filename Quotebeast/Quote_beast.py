import random
import argparse
import sys
from datetime import datetime
import requests
import json
import os
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_URL = "http://192.168.1.67:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"

LAST_MODE_FILE = "last_mode.txt"
LAST_AI_QUOTE_FILE = "last_ai_quote.txt"

COLORS = {
    "header": "\033[96m",
    "text":   "\033[97m",
    "reset":  "\033[0m"
}

def get_clipboard():
    try:
        result = subprocess.run(['powershell', '-Command', 'Get-Clipboard'], 
                              capture_output=True, text=True, encoding='utf-8', timeout=2)
        return result.stdout.strip()
    except:
        return ""

def clean_text(text):
    replacements = {'—': '-', '–': '-', '―': '-', '‐': '-', '‑': '-', '‘': "'", '’': "'", '“': '"', '”': '"'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.lstrip(' -–—•*#0123456789').strip()
    return text

def get_last_mode():
    if os.path.exists(LAST_MODE_FILE):
        try:
            with open(LAST_MODE_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            pass
    return "hot"

def save_last_mode(mode):
    try:
        with open(LAST_MODE_FILE, "w", encoding="utf-8") as f:
            f.write(mode)
    except:
        pass

def get_last_ai_quote():
    if os.path.exists(LAST_AI_QUOTE_FILE):
        try:
            with open(LAST_AI_QUOTE_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            pass
    return ""

def save_last_ai_quote(text):
    try:
        with open(LAST_AI_QUOTE_FILE, "w", encoding="utf-8") as f:
            f.write(text)
    except:
        pass

def build_prompt(mode, comment_context=""):
    if comment_context:
        context = f"\n\nPrevious quote (react to it directly): \"{comment_context}\""
    else:
        context = ""

    if mode == "hot":
        prompt = """You are AI Quote Beast — the most savage hot take generator alive.

Write **EXACTLY ONE very short sentence**. Maximum 20 words.

Brutal, sarcastic, irreverent. Casual internet language, swearing allowed.

Rules:
- Boldly contradict a common belief
- Short. Punchy. No fluff.
- Completely new topic every time
- Plain text only. Never use **bold**, *italics*, markdown, asterisks.
- Use ONLY simple hyphen - 
- Never start the sentence with a dash or hyphen. Begin directly with the words."""

    elif mode == "boost":
        prompt = """You are a no-bullshit motivation machine.

Write **EXACTLY ONE very short sentence**. Maximum 20 words.

Tone: grounded, direct, tough-love, raw.

Rules:
- Be original every single time
- NEVER use overused phrases
- Vary topics heavily
- Plain text only. Never use **bold**, *italics*, markdown, asterisks.
- Use ONLY simple hyphen - 
- Never start the sentence with a dash or hyphen. Begin directly with the words."""

    elif mode == "flirt":
        prompt = """You are AI Flirt Beast — master of smooth, playful one-liners.

Write **EXACTLY ONE very short sentence**. Maximum 20 words.

Tone: cheeky, confident, teasing, seductive but classy.

Rules:
- Be original every single time
- Playful, bold, witty — never creepy
- Plain text only. Never use **bold**, *italics*, markdown, asterisks.
- Use ONLY simple hyphen - 
- Never start the sentence with a dash or hyphen. Begin directly with the words."""

    elif mode == "stoic":
        prompt = """Write EXACTLY ONE short sentence only.
Tone: calm, blunt, direct, no-nonsense wisdom like Marcus Aurelius or Seneca.

CRITICAL: No poetry, no metaphors, no nature imagery, no art, no garden, no creative references, no self-help talk about effort or excuses.
Keep it simple, practical, grounded.
Plain text only. Never use **bold**, *italics*, markdown, asterisks.
Use ONLY simple hyphen - 
Never start the sentence with a dash or hyphen. Begin directly with the words."""

    else:
        prompt = """Write ONE sentence only. Tone: direct, human, grounded. Plain text only. Use ONLY simple hyphen -"""

    prompt += context
    prompt += "\n\nYour reply:"

    return prompt

def get_fallback(mode):
    fallbacks = {
        "hot": ["Most people don't want freedom - they want a comfortable cage."],
        "boost": ["Discipline is just self-respect with a deadline."],
        "flirt": ["That smile should come with a warning label."],
        "stoic": ["The obstacle is the way."]
    }
    return random.choice(fallbacks.get(mode, fallbacks["stoic"]))

def ai_line(mode, comment_context="", model=DEFAULT_MODEL):
    prompt = build_prompt(mode, comment_context)
    for attempt in range(3):
        try:
            r = requests.post(OLLAMA_URL, json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 1.65,
                "repeat_penalty": 1.9,
            }, timeout=60)
            r.raise_for_status()
            text = r.json().get("response", "").strip()
            if text and 5 <= len(text.split()) <= 25:
                return clean_text(text)
        except:
            if attempt < 2:
                continue
    return get_fallback(mode)

def generate_line(mode="hot", comment_context="", model=DEFAULT_MODEL):
    line = ai_line(mode, comment_context, model)
    header = f"🔥 {mode.upper()} #{random.randint(1000,9999)} 🔥"
    colored = f"{COLORS['header']}{header}{COLORS['reset']}\n{COLORS['text']}{line}{COLORS['reset']}\n"
    return colored, line

def copy_to_clipboard(text):
    try:
        subprocess.run('clip', input=text + '\n', text=True, check=False, encoding='utf-8')
        print(f"{COLORS['text']}📋 Copied to clipboard!{COLORS['reset']}")
    except:
        pass

def main():
    parser = argparse.ArgumentParser(description="🔥 AI QUOTE BEAST")
    parser.add_argument("-m", "--mode", type=str, default=None, choices=["stoic", "hot", "boost", "flirt"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("-l", "--last", action="store_true")
    parser.add_argument("--blind", action="store_true", help="Ignore clipboard and generate blind quote")

    args = parser.parse_args()

    if args.last or args.mode is None:
        args.mode = get_last_mode()

    save_last_mode(args.mode)

    print(f"{COLORS['header']}AI QUOTE BEAST v9.9 ACTIVATED — Mode: {args.mode} — Model: {args.model} — {datetime.now().strftime('%Y-%m-%d %H:%M')}{COLORS['reset']}\n")

    # === SMART CLIPBOARD LOGIC ===
    clipboard_text = get_clipboard().strip()
    last_ai = get_last_ai_quote()

    # If clipboard is our own previous quote → treat as blind (fresh)
    if clipboard_text == last_ai or args.blind or not clipboard_text:
        comment_context = ""
    else:
        comment_context = clipboard_text

    colored, raw = generate_line(args.mode, comment_context, args.model)
    print(colored)
    
    if raw:
        copy_to_clipboard(raw)
        save_last_ai_quote(raw)   # remember what we just made

if __name__ == "__main__":
    main()
