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
import importlib

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY environment variable not set!")

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MAIN_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

LAST_MODE_FILE = "last_mode.txt"
LAST_AI_QUOTE_FILE = "last_ai_quotes.txt"
HISTORY_SIZE = 10

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COLORS = {"header": "\033[96m", "text": "\033[97m", "reset": "\033[0m"}


# ── History ───────────────────────────────────────────────────────────────────

def get_recent_quotes():
    path = _path(LAST_AI_QUOTE_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                return lines[-HISTORY_SIZE:]
        except:
            pass
    return []


def save_recent_quote(text):
    try:
        quotes = get_recent_quotes()
        quotes.append(text)
        quotes = quotes[-HISTORY_SIZE:]
        with open(_path(LAST_AI_QUOTE_FILE), "w", encoding="utf-8") as f:
            f.write('\n'.join(quotes) + '\n')
    except:
        pass


# ── Clipboard ─────────────────────────────────────────────────────────────────

def is_windows():
    return platform.system().lower().startswith("win")


def get_clipboard():
    if is_windows():
        try:
            win32 = importlib.import_module("win32clipboard")
            try:
                win32.OpenClipboard()
                try:
                    data = win32.GetClipboardData(win32.CF_UNICODETEXT)
                    return (data or "").strip()
                finally:
                    win32.CloseClipboard()
            except Exception:
                try:
                    win32.CloseClipboard()
                except:
                    pass
        except Exception:
            pass
        try:
            p = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                capture_output=True
            )
            try:
                text = p.stdout.decode("utf-8")
            except:
                text = p.stdout.decode("utf-8", errors="replace")
            return (text or "").strip()
        except:
            pass
    return ""


def copy_to_clipboard(text):
    # Write to file so AHK can set clipboard reliably
    try:
        with open(_path("last_output.txt"), "w", encoding="utf-8") as f:
            f.write(text)
    except:
        pass
    if is_windows():
        try:
            win32 = importlib.import_module("win32clipboard")
            win32.OpenClipboard()
            try:
                win32.EmptyClipboard()
                win32.SetClipboardData(win32.CF_UNICODETEXT, text)
            finally:
                win32.CloseClipboard()
            print(f"{COLORS['text']}📋 Copied!{COLORS['reset']}")
            return
        except Exception:
            try:
                win32.CloseClipboard()
            except:
                pass
        # PowerShell fallback
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Set-Clipboard -Value {repr(text)}"],
                capture_output=True
            )
            print(f"{COLORS['text']}📋 Copied!{COLORS['reset']}")
            return
        except:
            pass
    print(f"{COLORS['text']}{text}{COLORS['reset']}")


# ── Text utils ────────────────────────────────────────────────────────────────

