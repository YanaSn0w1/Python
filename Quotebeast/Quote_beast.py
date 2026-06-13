#!/usr/bin/env python3
import random
import argparse
import sys
import re
from datetime import datetime
import requests
import os
import subprocess
import platform
import time

sys.stdout.reconfigure(encoding='utf-8')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set")

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MAIN_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

LAST_MODE_FILE = "last_mode.txt"
LAST_AI_QUOTE_FILE = "last_ai_quotes.txt"
HISTORY_SIZE = 10
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COLORS = {"header": "\033[96m", "text": "\033[97m", "reset": "\033[0m"}

SINGLE_FALLBACK = "This is a fallback."


def _path(name):
    return os.path.join(SCRIPT_DIR, name)

def is_windows():
    return platform.system().lower().startswith("win")

def get_clipboard():
    try:
        if is_windows():
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Clipboard'],
                capture_output=True, text=True, encoding='utf-8',
                errors='replace', timeout=2
            )
            text = result.stdout.strip()
            text = re.sub(r'\?{2,}', '', text).strip()
            return text
    except Exception:
        pass
    return ""

def copy_to_clipboard(text):
    if is_windows():
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
            finally:
                win32clipboard.CloseClipboard()
            print(f"{COLORS['text']}Copied!{COLORS['reset']}")
            return
        except Exception:
            pass
        try:
            subprocess.run(
                ['powershell', '-NoProfile', '-Command', f'Set-Clipboard -Value @\'\n{text}\n\'@'],
                capture_output=True, timeout=5
            )
            print(f"{COLORS['text']}Copied!{COLORS['reset']}")
            return
        except Exception:
            pass
    print(f"{COLORS['text']}{text}{COLORS['reset']}")

def clean_text(text):
    if not text:
        return ""
    try:
        text = text.encode("latin-1").decode("utf-8")
    except Exception:
        pass
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "..."
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.strip().strip('"\'')
    text = text.lstrip(' -\u2013\u2014\u2022*#0123456789').strip()
    return text

def sanitize_context(ctx, max_chars=120):
    if not ctx:
        return ""
    ctx = re.sub(r'@\w+', '', ctx)
    ctx = re.sub(r'https?://\S+', '', ctx)
    ctx = re.sub(r'\bx\.com/\S+', '', ctx)
    ctx = ctx.encode('ascii', errors='ignore').decode('ascii')
    ctx = re.sub(r'\?{2,}', '', ctx)
    ctx = ' '.join(ctx.split()).strip()
    return ctx[:max_chars]

