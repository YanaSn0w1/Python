#!/usr/bin/env python3
import random
import argparse
import sys
import re
import unicodedata
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

MAIN_MODEL = "qwen/qwen3.6-27b"
FALLBACK_MODELS = [
    "groq/compound",
    "groq/compound-mini",
    "allam-2-7b",
]

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
    if is_windows():
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
            text = (data or "").strip()
            text = re.sub(r'\?{2,}', '', text).strip()
            return text
        except Exception:
            pass

        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw'],
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

def sanitize_context(ctx, max_chars=111):
    if not ctx:
        return ""
    
    # First convert smart quotes/apostrophes to straight ones
    ctx = ctx.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    ctx = ctx.replace("–", "-").replace("—", "-")
    
    ctx = re.sub(r'@\w+', '', ctx)
    ctx = re.sub(r'https?://\S+', '', ctx)
    ctx = re.sub(r'\bx\.com/\S+', '', ctx)
    
    ctx = unicodedata.normalize('NFKD', ctx)
    ctx = ctx.encode('ascii', errors='ignore').decode('ascii')
    
    ctx = re.sub(r'\?{2,}', '', ctx)
    ctx = re.sub(r'\.{2,}', '.', ctx)
    ctx = re.sub(r'[^\w\s.,!?\'-]', '', ctx)
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
    'sunshine',
    'follow', 'retweet', 'subscribe', 'engage', 'engagement',
    'notification', 'notifications', 'dm', 'dms', 'inbox',
    'collab', 'collaboration',
}

BANNED_PHRASES = {
    'drop a', 'drop your', 'let me know', 'tag a',
    'tell me', 'hit the', 'click the', 'link in', 'looks like',
}

TRAILING_FILLER = re.compile(
    r'\s+(already|somehow|tonight|today|right now|out there|anyhow|'
    r'sometimes|right here|at all|though|actually|literally|basically|'
    r'honestly|truly|really|definitely|absolutely|totally|completely|'
    r'certainly|clearly|obviously|simply|just|even|still|yet|then|'
    r'there|here|ever|never|always|often|soon|perhaps|maybe)[.!?]?$',
    re.IGNORECASE
)

def strip_trailing_filler(text):
    for _ in range(5):
        cleaned = TRAILING_FILLER.sub('', text).strip()
        if cleaned == text:
            break
        text = cleaned

    # Remove trailing period right after an emoji
    text = re.sub(r'([^\w\s])\.$', r'\1', text)

    if text and text[-1] not in '.!?' and not re.search(r'[\U0001F300-\U0001F9FF]$', text):
        text += '.'
    return text

def get_fallback(mode=None, short=False):
    return SINGLE_FALLBACK


def build_messages(mode, comment_context="", short=False, recent=None):
    mode = (mode or "hot").strip().lower()
    limit = "1-11 words" if short else "14-25 words"

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
            f"You are YonaHeet. Write a hot take ({limit}) that contradicts "
            f"a common belief. Original, Punchy, Blunt.\n"
        ),
        "boost": f"Write ONE grounded motivational sentence ({limit}). Honest, no fluff.\n",
        "flirt": (
            f"You are YanaHeat on X. Vibe: real, positive, hustling quietly, supportive. "
            f"Write ONE complete reply ({limit}). Keep it genuine, no cringe.\n"
        ),
        "stoic": f"Write ONE stoic sentence ({limit}). Detached, factual. Like 'You control X, not Y'.\n",
    }
    persona = personas.get(mode, f"Write ONE sharp original sentence ({limit}).\n")

    banned_str = ', '.join(sorted(BANNED_WORDS | {'drop a', 'let me know', 'tag a'}))

    system = (
        f"{persona}"
        "- Natural contractions (I'm, you're, what's, don't, etc.). Perfect grammar.\n"
        "- Casual everyday language. Sound like a real person texting.\n"
        "- Prefer periods. Use exclamation marks only when really needed.\n"
        f"- Never use: {banned_str}.\n"
        "- Output ONLY the sentence. Nothing else.\n"
    )

    if comment_context:
        user = f"React to this specifically: \"{comment_context}\"\nWrite ONE original, natural reply. Do not copy or closely rephrase the original. Stay on topic.{avoid}"
    else:
        user = f"Write the complete sentence now.{avoid}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def force_single_sentence(text):
    if not text:
        return ""
    # Light cleaning only — no longer forces a single sentence
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</?think>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<reasoning>.*?</reasoning>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"Here's a thinking process:.*", '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'^thinking process:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'\s*\b(System|Assistant|Note|Explanation|I hope)\b.*', '', text, flags=re.I)
    text = re.sub(r'\?{2,}', '', text).strip()
    return text.strip().strip('"\'').strip()


def looks_like_assistant(s):
    if not s:
        return True
    bad = ["i'm here to help", "as an ai", "as an assistant", "i can help",
           "let me know", "system:", "assistant:", "here's a thinking", "thinking process"]
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
    max_words = 11 if short else 25
    min_words = 1 if short else 4
    model = MAIN_MODEL
    fallback_index = 0
    recent = get_recent_quotes()

    for attempt in range(8):
        try:
            messages = build_messages(mode, comment_context, short, recent=recent)
            temp = min(0.65 + attempt * 0.06, 1.15)

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temp,
                "max_completion_tokens": 50 if short else 60,
                "top_p": 0.9,
            }

            # Only Qwen supports reasoning_effort
            if "qwen" in model:
                payload["reasoning_effort"] = "none"

            r = requests.post(
                API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )

            resp_json = r.json()
            message = resp_json.get("choices", [{}])[0].get("message", {})
            raw = (message.get("content") or message.get("reasoning_content") or "").strip()
            err = resp_json.get("error", "")

            write_debug(f"attempt={attempt} model={model} status={r.status_code} temp={temp:.2f} err={repr(err)} raw={repr(raw[:400])}")

            if r.status_code in (429, 400) or (not raw and model != MAIN_MODEL):
                if fallback_index < len(FALLBACK_MODELS):
                    model = FALLBACK_MODELS[fallback_index]
                    fallback_index += 1
                    time.sleep(0.4)
                    continue
                else:
                    break

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

            if (min_words <= words <= max_words and 
                not is_dup and 
                not has_blocked and 
                text.endswith(('.', '!', '?'))):
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

    write_debug(f"CONTEXT raw_clipboard={clipboard_text!r}")
    write_debug(f"CONTEXT raw_codepoints={[hex(ord(c)) for c in clipboard_text[:30]]!r}")
    write_debug(f"CONTEXT sanitized={comment_context!r}")

    if comment_context:
        print(f"{COLORS['header']}Context: \"{comment_context[:60]}\"{COLORS['reset']}\n")

    for i in range(max(1, args.number)):
        if i > 0:
            print()
        current_context = comment_context if i == 0 else ""
        colored, raw = generate_line(args.mode, current_context, args.short)
        print(colored)
        if raw and raw != SINGLE_FALLBACK and i == max(1, args.number) - 1:
            copy_to_clipboard(raw)
            save_last_ai_quote(raw)

    save_last_mode(args.mode)


if __name__ == "__main__":
    main()
