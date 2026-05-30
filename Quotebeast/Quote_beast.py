#!/usr/bin/env python3
import random
import argparse
import sys
import json
import re
from datetime import datetime
import requests
import os
import subprocess
import platform
import traceback

sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_URL = "http://192.168.1.67:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"

LAST_MODE_FILE = "last_mode.txt"
LAST_AI_QUOTE_FILE = "last_ai_quote.txt"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

COLORS = {
    "header": "\033[96m",
    "text":   "\033[97m",
    "reset":  "\033[0m"
}

def is_windows():
    return platform.system().lower().startswith("win")

def get_clipboard():
    try:
        if is_windows():
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Clipboard'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=2
            )
            return result.stdout.strip()
        else:
            return ""
    except Exception:
        return ""

def copy_to_clipboard(text):
    try:
        if is_windows():
            subprocess.run('clip', input=text + '\n', text=True, check=False, encoding='utf-8')
        print(f"{COLORS['text']}📋 Copied to clipboard!{COLORS['reset']}")
    except Exception:
        pass

def clean_text(text):
    if not text:
        return ""
    # Attempt to fix common mojibake (Windows clipboard corruption)
    try:
        text = text.encode("latin-1").decode("utf-8")
    except Exception:
        pass

    replacements = {
        "—": "-", "–": "-", "―": "-", "‐": "-", "‑": "-",
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "…": "..."
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.strip()

    # Remove wrapping quotes
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")) or \
       (text.startswith('“') and text.endswith('”')) or \
       (text.startswith('‘') and text.endswith('’')):
        text = text[1:-1].strip()

    text = text.strip('"\'“”‘’')
    text = text.lstrip(' -–—•*#0123456789').strip()
    return text

def sanitize_context(ctx, max_chars=120):
    if not ctx:
        return ""
    s = " ".join(ctx.split())
    s = re.sub(r'^(i am|i\'m|i have|i\'ve|you are|i was|i\'m a|i am a)\b[^.?!]*[.?!]?\s*', '', s, flags=re.I)
    parts = re.split(r'[.?!]\s*', s)
    if parts:
        last = parts[-1].strip()
        if last:
            s = last
    if len(s) > max_chars:
        s = s[-max_chars:]
        idx = s.find(' ')
        if idx > 0:
            s = s[idx+1:]
    s = re.sub(r'^(you are|i am|i\'m)\b', '', s, flags=re.I).strip()
    return s

def _path(name):
    return os.path.join(SCRIPT_DIR, name)

def get_last_mode():
    path = _path(LAST_MODE_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return "hot"

def save_last_mode(mode):
    try:
        with open(_path(LAST_MODE_FILE), "w", encoding="utf-8") as f:
            f.write(mode)
    except Exception:
        pass

def get_last_ai_quote():
    path = _path(LAST_AI_QUOTE_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""

def save_last_ai_quote(text):
    try:
        with open(_path(LAST_AI_QUOTE_FILE), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass

def build_prompt(mode, comment_context="", short=False):
    mode = (mode or "").strip().lower()
    context = f"\n\nPrevious message you're replying to (react directly to it): {comment_context}" if comment_context else ""

    # === SHARED OUTPUT RULES (generalized) ===
    OUTPUT_RULES = (
        "CRITICAL OUTPUT RULES:\n"
        "- Output EXACTLY ONE single sentence.\n"
        "- Plain text only. No emojis, no markdown, no quotes, no asterisks, no bullet points.\n"
        "- Do NOT explain, apologize, or add any extra text.\n"
        "- Do NOT role-play as an AI or offer help.\n"
    )

    if short:
        if mode == "hot":
            persona = (
                "Write ONE ultra-short hot take (max 8 words).\n"
                "Brutal, sarcastic, irreverent. Swearing allowed.\n"
                "Must be a sharp opinion about human behavior, society, habits, or daily life.\n"
                "Never use pet/animal clichés.\n"
                f"{OUTPUT_RULES}"
            )
        elif mode == "boost":
            persona = (
                "Write ONE ultra-short grounded motivational line (max 8 words).\n"
                "Direct and supportive. No judgment, no shaming, no tough love.\n"
                f"{OUTPUT_RULES}"
            )
        elif mode == "flirt":
            persona = (
                "Write ONE ultra-short flirt line (max 8 words).\n"
                "Cheeky, confident, teasing, bold but classy. Never creepy.\n"
                f"{OUTPUT_RULES}"
            )
        elif mode == "stoic":
            persona = (
                "Write ONE ultra-short stoic sentence (max 8 words).\n"
                "Tone: cold, blunt, factual.\n"
                "Must follow one of these structures:\n"
                "  - You choose X, not Y.\n"
                "  - If X happens → you control Y.\n"
                "  - Wanting less X leads to less Y.\n"
                "Forbidden: metaphors, imagery, poetic language, emotional words, encouragement, moralizing, philosophy references.\n"
                f"{OUTPUT_RULES}"
            )
        else:
            persona = f"Write ONE ultra-short sentence (max 8 words).\n{OUTPUT_RULES}"

    else:  # FULL MODE
        if mode == "hot":
            persona = (
                "You are AI Quote Beast — savage hot take generator.\n"
                "Write ONE very short sentence (max 20 words).\n"
                "Brutal, sarcastic, irreverent. Use casual internet language.\n"
                "Boldly contradict a common belief or take a sharp angle on society, tech, relationships, work, or human behavior.\n"
                "Never repeat pet/animal clichés. Surprise the reader.\n"
                f"{OUTPUT_RULES}"
            )
        elif mode == "boost":
            persona = (
                "You are a direct, grounded motivational speaker.\n"
                "Write ONE very short sentence (max 20 words).\n"
                "Honest tone. No judgment, no shaming.\n"
                f"{OUTPUT_RULES}"
            )
        elif mode == "flirt":
            persona = (
                "You are AI Flirt Beast — master of smooth, playful one-liners.\n"
                "Write ONE very short sentence (max 20 words).\n"
                "Cheeky, confident, teasing, seductive but classy. Be original and never creepy.\n"
                f"{OUTPUT_RULES}"
            )
        elif mode == "stoic":
            persona = (
                "Write ONE short stoic sentence (max 20 words).\n"
                "Tone: detached, factual, unsentimental.\n"
                "Must express a hard truth about control, responsibility, perception, or consequence.\n"
                "Preferred structures:\n"
                "  - You control X, not the outcome.\n"
                "  - If X happens → then Y.\n"
                "  - Wanting less X leads to less suffering.\n"
                "Forbidden: metaphors, imagery, poetic language, emotional vocabulary, encouragement, moralizing, references to Stoicism or philosophy.\n"
                f"{OUTPUT_RULES}"
            )
        else:
            persona = f"Write ONE sentence only. Tone: direct and grounded.\n{OUTPUT_RULES}"

    return persona + context + "\n\nYour reply:"

def get_fallback(mode, short=False):
    if short:
        fb = {
            "hot": ["Truth hurts louder than lies."],
            "boost": ["You’ve got this."],
            "flirt": ["You’re trouble, aren’t you."],
            "stoic": ["Control what you can."]
        }
        return random.choice(fb.get(mode, ["Stay sharp."]))
    fb = {
        "hot": ["Most people don't want freedom - they want a comfortable cage."],
        "boost": ["Discipline is just self-respect with a deadline."],
        "flirt": ["That smile should come with a warning label."],
        "stoic": ["The obstacle is the way."]
    }
    return random.choice(fb.get(mode, ["Stay sharp."]))

def extract_first_nonempty_line(s):
    if not s:
        return ""
    for line in str(s).splitlines():
        line = line.strip()
        if line:
            return line
    return str(s).strip()

def detect_assistant_style(s):
    if not s:
        return False
    s_low = s.lower()
    assistant_signals = [
        "i'm here to help", "i am here to help", "i'm sorry", "i am sorry",
        "i don't know", "i do not know", "as an ai", "as an assistant",
        "i can help", "i can assist", "let me know", "how can i help",
        "i'm not sure", "i'm not certain", "if you want", "if you'd like",
        "i'm here", "i am here", "i'm a", "i am a", "i work as"
    ]
    for sig in assistant_signals:
        if sig in s_low:
            return True
    if "\n" in s and len(s.splitlines()) > 1:
        return True
    return False

def safe_json_load(text):
    try:
        return json.loads(text)
    except Exception:
        return None

def ai_line(mode, comment_context="", model=DEFAULT_MODEL, short=False, debug=False):
    mode = (mode or "").strip().lower()
    short = bool(short)

    SYSTEM_PREFIX = (
        "SYSTEM: You are a persona generator. Do NOT identify as an AI or assistant. "
        "Do NOT offer help, explanations, or ask clarifying questions. Produce ONLY the single-line persona output requested.\n\n"
    )
    STRONG_PREFIX = (
        "SYSTEM: You are a persona generator. You MUST NOT speak as an assistant, "
        "you MUST NOT apologize, offer help, or explain. Output exactly one short sentence only, matching the persona instructions below.\n\n"
    )

    min_words_map = {
        "hot": 1,
        "flirt": 1,
        "boost": 3,
        "stoic": 1
    }
    min_words = min_words_map.get(mode, 1)

    def first_line_only(s):
        if not s:
            return ""
        for line in str(s).splitlines():
            line = line.strip()
            if line:
                return line
        return str(s).strip()

    def looks_like_assistant(s):
        if not s:
            return False
        s_low = s.lower()
        assistant_signals = [
            "i'm here to help", "i am here to help", "i'm sorry", "i am sorry",
            "i don't know", "i do not know", "as an ai", "as an assistant",
            "i can help", "i can assist", "let me know", "how can i help",
            "i'm not sure", "i'm not certain", "if you want", "if you'd like",
            "i'm here", "i am here"
        ]
        for sig in assistant_signals:
            if sig in s_low:
                return True
        if "\n" in s and len(s.splitlines()) > 1:
            return True
        if s_low.startswith("system:") or s_low.startswith("assistant:"):
            return True
        if s_low.startswith("you are") and mode != "boost":
            return True
        return False

    def base_temperature():
        if short:
            return 0.5 if mode == "stoic" else 1.2
        return 0.6 if mode == "stoic" else 1.4

    for attempt in range(3):
        try:
            if attempt == 0:
                prompt = STRONG_PREFIX + build_prompt(mode, comment_context, short)
            else:
                prompt = SYSTEM_PREFIX + build_prompt(mode, comment_context, short)

            temperature = base_temperature()

            r = requests.post(OLLAMA_URL, json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "repeat_penalty": 2.0,
                "top_p": 0.9
            }, timeout=60)

            if debug:
                try:
                    print(f"DEBUG: status_code={r.status_code}", file=sys.stderr)
                    print("DEBUG: raw response (first 2000 chars):", file=sys.stderr)
                    print(r.text[:2000], file=sys.stderr)
                except Exception:
                    pass

            raw = ""
            try:
                data = r.json()
                if isinstance(data, dict):
                    for key in ("response", "text", "output", "result", "generated_text"):
                        if key in data and data[key]:
                            raw = data[key]
                            break
                    if not raw:
                        for v in data.values():
                            if isinstance(v, str) and v.strip():
                                raw = v
                                break
                            if isinstance(v, list) and v:
                                for item in v:
                                    if isinstance(item, str) and item.strip():
                                        raw = item
                                        break
                                    if isinstance(item, dict):
                                        for sub in item.values():
                                            if isinstance(sub, str) and sub.strip():
                                                raw = sub
                                                break
                                    if raw:
                                        break
                                if raw:
                                    break
                elif isinstance(data, str):
                    raw = data
                else:
                    raw = r.text
            except Exception:
                raw = r.text

            text = first_line_only(raw).strip()

            if not text or looks_like_assistant(text):
                if debug:
                    print("DEBUG: assistant-like or empty output detected, retrying...", file=sys.stderr)
                prompt = STRONG_PREFIX + build_prompt(mode, comment_context, short)
                temperature = 0.4 if mode == "stoic" else min(1.6, base_temperature() + 0.2)
                continue

            words = len(text.split())
            if short:
                if 1 <= words <= 8:
                    return clean_text(text)
                else:
                    prompt = STRONG_PREFIX + build_prompt(mode, comment_context, short)
                    temperature = 0.4 if mode == "stoic" else min(1.6, base_temperature() + 0.2)
                    continue
            else:
                if min_words <= words <= 25:
                    return clean_text(text)
                if mode == "stoic":
                    first_sentence = text.split(".")[0].strip()
                    if 1 <= len(first_sentence.split()) <= 25:
                        return clean_text(first_sentence)
                    prompt = STRONG_PREFIX + build_prompt(mode, comment_context, short)
                    temperature = 0.4
                    continue
                prompt = STRONG_PREFIX + build_prompt(mode, comment_context, short)
                temperature = min(1.6, base_temperature() + 0.2)
                continue

        except Exception:
            if attempt < 2:
                continue

    return get_fallback(mode, short)

def generate_line(mode="hot", comment_context="", model=DEFAULT_MODEL, short=False, debug=False):
    mode = (mode or "").strip().lower()
    short = bool(short)
    line = ai_line(mode, comment_context, model, short, debug=debug)
    tag = ("SHORT-" + mode.upper()) if short else mode.upper()
    header = f"🔥 {tag} #{random.randint(1000,9999)} 🔥"
    colored = f"{COLORS['header']}{header}{COLORS['reset']}\n{COLORS['text']}{line}{COLORS['reset']}\n"
    return colored, line

def main():
    parser = argparse.ArgumentParser(description="🔥 AI QUOTE BEAST")
    parser.add_argument("-m", "--mode", type=str, default=None, choices=["stoic", "hot", "boost", "flirt"])
    parser.add_argument("-n", "--number", type=int, default=1, help="Number of quotes to generate in a row")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("-l", "--last", action="store_true")
    parser.add_argument("--blind", action="store_true", help="Ignore clipboard and generate blind quote")
    parser.add_argument("--short", action="store_true", help="Generate ultra-short single-line output (max 8 words)")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging to stderr")

    args = parser.parse_args()

    if args.last or args.mode is None:
        args.mode = get_last_mode()

    print(f"{COLORS['header']}AI QUOTE BEAST v19 — Mode: {args.mode} — Model: {args.model} — {datetime.now().strftime('%Y-%m-%d %H:%M')}{COLORS['reset']}\n")

    clipboard_text = get_clipboard().strip()
    last_ai = get_last_ai_quote()

    if args.debug:
        print("DEBUG: SCRIPT_DIR =", SCRIPT_DIR, file=sys.stderr)
        try:
            print("DEBUG: CWD =", os.getcwd(), file=sys.stderr)
        except Exception:
            print("DEBUG: CWD = <unavailable>", file=sys.stderr)
        print("DEBUG: ARGS =", vars(args), file=sys.stderr)
        print("DEBUG: clipboard_text (raw) >>>", clipboard_text, "<<<", file=sys.stderr)
        print("DEBUG: last_ai_quote (file) >>>", last_ai, "<<<", file=sys.stderr)

    if args.last and not args.short:
        comment_context = ""
    else:
        if clipboard_text == last_ai or args.blind or not clipboard_text or args.number > 1:
            comment_context = ""
        else:
            comment_context = sanitize_context(clipboard_text, max_chars=120)

    num_quotes = max(1, args.number)

    for i in range(num_quotes):
        if i > 0:
            print()
        current_context = comment_context if i == 0 else ""
        try:
            colored, raw = generate_line(args.mode, current_context, args.model, args.short, debug=args.debug)
            if not raw:
                raise ValueError("Empty generation")
        except Exception as e:
            if args.debug:
                print("DEBUG: generation exception in main:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
            raw = get_fallback(args.mode, args.short)
            tag = ("SHORT-" + args.mode.upper()) if args.short else args.mode.upper()
            header = f"🔥 {tag} #{random.randint(1000,9999)} 🔥"
            colored = f"{COLORS['header']}{header}{COLORS['reset']}\n{COLORS['text']}{raw}{COLORS['reset']}\n"
        print(colored)

        if raw and i == num_quotes - 1:
            copy_to_clipboard(raw)
            save_last_ai_quote(raw)

    save_last_mode(args.mode)

if __name__ == "__main__":
    main()