def get_last_mode():
    try:
        with open(_path(LAST_MODE_FILE), "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "hot"

def save_last_mode(mode):
    try:
        with open(_path(LAST_MODE_FILE), "w", encoding="utf-8") as f:
            f.write(mode)
    except Exception:
        pass

def get_recent_quotes():
    try:
        with open(_path(LAST_AI_QUOTE_FILE), "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            return lines[-HISTORY_SIZE:]
    except Exception:
        return []

def get_last_ai_quote():
    quotes = get_recent_quotes()
    return quotes[-1] if quotes else ""

def save_last_ai_quote(text):
    try:
        quotes = get_recent_quotes()
        quotes.append(text)
        quotes = quotes[-HISTORY_SIZE:]
        with open(_path(LAST_AI_QUOTE_FILE), "w", encoding="utf-8") as f:
            f.write('\n'.join(quotes) + '\n')
    except Exception:
        pass


BANNED_WORDS = {
    'sunshine', 'wishing',
    'follow', 'retweet', 'subscribe', 'engage', 'engagement',
    'notification', 'notifications', 'dm', 'dms', 'inbox',
    'collab', 'collaboration',
}

BANNED_PHRASES = {
    'drop a', 'drop your', 'let me know', 'sounds like', 'tag a',
    'tell me', 'hit the', 'click the', 'link in', 'looks like',
}

OUTPUT_RULES = (
    "- Non poetic/robotic.\n"
    "- Never use anyone's name.\n"
)

TRAILING_FILLER = re.compile(
    r'\s+(already|somehow|tonight|today|right now|out there|anyhow|'
    r'sometimes|right here|at all|though|actually|literally|basically|'
    r'honestly|truly|really|definitely|absolutely|totally|completely|'
    r'certainly|clearly|obviously|simply|just|even|still|yet|now|then|'
    r'there|here|ever|never|always|often|soon|perhaps|maybe)[.!?]?$',
    re.IGNORECASE
)

def strip_trailing_filler(text):
    for _ in range(5):
        cleaned = TRAILING_FILLER.sub('', text).strip()
        if cleaned == text:
            break
        text = cleaned
    if text and text[-1] not in '.!?':
        text += '.'
    return text

def get_fallback(mode=None, short=False):
    return SINGLE_FALLBACK


def build_messages(mode, comment_context="", short=False, recent=None):
    mode = (mode or "hot").strip().lower()
    limit = "max 8 words" if short else "max 15 words"

    if recent:
        stopwords = {'a','an','the','and','or','but','in','on','at','to','for',
                     'of','with','is','it','its','i','you','we','they','he','she',
                     'my','your','our','their','be','are','was','were','not','no',
                     'so','do','did','have','has','had','this','that','these','those'}
        blocked = set()
        for q in recent[-3:]:
            for w in re.findall(r"[a-zA-Z']+", q.lower()):
                if w not in stopwords:
                    blocked.add(w)
        blocked_list = sorted(blocked)
        avoid = f"\nDo not use any of these words: {', '.join(blocked_list)}" if blocked_list else ""
    else:
        avoid = ""

    personas = {
        "hot": (
            f"You are YonaHeet. Write ONE hot take ({limit}) that boldly contradicts "
            f"a common belief. Blunt, punchy, never rude or insulting.\n"
        ),
        "boost": f"Write ONE grounded motivational sentence ({limit}). Honest, no fluff.\n",
        "flirt": (
            f"You are YanaHeat on X. Vibe: real, positive, hustling quietly, supportive. "
            f"Write ONE reply ({limit}). Keep it genuine, no cringe.\n"
        ),
        "stoic": f"Write ONE stoic sentence ({limit}). Detached, factual. Like 'You control X, not Y'.\n",
    }
    persona = personas.get(mode, f"Write ONE sharp original sentence ({limit}).\n")
    banned_str = ', '.join(sorted(BANNED_WORDS | {'drop a', 'let me know', 'tag a'}))
    system = persona + OUTPUT_RULES + f"- Never use: {banned_str}.\n"

    if comment_context:
        user = f"React to this specifically: \"{comment_context}\"\nWrite ONE sentence in response. Stay on topic.{avoid}"
    else:
        user = f"Write the sentence now.{avoid}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def force_single_sentence(text):
    if not text:
        return ""
    for line in text.splitlines():
        line = line.strip()
        if line:
            text = line
            break
    match = re.search(r'^(.+?[.!?])(\s|$)', text)
    if match:
        text = match.group(1).strip()
    text = re.sub(r'\s*(System|Assistant|Note|Explanation|I hope).*', '', text, flags=re.I)
    text = re.sub(r'\?{2,}', '', text).strip()
    return text.strip().strip('"\'').strip()

def looks_like_assistant(s):
    if not s:
        return True
    bad = ["i'm here to help", "as an ai", "as an assistant", "i can help",
           "let me know", "system:", "assistant:"]
    return any(p in s.lower() for p in bad)

def write_debug(line):
    try:
        with open(_path("debug_api.txt"), "a", encoding="utf-8") as dbg:
            dbg.write(line + "\n")
        with open(_path("debug_api.txt"), "r", encoding="utf-8") as dbg:
            lines = dbg.readlines()
        if len(lines) > 50:
            with open(_path("debug_api.txt"), "w", encoding="utf-8") as dbg:
                dbg.writelines(lines[-50:])
    except Exception:
        pass

def ai_line(mode, comment_context="", short=False):
    mode = (mode or "hot").strip().lower()
    max_words = 10 if short else 15
    model = MAIN_MODEL
    recent = get_recent_quotes()

    for attempt in range(8):
        try:
            messages = build_messages(mode, comment_context, short, recent=recent)
            temp = min(0.7 + attempt * 0.07, 1.3)
            r = requests.post(
                API_URL,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": 35,
                    "top_p": 0.9,
                    "stop": ["\n", "System:", "Assistant:", "Note:"],
                },
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )

            resp_json = r.json()
            raw = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            err = resp_json.get("error", "")
            write_debug(f"attempt={attempt} model={model} status={r.status_code} temp={temp:.2f} err={repr(err)} raw={repr(raw[:100])}")

            if r.status_code == 429:
                model = FALLBACK_MODEL
                time.sleep(0.5)
                continue
            if r.status_code == 400:
                model = FALLBACK_MODEL
                continue

            text = force_single_sentence(raw)
            text = clean_text(text)
            text = strip_trailing_filler(text)

            if not text or looks_like_assistant(text):
                continue

            words = len(text.split())
            fingerprint = ' '.join(text.lower().split()[:4])
            recent_fingerprints = [' '.join(q.lower().split()[:4]) for q in recent]
            is_dup = text.lower() in [q.lower() for q in recent] or fingerprint in recent_fingerprints
            output_words = set(re.findall(r"[a-zA-Z]+", text.lower()))
            text_lower = text.lower()
            has_blocked = (
                bool(output_words & BANNED_WORDS) or
                any(p in text_lower for p in BANNED_PHRASES)
            )
            if 1 <= words <= max_words and not is_dup and not has_blocked:
                return text

            write_debug(f"  REJECTED: words={words} max={max_words} dup={is_dup} banned={has_blocked} text={repr(text)}")
            time.sleep(0.2)

        except Exception as e:
            write_debug(f"attempt={attempt} EXCEPTION={repr(str(e))}")
            time.sleep(0.3)

    return SINGLE_FALLBACK


def generate_line(mode="hot", comment_context="", short=False):
    line = ai_line(mode, comment_context, short)
    tag = ("SHORT-" + mode.upper()) if short else mode.upper()
    header = f"🔥 {tag} #{random.randint(1000, 9999)} 🔥"
    colored = f"{COLORS['header']}{header}{COLORS['reset']}\n{COLORS['text']}{line}{COLORS['reset']}\n"
    return colored, line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=["stoic", "hot", "boost", "flirt"])
    parser.add_argument("-n", "--number", type=int, default=1)
    parser.add_argument("--short", action="store_true")
    parser.add_argument("--blind", action="store_true")
    args = parser.parse_args()

    if args.mode is None:
        args.mode = get_last_mode()

    save_last_mode(args.mode)

    print(f"{COLORS['header']}AI QUOTE BEAST — Mode: {args.mode} — {datetime.now().strftime('%H:%M')}{COLORS['reset']}\n")

    clipboard_text = get_clipboard()
    last_ai = get_last_ai_quote()

    if args.blind or not clipboard_text or clipboard_text.strip().replace('\r\n', '\n') == last_ai.strip().replace('\r\n', '\n') or args.number > 1:
        comment_context = ""
    else:
        comment_context = sanitize_context(clipboard_text)

    if comment_context:
        print(f"{COLORS['header']}Context: \"{comment_context[:60]}\"{COLORS['reset']}\n")

    fallback_flag = _path("last_was_fallback.txt")
    try:
        os.remove(fallback_flag)
    except Exception:
        pass

    used_fallback = False
    for i in range(max(1, args.number)):
        if i > 0:
            print()
        current_context = comment_context if i == 0 else ""
        colored, raw = generate_line(args.mode, current_context, args.short)
        print(colored)
        if raw and i == max(1, args.number) - 1:
            if raw == SINGLE_FALLBACK:
                used_fallback = True
            else:
                copy_to_clipboard(raw)
                save_last_ai_quote(raw)

    if used_fallback:
        try:
            with open(fallback_flag, "w", encoding="utf-8") as f:
                f.write("1")
        except Exception:
            pass

    save_last_mode(args.mode)


if __name__ == "__main__":
    main()