def clean_text(text):
    if not text:
        return ""
    try:
        text = text.encode("latin-1").decode("utf-8")
    except:
        pass
    replacements = {
        "\u2014": "-", "\u2013": "-",
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2026": "..."
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'") and text.count("'") == 2):
        text = text[1:-1].strip()
    text = text.lstrip(' -\u2013\u2014\u2022*#0123456789').strip()
    return text


EMOJI_RE = re.compile(
    r'(?:\U0001F3F4[\U000E0000-\U000E007F]+'
    r'|[\U0001F1E6-\U0001F1FF]{2}'
    r'|[\u2600-\u27BF\U0001F300-\U0001FAFF\U0001F900-\U0001F9FF]'
    r'(?:\uFE0F)?(?:[\U0001F3FB-\U0001F3FF])?'
    r'(?:\u200D[\u2600-\u27BF\U0001F300-\U0001FAFF\U0001F900-\U0001F9FF]'
    r'(?:\uFE0F)?(?:[\U0001F3FB-\U0001F3FF])?)*'
    r')', flags=re.UNICODE)


def strip_emojis(text):
    return EMOJI_RE.sub('', text or "").strip()


def sanitize_context(ctx, max_chars=160):
    if not ctx:
        return ""

    TWITTER_GREETINGS = {
        r'\bGM[!.,]?\b': 'GM',
        r'\bGA[!.,]?\b': 'GA',
        r'\bGE[!.,]?\b': 'GE',
        r'\bGN[!.,]?\b': 'GN',
    }
    COMMUNITY_TAGS = r'\b(CT|FT|JM|XRP|BTC|ETH|SOL|crypto\s+twitter|football\s+twitter)\b'
    TIME_WISH_PATTERNS = [
        (r'\b(sweet\s+dreams?)\b', 'Good Night'),
        (r'\b(rest\s+well|sleep\s+well|sleep\s+tight)\b', 'Good Night'),
        (r'\bsee\s+you\s+(tomorrow|tonight|later|soon)\b', 'Good Night'),
        (r'\b(?:happy|beautiful|peaceful|lovely|great|blessed|wonderful|amazing|magical|restful)\s+night\b', 'Good Night'),
        (r'\b(?:happy|beautiful|peaceful|lovely|great|blessed|wonderful|amazing)\s+evening\b', 'Good Evening'),
        (r'\b(?:happy|beautiful|peaceful|lovely|great|blessed|wonderful|amazing)\s+morning\b', 'Good Morning'),
        (r'\b(?:happy|beautiful|peaceful|lovely|great|blessed|wonderful|amazing)\s+afternoon\b', 'Good Afternoon'),
        (r'\bwish\b.{0,40}\b(night|evening|morning|afternoon)\b', None),
        (r'\b(night|evening)\b.{0,30}\b(stars?|moon|peaceful|beautiful|rest)\b', 'Good Night'),
    ]

    # Names that refer to the account owner — strip from incoming context
    OWN_NAMES = {'yana', 'yanaheat'}

    ctx = re.sub(r'@\w+', '', ctx)

    detected = None
    for raw_line in ctx.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        s = line.encode('ascii', errors='ignore').decode('ascii')
        s = " ".join(s.split()).strip()
        for pattern, replacement in TWITTER_GREETINGS.items():
            s = re.sub(pattern, replacement, s, flags=re.I)
        s = re.sub(COMMUNITY_TAGS, '', s, flags=re.I).strip()
        s = " ".join(s.split())
        m = re.search(r'\b(good\s*(?:morning|afternoon|evening|night|day))\b', s, flags=re.I)
        if m:
            greeting = None
            for word in ['morning', 'afternoon', 'evening', 'night', 'day']:
                if word in m.group(1).lower():
                    greeting = 'Good ' + word.capitalize()
                    break
            if greeting:
                rest = s[m.end():].strip()
                rest = re.sub(COMMUNITY_TAGS, '', rest, flags=re.I).strip()
                rest = re.sub(r'^\s*(and|or|to|the|a)\s+', '', rest, flags=re.I).strip()
                rest = re.sub(r'\b(fam|all|everyone|folks|world|friends|peeps|y\'all|yall)\b', '', rest, flags=re.I).strip()
                # Strip own name
                for name in OWN_NAMES:
                    rest = re.sub(rf'\b{name}\b', '', rest, flags=re.I).strip()
                rest = " ".join(rest.split())
                if rest and len(rest.split()) >= 2:
                    return greeting + ' — ' + rest
                return greeting
        m2 = re.search(r'\b(goodnight|goodmorning|goodevening|goodafternoon|morning|afternoon|evening|night)\b', s, flags=re.I)
        if m2:
            word = m2.group(1).lower()
            mapping = {
                'goodnight': 'Good Night', 'goodmorning': 'Good Morning',
                'goodevening': 'Good Evening', 'goodafternoon': 'Good Afternoon',
                'morning': 'Morning', 'afternoon': 'Afternoon',
                'evening': 'Evening', 'night': 'Night',
            }
            greeting = mapping.get(word, word.capitalize())
            rest = s[m2.end():].strip()
            rest = re.sub(COMMUNITY_TAGS, '', rest, flags=re.I).strip()
            rest = re.sub(r'^\s*(and|or|to|the|a)\s+', '', rest, flags=re.I).strip()
            rest = re.sub(r'\b(fam|all|everyone|folks|world|friends|peeps|y\'all|yall)\b', '', rest, flags=re.I).strip()
            for name in OWN_NAMES:
                rest = re.sub(rf'\b{name}\b', '', rest, flags=re.I).strip()
            rest = " ".join(rest.split())
            if rest and len(rest.split()) >= 2:
                return greeting + ' — ' + rest
            return greeting
        if detected is None:
            s_lower = s.lower()
            for pattern, mapped in TIME_WISH_PATTERNS:
                if re.search(pattern, s_lower):
                    if mapped:
                        detected = mapped
                    else:
                        for word, greeting in [
                            ('morning', 'Good Morning'), ('afternoon', 'Good Afternoon'),
                            ('evening', 'Good Evening'), ('night', 'Good Night')
                        ]:
                            if word in s_lower:
                                detected = greeting
                                break
                    break

    if detected:
        return detected

    display_name_words = set()
    first_real_line = next((l.strip() for l in ctx.splitlines() if l.strip()), "")
    if first_real_line and not re.search(r'@\w+', first_real_line) and len(first_real_line.split()) <= 1 and not first_real_line.isupper():
        for w in first_real_line.split():
            w = re.sub(r'[^a-zA-Z]', '', w)
            if len(w) > 2:
                display_name_words.add(w.lower())

    content_lines = []
    for line in ctx.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r'@\w+', stripped):
            continue
        s_tmp = stripped.encode('ascii', errors='ignore').decode('ascii').strip()
        s_tmp = re.sub(r'https?://\S+|pic\.\S+', '', s_tmp).strip()
        if s_tmp:
            content_lines.append(s_tmp)
        if len(content_lines) >= 2:
            break

    if not content_lines:
        return ""

    s = ' '.join(content_lines)
    s = " ".join(s.split()).strip()
    if display_name_words:
        words = s.split()
        words = [w for w in words if w.lower().rstrip('.,!?') not in display_name_words]
        s = " ".join(words).strip()
    if not s:
        return ""
    return s[:max_chars]


