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
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2")
GROQ_KEYS = [k for k in [GROQ_API_KEY, GROQ_API_KEY_2] if k]
if not GROQ_KEYS:
    raise ValueError("No Groq API keys found")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "qwen/qwen3.6-27b"
FALLBACK_MODEL = "openai/gpt-oss-20b"

KEY_SWAP = True
HISTORY_SIZE = 10
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COLORS = {"header": "\033[96m", "text": "\033[97m", "reset": "\033[0m"}

LAST_MODE_FILE = "last_mode.txt"
LAST_AI_QUOTE_FILE = "last_ai_quotes.txt"
PREFERRED_GROQ_KEY_FILE = "preferred_groq_key.txt"
SINGLE_FALLBACK = "This is a fallback."
REQUEST_TIMEOUT = 8
MAX_ATTEMPTS = 2


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
            return re.sub(r"\?{2,}", "", text).strip()
        except Exception:
            pass
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=2,
            )
            text = result.stdout.strip()
            return re.sub(r"\?{2,}", "", text).strip()
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
                ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value @'\n{text}\n'@"],
                capture_output=True,
                timeout=5,
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
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.strip().strip("\"'")
    text = text.lstrip(" -\u2013\u2014\u2022*#0123456789").strip()
    return text


def sanitize_context(ctx, max_chars=111):
    if not ctx:
        return ""
    ctx = ctx.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    ctx = ctx.replace("–", "-").replace("—", "-")
    ctx = re.sub(r"@\w+", "", ctx)
    ctx = re.sub(r"https?://\S+", "", ctx)
    ctx = re.sub(r"\bx\.com/\S+", "", ctx)
    ctx = unicodedata.normalize("NFKD", ctx)
    ctx = ctx.encode("ascii", errors="ignore").decode("ascii")
    ctx = re.sub(r"\?{2,}", "", ctx)
    ctx = re.sub(r"\.{2,}", ".", ctx)
    ctx = re.sub(r"[^\w\s.,!?'-]", "", ctx)
    ctx = " ".join(ctx.split()).strip()
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
            return [l.strip() for l in f.readlines() if l.strip()][-HISTORY_SIZE:]
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
            f.write("\n".join(quotes) + "\n")
    except Exception:
        pass


def get_preferred_key_index():
    try:
        with open(_path(PREFERRED_GROQ_KEY_FILE), "r", encoding="utf-8") as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def save_preferred_key_index(idx):
    try:
        with open(_path(PREFERRED_GROQ_KEY_FILE), "w", encoding="utf-8") as f:
            f.write(str(idx))
    except Exception:
        pass


BANNED_WORDS = {
    "sunshine",
    "follow",
    "retweet",
    "subscribe",
    "engage",
    "engagement",
    "notification",
    "notifications",
    "dm",
    "dms",
    "inbox",
    "collab",
    "collaboration",
}
BANNED_PHRASES = {
    "drop a",
    "drop your",
    "let me know",
    "tag a",
    "tell me",
    "hit the",
    "click the",
    "link in",
    "looks like",
}
TRAILING_FILLER = re.compile(
    r"\s+(already|somehow|tonight|today|right now|out there|anyhow|"
    r"sometimes|right here|at all|though|actually|literally|basically|"
    r"honestly|truly|really|definitely|absolutely|totally|completely|"
    r"certainly|clearly|obviously|simply|just|even|still|yet|then|"
    r"ever|never|always|often|soon|perhaps|maybe)[.!?]?$",
    re.IGNORECASE,
)
EMOJI_OR_SMILEY = re.compile(r"[\U0001F300-\U0001F9FF\u2600-\u27BF]$|[:;]-?[)D]$")


def strip_trailing_filler(text):
    for _ in range(5):
        cleaned = TRAILING_FILLER.sub("", text).strip()
        if cleaned == text:
            break
        text = cleaned
    text = re.sub(r"([^\w\s])\.$", r"\1", text)
    if text and not (text.endswith((".", "!", "?")) or bool(EMOJI_OR_SMILEY.search(text))):
        text += "."
    return text


def write_debug(line):
    print(f"{COLORS['header']}{line}{COLORS['reset']}")
    try:
        with open(_path("debug_api.txt"), "a", encoding="utf-8") as dbg:
            dbg.write(line + "\n")
        with open(_path("debug_api.txt"), "r", encoding="utf-8") as dbg:
            lines = dbg.readlines()
        if len(lines) > 300:
            with open(_path("debug_api.txt"), "w", encoding="utf-8") as dbg:
                dbg.writelines(lines[-300:])
    except Exception:
        pass


def rate_limit_summary(headers):
    if not headers:
        return ""
    h = {k.lower(): v for k, v in headers.items()}
    parts = []
    for key, label in (
        ("x-ratelimit-remaining-tokens", "tok_left"),
        ("x-ratelimit-limit-tokens", "tok_lim"),
        ("x-ratelimit-reset-tokens", "tok_reset"),
        ("x-ratelimit-remaining-requests", "req_left"),
        ("x-ratelimit-limit-requests", "req_lim"),
        ("x-ratelimit-reset-requests", "req_reset"),
        ("retry-after", "retry_after"),
    ):
        if key in h:
            parts.append(f"{label}={h[key]}")
    return " ".join(parts)


