import random
import argparse
import sys
from datetime import datetime
import requests
import json
import os
import msvcrt
import time
import subprocess

# Force proper UTF-8 output on Windows (prevents mojibake)
sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_URL = "http://192.168.1.67:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"

HISTORY_FILE = "quote_beast_history.json"
MAX_HISTORY = 100   # ← sensible limit so the file never gets huge

COLORS = {
    "header": "\033[96m",     # Cyan for the 🔥 header
    "text":   "\033[97m",     # Bright White - easy to read on black
    "reset":  "\033[0m"
}

def clean_text(text):
    """Aggressively replace ALL fancy dashes/quotes with plain ASCII versions."""
    replacements = {
        '—': '-', '–': '-', '―': '-', '‐': '-', '‑': '-',
        '‘': "'", '’': "'", '“': '"', '”': '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()

def load_history():
    """Load history (new format: list of dicts). Returns only the quotes (strings) for the prompt.
    Backward compatible with old string-only history files."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, list) and data:
                # New format: [{"mode": "...", "quote": "..."}, ...]
                if isinstance(data[0], dict):
                    return [entry["quote"] for entry in data[-MAX_HISTORY:]]
                # Old format: just list of strings
                else:
                    return data[-MAX_HISTORY:]
        except:
            pass
    return []

def save_history(history_list, mode, raw_quote):
    """Append new quote with its mode and keep only the last MAX_HISTORY entries."""
    # Build new entry
    entry = {"mode": mode, "quote": raw_quote}
    
    # Load existing (or start fresh)
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = []
        except:
            data = []
    else:
        data = []
    
    # Append new one
    data.append(entry)
    
    # Trim to MAX_HISTORY
    data = data[-MAX_HISTORY:]
    
    # Save pretty-printed (one entry per line, easy to read)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def build_prompt(mode, previous=None):
    if mode == "hot":
        prompt = """You are AI Quote Beast — the most savage hot take generator alive.

Write **EXACTLY ONE very short sentence**. Maximum 20 words.

Brutal, sarcastic, irreverent. Casual internet language, swearing allowed.

Rules:
- Boldly contradict a common belief
- Short. Punchy. No fluff. No long explanations.
- Completely new topic every time
- Plain text only. Never use **bold**, *italics*, markdown, asterisks, or any special formatting.
- Use ONLY simple hyphen - (never em dash —, en dash –, or any fancy punctuation)

Good short examples:
- Therapy is just paid friends for people too scared to fix their shit.
- Hustle culture is just rich people selling burnout as a personality.
- Most "self-care" is just expensive procrastination with better lighting.
- Your dream job is still a job.

Recent takes (avoid these topics and style):"""
        if previous:
            prompt += "\n" + "\n".join(f"- {t}" for t in previous)
        prompt += "\n\nNow drop a fresh, short, savage one:"
        return prompt

    if mode == "boost":
        prompt = """You are a no-bullshit motivation machine.

Write **EXACTLY ONE very short sentence**. Maximum 20 words.

Tone: grounded, direct, tough-love, raw. Casual internet tone is fine, swearing allowed.

Rules:
- Be original every single time
- NEVER use overused phrases like "stop making excuses", "get to work", "you've got this", "take action"
- Vary topics heavily: habits, identity, regret, standards, systems, discomfort, future self, small choices, self-respect, etc.
- Plain text only. Never use **bold**, *italics*, markdown, asterisks, or any special formatting.
- Use ONLY simple hyphen - (never em dash —, en dash –, or any fancy punctuation)

Strong examples:
- Discipline is just self-respect with a deadline.
- Most people die at 30 and get buried at 75.
- You don't lack motivation - you lack standards.
- Comfort is the most expensive thing you'll ever buy.
- The version of you that wins already exists - you're just late.
- Small boring actions today = unrecognizable life in two years.

Recent boost lines (avoid repeating these ideas):"""
        if previous:
            prompt += "\n" + "\n".join(f"- {t}" for t in previous[-10:])
        prompt += "\n\nNow drop a completely fresh, hard-hitting one:"
        return prompt

    if mode == "flirt":
        prompt = """You are AI Flirt Beast — master of smooth, playful one-liners.

Write **EXACTLY ONE very short sentence**. Maximum 20 words.

Tone: cheeky, confident, teasing, seductive but classy. Casual internet vibe, light spice ok.

Rules:
- Be original every single time
- Playful, bold, witty — never creepy
- Vary topics: compliments, teasing, bold moves, tension, confidence, etc.
- Plain text only. Never use **bold**, *italics*, markdown, asterisks, or any special formatting.
- Use ONLY simple hyphen - (never em dash —, en dash –, or any fancy punctuation)

Strong examples:
- That smile should come with a warning label.
- You just made my whole day way more dangerous.
- If you were a crime, I'd be guilty as charged.
- Careful... you're making it hard to play it cool.
- You just raised the temperature in here by 10 degrees.

Recent flirt lines (avoid repeating these ideas):"""
        if previous:
            prompt += "\n" + "\n".join(f"- {t}" for t in previous[-10:])
        prompt += "\n\nNow drop a fresh, smooth one:"
        return prompt

    if mode == "stoic":
        return """Write EXACTLY ONE short sentence only.
Tone: calm, blunt, direct, no-nonsense wisdom like Marcus Aurelius or Seneca.

CRITICAL: No poetry, no metaphors, no nature imagery.
Keep it simple, practical, grounded.
Plain text only. Never use **bold**, *italics*, markdown, asterisks, or any special formatting.
Use ONLY simple hyphen - (never em dash —, en dash –, or any fancy punctuation)"""

    return "Write ONE sentence only. Tone: direct, human, grounded. Plain text only. Use ONLY simple hyphen -"

def get_fallback(mode):
    fallbacks = {
        "hot": ["Most people don't want freedom - they want a comfortable cage."],
        "boost": ["Discipline is just self-respect with a deadline."],
        "flirt": ["That smile should come with a warning label."],
        "stoic": ["The obstacle is the way.", "You have power over your mind - not outside events."]
    }
    return random.choice(fallbacks.get(mode, fallbacks["stoic"]))

def ai_line(mode, previous=None, model=DEFAULT_MODEL):
    prompt = build_prompt(mode, previous)
    for attempt in range(3):
        try:
            r = requests.post(OLLAMA_URL, json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 1.4 if mode in ["hot", "flirt"] else 1.3,
                "repeat_penalty": 1.5,
                "top_p": 0.9
            }, timeout=60)
            r.raise_for_status()
            text = r.json().get("response", "").strip()
            if text and len(text.split()) >= 5 and len(text.split()) <= 25:
                return clean_text(text)
        except:
            if attempt < 2:
                continue
    print(f"⚠️  Ollama failed after 3 tries, using fallback...")
    return get_fallback(mode)

def generate_line(mode="hot", previous=None, model=DEFAULT_MODEL):
    line = ai_line(mode, previous, model)
    
    header = f"🔥 {mode.upper()} #{random.randint(1000,9999)} 🔥"
    
    colored = (
        f"{COLORS['header']}{header}{COLORS['reset']}\n"
        f"{COLORS['text']}{line}{COLORS['reset']}\n"
    )
    return colored, line

def copy_to_clipboard(text):
    """Copy clean text to Windows clipboard"""
    try:
        subprocess.run('clip', input=text + '\n', text=True, check=False, encoding='utf-8')
        print(f"{COLORS['text']}📋 Copied to clipboard!{COLORS['reset']}")
    except:
        pass

def infinite_wait_for_key():
    print("Press Enter for next or X to exit... ", end="", flush=True)
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b'\r', b'\n'):
                print()
                return True
            elif key.lower() == b'x':
                print("\nExiting infinite mode...")
                return False
            else:
                print()
                return True
        time.sleep(0.05)

def main():
    parser = argparse.ArgumentParser(description="🔥 AI QUOTE BEAST v9.8 — quote_beast_history.json + mode tracking")
    parser.add_argument("-n", "--number", type=int, default=1)
    parser.add_argument("-m", "--mode", type=str, default="hot", 
                        choices=["stoic", "hot", "boost", "flirt"])
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--infinite", action="store_true")

    args = parser.parse_args()

    print(
        f"{COLORS['header']}AI QUOTE BEAST v9.8 ACTIVATED — Model: {args.model} — "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}{COLORS['reset']}\n"
    )

    # Only hot/boost/flirt use history
    previous = load_history() if args.mode in ["hot", "boost", "flirt"] else []

    try:
        if args.infinite:
            print("Infinite mode — Press Enter for next or X to exit\n")
            while True:
                colored, raw = generate_line(args.mode, previous, args.model)
                print(colored)
                copy_to_clipboard(raw)
                
                if args.mode in ["hot", "boost", "flirt"]:
                    previous.append(raw)                    # for next prompt
                    save_history(previous, args.mode, raw)  # saves with mode + trims
                
                if not infinite_wait_for_key():
                    break
        else:
            for _ in range(args.number):
                colored, raw = generate_line(args.mode, previous, args.model)
                print(colored)
                copy_to_clipboard(raw)
                
                if args.mode in ["hot", "boost", "flirt"]:
                    previous.append(raw)
                    save_history(previous, args.mode, raw)
    except KeyboardInterrupt:
        print(f"\n{COLORS['header']}Stopped.{COLORS['reset']}")
        sys.exit(0)

if __name__ == "__main__":
    main()