def _path(name):
    return os.path.join(SCRIPT_DIR, name)


def get_last_mode():
    path = _path(LAST_MODE_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            pass
    return "hot"


def save_last_mode(mode):
    try:
        with open(_path(LAST_MODE_FILE), "w", encoding="utf-8") as f:
            f.write(mode)
    except:
        pass


def get_last_ai_quote():
    quotes = get_recent_quotes()
    return quotes[-1] if quotes else ""


def save_last_ai_quote(text):
    save_recent_quote(text)


# ── Banned content ────────────────────────────────────────────────────────────

BANNED_WORDS = [
    "sunshine", "sleepyhead", "dms", " dm ",
    "retweet", "re-tweet", "engagement", " active",
    "notification", " fb ", "facebook", "connect"
]
# Own name — checked separately with word-boundary match
OWN_NAME_BAN = re.compile(r"\byana\b", re.IGNORECASE)
BANNED_PHRASES = [
    "gm morning", "gm good morning", "gn night", "gn good night",
    "ga afternoon", "ge evening",
    "that means a lot", "being called that", "considered a friend",
    "means everything", "nice to hear", "great to hear",
]
BANNED_AI_TELLS = ["as an ai", "i can help", "let me know"]


# ── Prompts ───────────────────────────────────────────────────────────────────

HARD_RULES = """Rules:
- One sentence only. Stop after the period/exclamation/question mark.
- Plain text: no emojis, no markdown, no quotes, no asterisks.
- Never use anyone's name, including Yana. Use I, you, they, or no subject.
- Use contractions (I'd, I'm, don't, it's).
- Never say: sunshine, sleepyhead, dm, follow, retweet, engagement, notification, facebook."""

MODE_PERSONAS = {
    "hot": (
        "You write bold hot takes that contradict popular opinion.\n"
        "Tone: blunt, punchy, a little sarcastic.\n"
        "Style examples (never repeat these):\n"
        "  Meetings are just ideas waiting to die.\n"
        "  Hustle culture is a scam with good branding.\n"
    ),
    "boost": (
        "You write grounded, practical motivation. No fluff, no clichés.\n"
        "Style examples (never repeat these):\n"
        "  The version of you that shows up daily already knows what to do.\n"
        "  Momentum is built in the moments nobody's watching.\n"
    ),
    "flirt": (
        "You write short, punchy social replies that match the energy of what someone said.\n"
        "Hype post → amplify it. Warm post → be genuine. Funny post → be witty.\n"
        "Never romantic. Never use names or titles.\n"
    ),
    "stoic": (
        "You write calm, detached one-liners in the style of a stoic philosopher.\n"
        "Style examples (never repeat these):\n"
        "  Discomfort is the only honest teacher.\n"
        "  The obstacle is the way.\n"
    ),
}


def build_messages(mode, comment_context="", short=False, target_words=None, recent=None, max_words=45):
    mode = (mode or "hot").strip().lower()
    persona = MODE_PERSONAS.get(mode, "You write concise, original one-liners.\n")
    has_context = bool(comment_context)

    GREETING_MAP = {
        'good morning': 'Good Morning',
        'good afternoon': 'Good Afternoon',
        'good evening': 'Good Evening',
        'good night': 'Good Night',
        'good day': 'Good Day',
        'morning': 'Morning',
        'afternoon': 'Afternoon',
        'evening': 'Evening',
        'night': 'Night',
        'gm': 'GM',
        'ga': 'GA',
        'ge': 'GE',
        'gn': 'GN',
    }

    reply_word = None
    extra = ""
    if has_context:
        ctx_lower = comment_context.lower()
        for key in sorted(GREETING_MAP, key=len, reverse=True):
            if ctx_lower.startswith(key):
                reply_word = GREETING_MAP[key]
                extra = comment_context[len(key):].lstrip(' —,.!').strip()
                break

    is_greeting = reply_word is not None

    avoid_hint = ""
    if recent:
        avoid_hint = f"\nDo not repeat or closely rephrase any of these: {recent[-5:]}"

    system = f"{persona}\n{HARD_RULES}\nMax {max_words} words. Do not repeat or summarize what was said."

    if not has_context:
        user = f"Write one original sentence.{avoid_hint}"

    elif is_greeting:
        if extra:
            user = f"Reply to \"{reply_word}, {extra}\". Start with \"{reply_word}\". Max {max_words} words. Example: \"{reply_word}, [short reaction].\"{avoid_hint}"
        else:
            user = f"Reply to \"{reply_word}\". Start with \"{reply_word}\". Max {max_words} words. Example: \"{reply_word}, [short thought].\"{avoid_hint}"

    else:
        is_question = '?' in comment_context
        tone_verb = {
            "hot": "Challenge or subvert",
            "boost": "Find the positive angle in",
            "flirt": "Match the energy of",
            "stoic": "State a calm truth about",
        }.get(mode, "React to")

        if is_question:
            user = (
                f"Topic: \"{comment_context}\"\n"
                f"Answer directly in first person. Be specific. One sentence.{avoid_hint}"
            )
        else:
            user = (
                f"Topic: \"{comment_context}\"\n"
                f"{tone_verb} this in one sentence.{avoid_hint}"
            )

    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]