def build_messages(mode, comment_context="", short=False, recent=None):
    mode = (mode or "hot").strip().lower()
    limit = "1-11 words" if short else "14-25 words"
    if recent:
        stopwords = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "it", "its", "i", "you", "we", "they", "he", "she",
            "my", "your", "our", "their", "be", "are", "was", "were", "not", "no",
            "so", "do", "did", "have", "has", "had", "this", "that", "these", "those",
        }
        blocked = set()
        for q in recent[-3:]:
            for w in re.findall(r"[a-zA-Z']+", q.lower()):
                if w not in stopwords:
                    blocked.add(w)
        avoid = f"\nDo not use any of these words: {', '.join(sorted(blocked))}" if blocked else ""
    else:
        avoid = ""
    personas = {
        "hot": f"You are YonaHeet. Write a hot take ({limit}) that contradicts a common belief. Original, Punchy, Blunt.\n",
        "boost": f"Write ONE grounded motivational sentence ({limit}). Honest, no fluff.\n",
        "flirt": f"You are YanaHeat on X. Vibe: real, positive, hustling quietly, supportive. Write ONE complete reply ({limit}). Keep it genuine, no cringe.\n",
        "stoic": f"Write ONE stoic sentence ({limit}). Detached, factual. Like 'You control X, not Y'.\n",
    }
    persona = personas.get(mode, f"Write ONE sharp original sentence ({limit}).\n")
    banned_str = ", ".join(sorted(BANNED_WORDS | {"drop a", "let me know", "tag a"}))
    system = (
        f"{persona}"
        "- Natural contractions (I'm, you're, what's, don't, etc.). Perfect grammar.\n"
        "- Casual everyday language. Sound like a real person texting.\n"
        "- Prefer periods. Use exclamation marks only when really needed.\n"
        f"- Never use: {banned_str}.\n"
        "- Output ONLY the sentence. Nothing else.\n"
    )
    if comment_context:
        user = (
            f'React to this specifically: "{comment_context}"\n'
            f"Write ONE original, natural reply. Do not copy or closely rephrase the original. Stay on topic.{avoid}"
        )
    else:
        user = f"Write the complete sentence now.{avoid}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def force_single_sentence(text):
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"</?think>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"Here's a thinking process:.*", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"^thinking process:.*", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\s*\b(System|Assistant|Note|Explanation|I hope)\b.*", "", text, flags=re.I)
    text = re.sub(r"\?{2,}", "", text).strip()
    return text.strip().strip("\"'").strip()


def looks_like_assistant(s):
    if not s:
        return True
    s_lower = s.lower().strip()
    bad = [
        "i'm here to help",
        "as an ai",
        "as an assistant",
        "i can help",
        "let me know",
        "system:",
        "assistant:",
        "here's a thinking",
        "thinking process",
    ]
    if any(p in s_lower for p in bad):
        return True
    if len(s) < 8:
        return True
    if s.startswith(("(", "[", "{", '"', "'")) and len(s) < 20:
        return True
    if re.match(r"^[\W\d_]+$", s):
        return True
    if s.count("(") != s.count(")"):
        return True
    return False


def should_switch_model(result):
    err = (result.get("err") or "").lower()
    return (
        result.get("status") in (408, 503, 429)
        or result.get("kind") == "timeout"
        or "over capacity" in err
    )


def groq_once(key, messages, temp, max_tokens, model):
    t0 = time.time()
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temp,
        "max_completion_tokens": max_tokens,
        "top_p": 0.9,
    }
    if model.startswith("qwen/"):
        payload["reasoning_effort"] = "none"
    try:
        r = requests.post(
            GROQ_URL,
            json=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        elapsed = time.time() - t0
        body_text = r.text or ""
        try:
            resp_json = r.json() if body_text else {}
        except Exception:
            resp_json = {}
        err = resp_json.get("error", {}) or {}
        err_msg = err.get("message", "") if isinstance(err, dict) else str(err)
        if not err_msg and r.status_code >= 400:
            err_msg = body_text[:300]
        message = {}
        if isinstance(resp_json, dict):
            message = resp_json.get("choices", [{}])[0].get("message", {}) or {}
        raw = (message.get("content") or message.get("reasoning_content") or "").strip()
        return {
            "ok": r.status_code == 200 and bool(raw),
            "status": r.status_code,
            "raw": raw,
            "err": err_msg or "",
            "headers": r.headers,
            "elapsed": elapsed,
            "kind": "http",
            "model": model,
        }
    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "status": 408,
            "raw": "",
            "err": f"client timeout after {REQUEST_TIMEOUT}s",
            "headers": {},
            "elapsed": time.time() - t0,
            "kind": "timeout",
            "model": model,
        }
    except Exception as e:
        return {
            "ok": False,
            "status": 0,
            "raw": "",
            "err": f"{type(e).__name__}: {e}"[:200],
            "headers": {},
            "elapsed": time.time() - t0,
            "kind": "exception",
            "model": model,
        }