# ── Generation ────────────────────────────────────────────────────────────────

MAX_ATTEMPTS = 12
NUM_PREDICT_SHORT = 60
NUM_PREDICT_LONG  = 120
TOP_P_SEQUENCE    = [0.85, 0.9, 0.95]
TEMP_SEQUENCE     = [0.75, 0.85, 0.95]
BACKOFF_SECONDS   = 0.25
SHORT_MAX_WORDS   = 15
DEFAULT_STOP_LIST = ["System:", "Assistant:", "Note:", "Explanation:"]
SINGLE_FALLBACK   = "This is a fallback."


def force_single_sentence(text):
    if not text:
        return ""
    match = re.search(r'([A-Z][^.!?]+[.!?])', text)
    if match:
        return match.group(1).strip()
    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    first_line = re.sub(
        r'\s*(System|Assistant|Note|Explanation|I hope|Regards|Reacting to).*?$',
        '', first_line, flags=re.I
    ).strip()
    m2 = re.search(r'^(.+?[.!?])(\s|$)', first_line)
    if m2:
        return m2.group(1).strip()
    return first_line.strip()


def ai_line(mode, comment_context="", model=MAIN_MODEL, short=False):
    mode = (mode or "").strip().lower()
    short = bool(short)
    has_context = bool(comment_context)
    if has_context:
        model = MAIN_MODEL

    target_words = None
    max_words = 6  # tight cap for blind
    if has_context:
        src_words = len(comment_context.replace(' — ', ' ').split())
        if short:
            max_words = max(6, min(src_words + 3, 10))
        else:
            lo = max(5, src_words - 2)
            hi = min(15, src_words + 3)
            max_words = random.randint(lo, hi)

        try:
            with open(os.path.join(SCRIPT_DIR, "debug_api.txt"), "a", encoding="utf-8") as dbg:
                dbg.write(f"BUDGET: ctx={repr(comment_context[:60])} src={src_words} max={max_words} short={short}\n")
        except:
            pass

    seen_this_run = set()
    recent = get_recent_quotes()

    for attempt in range(MAX_ATTEMPTS):
        try:
            messages = build_messages(
                mode, comment_context, short,
                target_words=target_words, recent=recent, max_words=max_words
            )
            temp = (
                min(0.85 + attempt * 0.05, 1.3)
                if has_context
                else TEMP_SEQUENCE[min(attempt, len(TEMP_SEQUENCE) - 1)]
            )
            r = requests.post(
                API_URL,
                json={
                    "model":       model,
                    "messages":    messages,
                    "temperature": temp,
                    "max_tokens":  NUM_PREDICT_LONG,
                    "top_p":       TOP_P_SEQUENCE[min(attempt, len(TOP_P_SEQUENCE) - 1)],
                    "stop":        DEFAULT_STOP_LIST,
                },
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=60
            )

            resp_json = r.json()
            raw = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")

            try:
                with open(os.path.join(SCRIPT_DIR, "debug_api.txt"), "a", encoding="utf-8") as dbg:
                    err = resp_json.get("error", "")
                    dbg.write(
                        f"attempt={attempt} model={model} status={r.status_code} "
                        f"short={short} ctx={repr(comment_context)} max_words={max_words} "
                        f"err={repr(err)} raw={repr(raw[:120])}\n"
                    )
            except:
                pass

            if r.status_code == 400:
                model = FALLBACK_MODEL
                continue

            if r.status_code == 429:
                if model == MAIN_MODEL:
                    model = FALLBACK_MODEL
                    continue
                else:
                    break

            text = force_single_sentence(raw)
            text = clean_text(text)
            words = len(text.split())

            def _core(t):
                t = t.lower().strip()
                for key in ['good morning', 'good afternoon', 'good evening', 'good night',
                            'morning', 'afternoon', 'evening', 'night', 'gm', 'gn', 'ga', 'ge']:
                    if t.startswith(key):
                        t = t[len(key):].lstrip(' ,—').strip()
                        break
                return ' '.join(t.split()[:5])

            text_core = _core(text)
            recent_cores = [_core(q) for q in recent]
            seen_cores = [_core(s) for s in seen_this_run]

            is_duplicate = (
                text in seen_this_run
                or text.lower() in [q.lower() for q in recent]
                or (text_core and text_core in recent_cores)
                or (text_core and text_core in seen_cores)
            )
            has_banned = (
                any(b in text.lower() for b in BANNED_WORDS)
                or any(p in text.lower() for p in BANNED_PHRASES)
                or any(x in text.lower() for x in BANNED_AI_TELLS)
            )

            if text and 1 <= words <= max_words and not is_duplicate and not has_banned:
                return text

            seen_this_run.add(text)
            try:
                with open(os.path.join(SCRIPT_DIR, "debug_api.txt"), "a", encoding="utf-8") as dbg:
                    dbg.write(
                        f"  REJECTED: words={words} max={max_words} "
                        f"dup={is_duplicate} banned={has_banned} text={repr(text)}\n"
                    )
            except:
                pass
            time.sleep(BACKOFF_SECONDS)

        except Exception as e:
            try:
                with open(os.path.join(SCRIPT_DIR, "debug_api.txt"), "a", encoding="utf-8") as dbg:
                    dbg.write(f"attempt={attempt} EXCEPTION={repr(str(e))}\n")
            except:
                pass
            time.sleep(BACKOFF_SECONDS)

    print(f"{COLORS['text']}⚠️ This is a fallback{COLORS['reset']}")
    return SINGLE_FALLBACK