def accept_or_reject(text, recent, min_words, max_words):
    text = strip_trailing_filler(clean_text(force_single_sentence(text)))
    if not text or looks_like_assistant(text):
        return None, "BAD TEXT"
    words = len(text.split())
    recent_for_dup = recent[-3:] if recent else []
    fingerprint = " ".join(text.lower().split()[:5])
    recent_fingerprints = [" ".join(q.lower().split()[:5]) for q in recent_for_dup]
    is_dup = text.lower() in [q.lower() for q in recent_for_dup] or fingerprint in recent_fingerprints
    output_words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    has_blocked = bool(output_words & BANNED_WORDS) or any(p in text.lower() for p in BANNED_PHRASES)
    ends_ok = text.endswith((".", "!", "?")) or bool(EMOJI_OR_SMILEY.search(text))
    reasons = []
    if not (min_words <= words <= max_words):
        reasons.append(f"{words}w")
    if is_dup:
        reasons.append("dup")
    if has_blocked:
        reasons.append("blocked")
    if not ends_ok:
        reasons.append("no end")
    if reasons:
        return None, ",".join(reasons)
    return text, ""


def same_text(a, b):
    def norm(s):
        return (s or "").replace("\r", "\n").strip()
    return norm(a) == norm(b)


def ai_line(mode, comment_context="", short=False):
    mode = (mode or "hot").strip().lower()
    max_words = 11 if short else 25
    min_words = 1 if short else 4
    recent = get_recent_quotes()
    started = time.time()
    last_status, last_err = 0, ""
    used_key_num, next_key_num = 1, 1

    for attempt in range(MAX_ATTEMPTS):
        try:
            messages = build_messages(mode, comment_context, short, recent=recent)
            temp = min(0.65 + attempt * 0.08, 1.1)
            max_tokens = 50 if short else 60
            start_idx = get_preferred_key_index() % len(GROQ_KEYS)

            for offset in range(len(GROQ_KEYS)):
                key_idx = (start_idx + offset) % len(GROQ_KEYS)
                key = GROQ_KEYS[key_idx]
                used_key_num = key_idx + 1
                next_key_num = (key_idx + 1) % len(GROQ_KEYS) + 1
                models_to_try = [MODEL]
                if FALLBACK_MODEL != MODEL:
                    models_to_try.append(FALLBACK_MODEL)

                for model_name in models_to_try:
                    result = groq_once(key, messages, temp, max_tokens, model_name)
                    last_status, last_err = result["status"], result["err"]
                    rl = rate_limit_summary(result["headers"])

                    if not result["ok"]:
                        write_debug(
                            f"  → Groq key {used_key_num} model={model_name} failed "
                            f"status={result['status']} kind={result['kind']} "
                            f"{result['elapsed']:.1f}s err={result['err']!r} {rl}"
                        )
                        if should_switch_model(result) and model_name == MODEL:
                            write_debug(f"  → switching to {FALLBACK_MODEL}")
                            continue
                        break

                    text, why = accept_or_reject(result["raw"], recent, min_words, max_words)
                    if not text:
                        write_debug(
                            f"attempt={attempt} key={used_key_num} model={model_name} "
                            f"status={result['status']} REJECTED ({why}) "
                            f"{result['elapsed']:.1f}s out={result['raw'][:120]!r}"
                        )
                        break

                    if KEY_SWAP and len(GROQ_KEYS) > 1:
                        save_preferred_key_index(next_key_num - 1)

                    ctx_display = comment_context or ""
                    if len(ctx_display) > 70:
                        ctx_display = ctx_display[:70] + "..."
                    write_debug(
                        f"attempt={attempt} key={used_key_num} to_key={next_key_num} "
                        f"model={model_name} status={result['status']} temp={temp:.2f} "
                        f"{result['elapsed']:.1f}s total={time.time()-started:.1f}s "
                        f"{rl} in={ctx_display!r} out={text!r}"
                    )
                    return text

            write_debug(
                f"attempt={attempt} key={used_key_num} status={last_status} "
                f"ALL_KEYS_FAILED err={last_err!r} total={time.time()-started:.1f}s"
            )
        except Exception as e:
            write_debug(f"attempt={attempt} EXCEPTION={type(e).__name__}: {str(e)[:100]}")
            break

    write_debug(
        f"GIVING UP status={last_status} err={last_err!r} "
        f"total={time.time()-started:.1f}s using fallback sentence"
    )
    return SINGLE_FALLBACK


def generate_line(mode="hot", comment_context="", short=False):
    line = ai_line(mode, comment_context, short)
    tag = ("SHORT-" + mode.upper()) if short else mode.upper()
    header = f"FIRE {tag} #{random.randint(1000, 9999)}"
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

    print(
        f"{COLORS['header']}AI QUOTE BEAST — Mode: {args.mode} — "
        f"{datetime.now().strftime('%H:%M')}{COLORS['reset']}\n"
    )

    clipboard_text = get_clipboard()
    last_ai = get_last_ai_quote()
    if args.blind or not clipboard_text or same_text(clipboard_text, last_ai) or args.number > 1:
        comment_context = ""
    else:
        comment_context = sanitize_context(clipboard_text)

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