def generate_line(mode="hot", comment_context="", model=MAIN_MODEL, short=False):
    line = ai_line(mode, comment_context, model, short)
    line = strip_emojis(line)
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

    print(f"{COLORS['header']}AI QUOTE BEAST — Mode: {args.mode} — {datetime.now().strftime('%H:%M')}{COLORS['reset']}\n")

    clipboard_text = get_clipboard() or ""
    last_ai = get_last_ai_quote()
    clipboard_normalized = clipboard_text.strip()
    last_ai_normalized = last_ai.strip()
    if args.blind or not clipboard_text or clipboard_normalized == last_ai_normalized or args.number > 1:
        comment_context = ""
    else:
        _cb_ascii = clipboard_text.encode('ascii', errors='ignore').decode('ascii')
        _original_greeting = None
        for sh in ['GM', 'GN', 'GA', 'GE']:
            if re.search(rf'\b{sh}[!.,]?\b', _cb_ascii, re.I):
                _original_greeting = sh
                break
        comment_context = sanitize_context(clipboard_text)
        if _original_greeting and comment_context and any(
            comment_context.lower().startswith(g)
            for g in ['good morning', 'good afternoon', 'good evening', 'good night']
        ):
            comment_context = (
                _original_greeting + comment_context[comment_context.index(' '):]
                if ' ' in comment_context
                else _original_greeting
            )

        # FIX 1: bare greetings included so extra content (e.g. "my friend") gets appended
        pure_greetings = {
            'GM', 'GN', 'GA', 'GE',
            'Good Morning', 'Good Afternoon', 'Good Evening', 'Good Night', 'Good Day',
            'Morning', 'Afternoon', 'Evening', 'Night',
        }
        if comment_context in pure_greetings:
            for line in clipboard_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if re.search(r'@\w+', stripped):
                    continue
                if re.match(r'^\d+[hmd]$', stripped):
                    continue
                clean = stripped.encode('ascii', errors='ignore').decode('ascii')
                clean = re.sub(r'https?://\S+|pic\.\S+', '', clean).strip()
                clean = re.sub(
                    r'\b(GM|GN|GA|GE|Good\s+(?:Morning|Afternoon|Evening|Night|Day)|Morning|Afternoon|Evening|Night)\b',
                    '', clean, flags=re.I
                ).strip()
                clean = re.sub(r'\b(fam|all|everyone|folks|and)\b', '', clean, flags=re.I).strip()
                clean = ' '.join(clean.split())
                if len(clean.split()) >= 2:
                    comment_context = comment_context + ' — ' + clean
                    break

        # Strip own name from context so the model never sees it
        for own_name in ['Yana', 'YanaHeat']:
            comment_context = re.sub(rf'\b{own_name}\b', '', comment_context, flags=re.I).strip()
        comment_context = ' '.join(comment_context.split())

    GREETING_LABELS = {
        'good morning': '🌅 Good Morning detected',
        'good afternoon': '☀️ Good Afternoon detected',
        'good evening': '🌆 Good Evening detected',
        'good night': '🌙 Good Night detected',
        'morning': '🌅 Morning detected',
        'afternoon': '☀️ Afternoon detected',
        'evening': '🌆 Evening detected',
        'night': '🌙 Night detected',
    }
    if comment_context:
        base = comment_context.split(' — ')[0].lower().strip()
        label = GREETING_LABELS.get(base, f'📎 Context: "{comment_context}"')
        print(f"{COLORS['header']}{label}{COLORS['reset']}\n")

    try:
        with open(_path("debug_last_run.txt"), "w", encoding="utf-8") as f:
            f.write(f"mode={args.mode}\ncontext={repr(comment_context)}\nclipboard={repr(clipboard_text[:100])}\n")
    except:
        pass

    for i in range(max(1, args.number)):
        if i > 0:
            print()
        current_context = comment_context if i == 0 else ""
        colored, raw = generate_line(args.mode, current_context, MAIN_MODEL, args.short)
        print(colored)
        if raw and i == max(1, args.number) - 1:
            copy_to_clipboard(raw)
            save_last_ai_quote(raw)

    save_last_mode(args.mode)


if __name__ == "__main__":
    main()
