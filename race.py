import curses
import time
import json
import os
import random
import shutil
from datetime import datetime, timedelta
from statistics import mean

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
WORDS_PATH = os.path.join(DATA_DIR, "words.json")
STATS_PATH = os.path.join(DATA_DIR, "stats.json")

# --- CONFIGURATION & DEFAULTS ---
DEFAULT_CONFIG = {
    "list_idx": 0,
    "pacer": 0,
    "pacer_enabled": False,
    "theme_idx": 1,
    "pacer_marker_idx": 0,
    "caret_marker_idx": 3,
    "stats_period_idx": 0,
    "goals": {
        "daily": 0,
        "weekly": 0,
        "monthly": 0,
    },
}

STATS_PERIODS = ["daily", "weekly", "monthly", "all"]
THEME_NAMES = ["latte", "frappe", "macchiato", "mocha"]
MARKER_NAMES = ["underline", "block", "bright", "dim"]

# Catppuccin palette (https://github.com/catppuccin/palette)
CATPPUCCIN = {
    "latte": {
        "base": "#eff1f5",
        "text": "#4c4f69",
        "subtext": "#6c6f85",
        "green": "#40a02b",
        "red": "#d20f39",
        "pink": "#ea76cb",
        "yellow": "#df8e1d",
        "blue": "#1e66f5",
        "mauve": "#8839ef",
        "surface": "#e6e9ef",
    },
    "frappe": {
        "base": "#303446",
        "text": "#c6d0f5",
        "subtext": "#a5adce",
        "green": "#a6d189",
        "red": "#e78284",
        "pink": "#f4b8e4",
        "yellow": "#e5c890",
        "blue": "#8caaee",
        "mauve": "#ca9ee6",
        "surface": "#414559",
    },
    "macchiato": {
        "base": "#24273a",
        "text": "#cad3f5",
        "subtext": "#a5adcb",
        "green": "#a6da95",
        "red": "#ed8796",
        "pink": "#f5bde6",
        "yellow": "#eed49f",
        "blue": "#8aadf4",
        "mauve": "#c6a0f6",
        "surface": "#363a4f",
    },
    "mocha": {
        "base": "#1e1e2e",
        "text": "#cdd6f4",
        "subtext": "#a6adc8",
        "green": "#a6e3a1",
        "red": "#f38ba8",
        "pink": "#f5c2e7",
        "yellow": "#f9e2af",
        "blue": "#89b4fa",
        "mauve": "#cba6f7",
        "surface": "#313244",
    },
}

COLOR_SLOT_BASE = 16
COLOR_SLOTS = {
    "text": 16,
    "subtext": 17,
    "green": 18,
    "red": 19,
    "pink": 20,
    "yellow": 21,
    "blue": 22,
    "mauve": 23,
    "base": 24,
    "surface": 25,
}

THEME_FALLBACK = {
    "latte": {
        "text": curses.COLOR_BLACK,
        "subtext": curses.COLOR_BLACK,
        "green": curses.COLOR_GREEN,
        "red": curses.COLOR_RED,
        "pink": curses.COLOR_MAGENTA,
        "yellow": curses.COLOR_YELLOW,
        "blue": curses.COLOR_BLUE,
        "mauve": curses.COLOR_MAGENTA,
        "base": curses.COLOR_WHITE,
        "surface": curses.COLOR_WHITE,
    },
    "frappe": {
        "text": curses.COLOR_WHITE,
        "subtext": curses.COLOR_WHITE,
        "green": curses.COLOR_GREEN,
        "red": curses.COLOR_RED,
        "pink": curses.COLOR_MAGENTA,
        "yellow": curses.COLOR_YELLOW,
        "blue": curses.COLOR_BLUE,
        "mauve": curses.COLOR_MAGENTA,
        "base": curses.COLOR_BLACK,
        "surface": curses.COLOR_BLACK,
    },
    "macchiato": {
        "text": curses.COLOR_WHITE,
        "subtext": curses.COLOR_WHITE,
        "green": curses.COLOR_GREEN,
        "red": curses.COLOR_RED,
        "pink": curses.COLOR_MAGENTA,
        "yellow": curses.COLOR_YELLOW,
        "blue": curses.COLOR_CYAN,
        "mauve": curses.COLOR_MAGENTA,
        "base": curses.COLOR_BLACK,
        "surface": curses.COLOR_BLACK,
    },
    "mocha": {
        "text": curses.COLOR_WHITE,
        "subtext": curses.COLOR_WHITE,
        "green": curses.COLOR_GREEN,
        "red": curses.COLOR_RED,
        "pink": curses.COLOR_MAGENTA,
        "yellow": curses.COLOR_YELLOW,
        "blue": curses.COLOR_CYAN,
        "mauve": curses.COLOR_MAGENTA,
        "base": curses.COLOR_BLACK,
        "surface": curses.COLOR_BLACK,
    },
}

DEFAULT_QUOTES = {
    "nietzsche": [
        "He who has a why to live for can bear almost any how.",
        "That which does not kill us makes us stronger.",
        "Without music, life would be a mistake.",
        "Beware that, when fighting monsters, you yourself do not become a monster... for when you gaze long into the abyss, the abyss gazes also into you.",
        "No one can construct for you the bridge upon which precisely you must cross the stream of life, no one but you yourself alone.",
        "You must have chaos within you to give birth to a dancing star.",
        "Sometimes people do not want to hear the truth because they do not want their illusions destroyed.",
        "The higher we soar the smaller we appear to those who cannot fly.",
        "There are no facts, only interpretations.",
        "Amor Fati: let that be my love henceforth! I do not want to wage war against what is ugly.",
    ],
    "mishima": [
        "Human life is limited, but I would like to live forever.",
        "A man who has attained mastery of an art reveals it in his every action.",
        "The instant that the blade of reality touched him, the beautiful illusion was reduced to ashes.",
        "Action is the only medium of expression for the body.",
        "Words are a medium that reduces reality to abstraction for transmission to our reason.",
        "True beauty is something that attacks, conquers, robs, and finally destroys.",
        "The special quality of hell is to see everything clearly down to the last detail.",
        "It is a common failing of childhood to think that if one makes a confession, one will be forgiven.",
        "Perfect purity is possible only when you are young and willing to die for an ideal.",
        "I want to make a poem of my life.",
    ],
}

# --- FILE HANDLING ---
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    for name in ("config.json", "words.json", "stats.json"):
        dest = os.path.join(DATA_DIR, name)
        legacy = os.path.join(BASE_DIR, name)
        if not os.path.exists(dest) and os.path.exists(legacy):
            shutil.move(legacy, dest)


def write_json(path, data):
    ensure_data_dir()
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def ensure_default_data():
    ensure_data_dir()
    write_json(WORDS_PATH, DEFAULT_QUOTES)
    if not os.path.exists(CONFIG_PATH):
        write_json(
            CONFIG_PATH,
            {
                "list_idx": DEFAULT_CONFIG["list_idx"],
                "pacer": DEFAULT_CONFIG["pacer"],
                "pacer_enabled": DEFAULT_CONFIG["pacer_enabled"],
                "theme_idx": DEFAULT_CONFIG["theme_idx"],
                "pacer_marker_idx": DEFAULT_CONFIG["pacer_marker_idx"],
                "caret_marker_idx": DEFAULT_CONFIG["caret_marker_idx"],
                "stats_period_idx": DEFAULT_CONFIG["stats_period_idx"],
                "goals": DEFAULT_CONFIG["goals"].copy(),
            },
        )
    if not os.path.exists(STATS_PATH):
        write_json(STATS_PATH, [])


def load_config():
    ensure_data_dir()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                saved_config = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged["goals"] = DEFAULT_CONFIG["goals"].copy()
                for key in (
                    "list_idx",
                    "pacer",
                    "pacer_enabled",
                    "theme_idx",
                    "pacer_marker_idx",
                    "caret_marker_idx",
                    "stats_period_idx",
                ):
                    if key in saved_config:
                        merged[key] = saved_config[key]
                if "pacer_enabled" not in saved_config:
                    merged["pacer_enabled"] = merged["pacer"] > 0
                if "goals" in saved_config and isinstance(saved_config["goals"], dict):
                    for period in merged["goals"]:
                        if period in saved_config["goals"]:
                            merged["goals"][period] = saved_config["goals"][period]
                return merged
        except Exception:
            pass
    return {
        "list_idx": DEFAULT_CONFIG["list_idx"],
        "pacer": DEFAULT_CONFIG["pacer"],
        "pacer_enabled": DEFAULT_CONFIG["pacer_enabled"],
        "theme_idx": DEFAULT_CONFIG["theme_idx"],
        "pacer_marker_idx": DEFAULT_CONFIG["pacer_marker_idx"],
        "caret_marker_idx": DEFAULT_CONFIG["caret_marker_idx"],
        "stats_period_idx": DEFAULT_CONFIG["stats_period_idx"],
        "goals": DEFAULT_CONFIG["goals"].copy(),
    }


def save_config():
    ensure_data_dir()
    with open(CONFIG_PATH, "w") as f:
        json.dump(
            {
                "list_idx": config["list_idx"],
                "pacer": config["pacer"],
                "pacer_enabled": config["pacer_enabled"],
                "theme_idx": config["theme_idx"],
                "pacer_marker_idx": config["pacer_marker_idx"],
                "caret_marker_idx": config["caret_marker_idx"],
                "stats_period_idx": config["stats_period_idx"],
                "goals": config["goals"],
            },
            f,
            indent=4,
        )


def load_words():
    try:
        with open(WORDS_PATH, "r") as f:
            quotes = json.load(f)
            if isinstance(quotes, dict) and quotes:
                return quotes
    except Exception:
        pass
    return {k: v.copy() for k, v in DEFAULT_QUOTES.items()}


def load_stats():
    ensure_data_dir()
    stats = []
    if os.path.exists(STATS_PATH):
        try:
            with open(STATS_PATH, "r") as f:
                stats = json.load(f)
        except Exception:
            pass
    return stats


def save_stat(wpm, list_name, accuracy):
    stats = load_stats()
    stats.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "list_name": list_name,
            "wpm": wpm,
            "accuracy": accuracy,
        }
    )

    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=4)


def reset_stats():
    write_json(STATS_PATH, [])


def restore_default_config():
    global config
    config.clear()
    config.update(
        {
            "list_idx": DEFAULT_CONFIG["list_idx"],
            "pacer": DEFAULT_CONFIG["pacer"],
            "pacer_enabled": DEFAULT_CONFIG["pacer_enabled"],
            "theme_idx": DEFAULT_CONFIG["theme_idx"],
            "pacer_marker_idx": DEFAULT_CONFIG["pacer_marker_idx"],
            "caret_marker_idx": DEFAULT_CONFIG["caret_marker_idx"],
            "stats_period_idx": DEFAULT_CONFIG["stats_period_idx"],
            "goals": DEFAULT_CONFIG["goals"].copy(),
        }
    )
    save_config()


def parse_stat_time(entry):
    return datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")


def period_start(period, now=None):
    now = now or datetime.now()
    if period == "daily":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "weekly":
        start = now - timedelta(days=now.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "monthly":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def filter_stats_by_period(stats, period):
    if period == "all":
        return stats
    start = period_start(period)
    return [s for s in stats if parse_stat_time(s) >= start]


def summarize_stats(stats):
    if not stats:
        return {"avg": 0, "best": 0, "avg_acc": 0}
    wpms = [s["wpm"] for s in stats]
    accs = [s.get("accuracy", 100) for s in stats]
    return {
        "avg": round(mean(wpms)),
        "best": max(wpms),
        "avg_acc": round(mean(accs)),
    }


def clamp_config_indices():
    changed = False
    list_names_len = len(load_words())
    if config["list_idx"] >= list_names_len:
        config["list_idx"] = 0
        changed = True
    if config["stats_period_idx"] >= len(STATS_PERIODS):
        config["stats_period_idx"] = 0
        changed = True
    if config.get("theme_idx", 0) >= len(THEME_NAMES):
        config["theme_idx"] = DEFAULT_CONFIG["theme_idx"]
        changed = True
    if config.get("pacer_marker_idx", 0) >= len(MARKER_NAMES):
        config["pacer_marker_idx"] = DEFAULT_CONFIG["pacer_marker_idx"]
        changed = True
    if config.get("caret_marker_idx", 0) >= len(MARKER_NAMES):
        config["caret_marker_idx"] = DEFAULT_CONFIG["caret_marker_idx"]
        changed = True
    if changed:
        save_config()


ensure_default_data()
config = load_config()
clamp_config_indices()

# --- PACER ---


def effective_pacer_wpm():
    if not config.get("pacer_enabled", False):
        return 0
    return max(0, config.get("pacer", 0))


# --- COLORS ---
ATTR_UNTYPED = 0
ATTR_CORRECT = 0
ATTR_ERROR = 0
ATTR_HUD = 0
ATTR_TITLE = 0
ATTR_PACER = 0
ATTR_SELECTED = 0
ATTR_CARET = 0
ATTR_EXTRA = 0


def marker_attr(pair_num, marker_idx, extra=0):
    name = MARKER_NAMES[marker_idx % len(MARKER_NAMES)]
    base = curses.color_pair(pair_num) | extra
    if name == "underline":
        return base | curses.A_UNDERLINE
    if name == "block":
        return base | curses.A_REVERSE
    if name == "bright":
        return base | curses.A_BOLD
    if name == "dim":
        return base | curses.A_REVERSE | curses.A_DIM
    return base | curses.A_UNDERLINE


def caret_display_char(ch):
    marker_idx = config.get("caret_marker_idx", DEFAULT_CONFIG["caret_marker_idx"])
    if marker_idx >= len(MARKER_NAMES):
        marker_idx = DEFAULT_CONFIG["caret_marker_idx"]
    if MARKER_NAMES[marker_idx] == "underline" and ch == " ":
        return "_"
    return ch


def hex_to_c1000(hex_color):
    hex_color = hex_color.lstrip("#")
    return (
        int(int(hex_color[0:2], 16) * 1000 / 255),
        int(int(hex_color[2:4], 16) * 1000 / 255),
        int(int(hex_color[4:6], 16) * 1000 / 255),
    )


def register_rgb_color(slot, hex_color):
    r, g, b = hex_to_c1000(hex_color)
    try:
        if hasattr(curses, "init_extended_color"):
            curses.init_extended_color(slot, r, g, b)
            return True
        if curses.can_change_color() and slot < curses.COLORS:
            curses.init_color(slot, r, g, b)
            return True
    except curses.error:
        pass
    return False


def init_theme_pair(pair_num, fg, bg):
    try:
        if hasattr(curses, "init_extended_pair"):
            curses.init_extended_pair(pair_num, fg, bg)
        else:
            curses.init_pair(pair_num, fg, bg)
        return True
    except curses.error:
        return False


def register_catppuccin_colors(colors):
    if not curses.can_change_color():
        return False
    for name, slot in COLOR_SLOTS.items():
        if name not in colors:
            continue
        if not register_rgb_color(slot, colors[name]):
            return False
    return True


def apply_catppuccin_pairs(theme_name, rgb_mode):
    if rgb_mode:
        base = COLOR_SLOTS["base"]
        surface = COLOR_SLOTS["surface"]
        init_theme_pair(1, COLOR_SLOTS["text"], base)
        init_theme_pair(2, COLOR_SLOTS["subtext"], base)
        init_theme_pair(3, COLOR_SLOTS["green"], base)
        init_theme_pair(4, COLOR_SLOTS["red"], base)
        init_theme_pair(5, COLOR_SLOTS["pink"], base)
        init_theme_pair(6, COLOR_SLOTS["yellow"], surface)
        init_theme_pair(7, COLOR_SLOTS["blue"], base)
        init_theme_pair(8, COLOR_SLOTS["mauve"], base)
        return

    fb = THEME_FALLBACK[theme_name]
    base = fb["base"]
    init_theme_pair(1, fb["text"], base)
    init_theme_pair(2, fb["subtext"], base)
    init_theme_pair(3, fb["green"], base)
    init_theme_pair(4, fb["red"], base)
    init_theme_pair(5, fb["pink"], base)
    init_theme_pair(6, fb["yellow"], fb["surface"])
    init_theme_pair(7, fb["blue"], base)
    init_theme_pair(8, fb["mauve"], base)


def init_colors(stdscr=None):
    global ATTR_UNTYPED, ATTR_CORRECT, ATTR_ERROR, ATTR_HUD, ATTR_TITLE, ATTR_PACER, ATTR_SELECTED, ATTR_CARET, ATTR_EXTRA
    theme_idx = config.get("theme_idx", DEFAULT_CONFIG["theme_idx"])
    if theme_idx >= len(THEME_NAMES):
        theme_idx = DEFAULT_CONFIG["theme_idx"]
    pacer_marker_idx = config.get("pacer_marker_idx", DEFAULT_CONFIG["pacer_marker_idx"])
    caret_marker_idx = config.get("caret_marker_idx", DEFAULT_CONFIG["caret_marker_idx"])
    if pacer_marker_idx >= len(MARKER_NAMES):
        pacer_marker_idx = DEFAULT_CONFIG["pacer_marker_idx"]
    if caret_marker_idx >= len(MARKER_NAMES):
        caret_marker_idx = DEFAULT_CONFIG["caret_marker_idx"]

    theme_name = THEME_NAMES[theme_idx]
    colors = CATPPUCCIN[theme_name]

    curses.start_color()
    curses.use_default_colors()

    rgb_mode = register_catppuccin_colors(colors)
    apply_catppuccin_pairs(theme_name, rgb_mode)

    ATTR_UNTYPED = curses.color_pair(1)
    ATTR_CORRECT = curses.color_pair(3) | curses.A_BOLD
    ATTR_ERROR = curses.color_pair(4) | curses.A_BOLD
    ATTR_HUD = curses.color_pair(2)
    if not rgb_mode:
        ATTR_HUD |= curses.A_DIM
    ATTR_TITLE = curses.color_pair(1) | curses.A_BOLD
    ATTR_PACER = marker_attr(6, pacer_marker_idx, curses.A_BOLD)
    ATTR_SELECTED = curses.color_pair(8) | curses.A_BOLD
    ATTR_CARET = marker_attr(7, caret_marker_idx)
    ATTR_EXTRA = curses.color_pair(5) | curses.A_BOLD

    if stdscr is not None:
        stdscr.bkgd(" ", curses.color_pair(1))


def safe_addstr(stdscr, y, x, text, attr=0):
    max_y, max_x = stdscr.getmaxyx()
    if y < 0 or y >= max_y or x >= max_x:
        return
    try:
        stdscr.addstr(y, x, text[: max_x - x - 1], attr)
    except curses.error:
        pass


def read_key(stdscr):
    try:
        return stdscr.getkey()
    except KeyboardInterrupt:
        return "CTRL_C"
    except Exception:
        return None


def is_enter(key):
    return key is not None and len(key) == 1 and ord(key) in (10, 13)


def is_ctrl_c(key):
    return key == "CTRL_C" or (key is not None and len(key) == 1 and ord(key) == 3)


def is_tab(key):
    return key is not None and len(key) == 1 and ord(key) == 9


def is_escape(key):
    return key is not None and len(key) == 1 and ord(key) == 27


def is_backspace(key):
    return key in ("KEY_BACKSPACE", "\b", "\x7f")


def is_up(key):
    return key == "KEY_UP"


def is_down(key):
    return key == "KEY_DOWN"


def menu_next(key, selected, count):
    if is_tab(key) or is_down(key):
        return (selected + 1) % count
    if is_up(key):
        return (selected - 1) % count
    return None


def draw_menu_line(stdscr, row, text, selected):
    prefix_sel = "> "
    prefix = "  "
    attr = ATTR_SELECTED if selected else ATTR_HUD
    safe_addstr(stdscr, row, 4, f"{prefix_sel if selected else prefix}{text}", attr)


def menu_footer(stdscr):
    max_y, _ = stdscr.getmaxyx()
    safe_addstr(stdscr, max_y - 2, 4, "tab / arrows · enter · esc", ATTR_HUD)


# --- LAYOUT ---
def layout_words(target, max_width):
    """Pack target text into lines without splitting words."""
    if max_width < 1:
        max_width = 1

    tokens = []
    i = 0
    n = len(target)
    while i < n:
        if target[i] == " ":
            tokens.append((i, i + 1))
            i += 1
        else:
            start = i
            while i < n and target[i] != " ":
                i += 1
            tokens.append((start, i))

    lines = []
    current_line = []
    current_len = 0

    for start, end in tokens:
        token_len = end - start
        if current_line and current_len + token_len > max_width:
            lines.append(current_line)
            current_line = []
            current_len = 0
        current_line.append((start, end))
        current_len += token_len

    if current_line:
        lines.append(current_line)

    return lines if lines else [[]]


def line_width(line):
    return sum(end - start for start, end in line)


def pos_to_line(pos, lines):
    for li, line in enumerate(lines):
        for start, end in line:
            if pos < end:
                return li
    return max(0, len(lines) - 1)


def get_word_spans(target):
    spans = []
    i = 0
    while i < len(target):
        if target[i] == " ":
            i += 1
            continue
        start = i
        while i < len(target) and target[i] != " ":
            i += 1
        spans.append((start, i))
    return spans


def word_has_error(word_start, word_end, current, target):
    if len(current) <= word_start:
        return False
    for i in range(word_start, min(word_end, len(current))):
        if current[i] != target[i]:
            return True
    return False


def get_active_word_span(pos, word_spans, target):
    for i, (start, end) in enumerate(word_spans):
        if start <= pos < end:
            return start, end
        if pos == end and pos < len(target) and target[pos] == " ":
            return start, end
    return word_spans[-1] if word_spans else (0, 0)


def at_space_boundary(pos, target):
    return pos < len(target) and target[pos] == " "


def can_type_char(key, pos, target):
    if pos >= len(target):
        return False
    if at_space_boundary(pos, target):
        return key == " " or (len(key) == 1 and ord(key) > 32)
    if key == " ":
        return False
    return len(key) == 1 and ord(key) > 32


def calc_accuracy(current, target):
    if not current:
        return 100
    correct = sum(1 for i, ch in enumerate(current) if i < len(target) and ch == target[i])
    return round(correct / len(current) * 100)


def calc_wpm(char_count, time_elapsed):
    if time_elapsed <= 0:
        return 0
    return round((char_count / 5) / (time_elapsed / 60))


def wrap_text_lines(text, max_width):
    if max_width < 1:
        max_width = 1
    lines = []
    for layout_line in layout_words(text, max_width):
        line = "".join(text[start:end] for start, end in layout_line)
        if line:
            lines.append(line)
    return lines or [""]


def pick_quote(word_lists, list_names, avoid=None):
    list_name = list_names[config["list_idx"]]
    raw_content = word_lists.get(list_name, ["error loading words"])
    if isinstance(raw_content, list):
        choices = raw_content or ["no quotes available"]
        if avoid and len(choices) > 1:
            choices = [quote for quote in choices if quote != avoid] or raw_content
        target_text = random.choice(choices)
    else:
        target_text = str(raw_content)
    return list_name, target_text


def get_error_word_indices(current, target, word_spans, overflow, committed_overflow):
    indices = set()
    pos = len(current)
    for start, end in word_spans:
        has_error = word_has_error(start, end, current, target)
        has_overflow = (overflow and pos == end and at_space_boundary(pos, target)) or end in committed_overflow
        if not has_error and not has_overflow:
            continue
        for i in range(start, end):
            indices.add(i)
    return indices


def char_display_attr(i, target, current, error_word_indices, pacer_idx=-1, overflow=None):
    overflow = overflow or []
    target_char = target[i]
    underline = curses.A_UNDERLINE if i in error_word_indices else 0
    pos = len(current)

    if i == pos and not (overflow and at_space_boundary(pos, target)):
        return caret_display_char(target_char), ATTR_CARET

    if i == pacer_idx and pacer_idx >= 0 and i != pos:
        return target_char, ATTR_PACER

    if i < len(current):
        if current[i] == target_char:
            return target_char, ATTR_CORRECT | underline
        return target_char, ATTR_ERROR | underline

    return target_char, ATTR_UNTYPED


def overflow_char_count(overflow, committed_overflow):
    return len(overflow) + sum(len(chars) for chars in committed_overflow.values())


# --- RENDERING ---
def render_race(stdscr, target, current, overflow, committed_overflow, wpm, time_elapsed, has_started, pacer_wpm, list_name, complete=False):
    max_y, max_x = stdscr.getmaxyx()
    text_width = max(10, max_x - 4)

    acc = calc_accuracy(current, target)
    if has_started:
        hud = f"wpm {wpm}  ·  time {int(time_elapsed)}s  ·  acc {acc}%"
    else:
        hud = "wpm 0  ·  time 0s  ·  acc 100%"
    safe_addstr(stdscr, 0, 0, hud[: max_x - 1], ATTR_HUD)
    if complete:
        safe_addstr(stdscr, 1, 0, " " * max(0, max_x - 1), ATTR_HUD)
    else:
        safe_addstr(stdscr, 1, 0, f"quotes: {list_name}  ·  tab new quote"[: max_x - 1], ATTR_HUD)

    lines = layout_words(target, text_width)
    active_line = pos_to_line(len(current), lines)
    start_line = max(0, active_line - 1)
    end_line = min(len(lines), start_line + 3)

    pacer_idx = -1
    if pacer_wpm > 0 and has_started:
        pacer_idx = int((pacer_wpm * 5 / 60) * time_elapsed)

    text_start_row = max(3, (max_y - 6) // 2)
    word_spans = get_word_spans(target)
    error_word_indices = get_error_word_indices(current, target, word_spans, overflow, committed_overflow)
    pos = len(current)

    for view_idx, line_idx in enumerate(range(start_line, end_line)):
        row = text_start_row + view_idx
        if row >= max_y - 1:
            break

        line = lines[line_idx]
        width = line_width(line)
        col_offset = 2 + max(0, (text_width - width) // 2)
        col = col_offset

        for start, end in line:
            for i in range(start, end):
                if col >= max_x - 1:
                    break

                if i in committed_overflow and len(current) > i:
                    for extra in committed_overflow[i]:
                        if col >= max_x - 1:
                            break
                        try:
                            stdscr.addch(row, col, extra, ATTR_EXTRA | curses.A_UNDERLINE)
                        except curses.error:
                            pass
                        col += 1

                if i == pos and overflow and at_space_boundary(pos, target):
                    for extra in overflow:
                        if col >= max_x - 1:
                            break
                        try:
                            stdscr.addch(row, col, extra, ATTR_EXTRA | curses.A_UNDERLINE)
                        except curses.error:
                            pass
                        col += 1
                    if col < max_x - 1:
                        try:
                            stdscr.addch(row, col, caret_display_char(" "), ATTR_CARET)
                        except curses.error:
                            pass
                        col += 1
                    if col < max_x - 1:
                        try:
                            stdscr.addch(row, col, target[i], ATTR_UNTYPED)
                        except curses.error:
                            pass
                        col += 1
                    continue

                display_char, attr = char_display_attr(
                    i, target, current, error_word_indices, pacer_idx, overflow
                )

                try:
                    stdscr.addch(row, col, display_char, attr)
                except curses.error:
                    pass

                col += 1

    word_start, word_end = get_active_word_span(pos, word_spans, target)
    word_box_row = max_y - 2
    render_current_word_box(
        stdscr,
        target,
        current,
        overflow,
        word_start,
        word_end,
        word_box_row,
        max_x,
        max_y,
        error_word_indices,
        pacer_idx,
    )


def render_current_word_box(
    stdscr,
    target,
    current,
    overflow,
    word_start,
    word_end,
    row,
    max_x,
    max_y,
    error_word_indices,
    pacer_idx=-1,
):
    word_len = word_end - word_start
    if word_len == 0:
        return

    pos = len(current)
    show_overflow = overflow and pos == word_end and at_space_boundary(pos, target)
    extra_count = len(overflow) if show_overflow else 0
    caret_slot = 1 if show_overflow else 0
    inner_width = word_len + extra_count + caret_slot + 2
    x = max(2, (max_x - inner_width) // 2)

    safe_addstr(stdscr, row, x, "[", ATTR_HUD)
    col = x + 1
    for i in range(word_len):
        idx = word_start + i
        display, attr = char_display_attr(
            idx, target, current, error_word_indices, pacer_idx, overflow
        )
        try:
            stdscr.addch(row, col, display, attr)
        except curses.error:
            pass
        col += 1

    if show_overflow:
        for extra in overflow:
            try:
                stdscr.addch(row, col, extra, ATTR_EXTRA | curses.A_UNDERLINE)
            except curses.error:
                pass
            col += 1
        if col < max_x - 1:
            try:
                stdscr.addch(row, col, caret_display_char(" "), ATTR_CARET)
            except curses.error:
                pass

    safe_addstr(stdscr, row, x + inner_width - 1, "]", ATTR_HUD)


# --- SCREENS ---
def prompt_number(stdscr, label, current, min_val=0, max_val=999):
    digits = str(current) if current else ""

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        safe_addstr(stdscr, 2, 2, label, ATTR_TITLE)
        value = digits if digits else "0"
        safe_addstr(stdscr, 4, 2, f"{label}: {value} wpm", ATTR_SELECTED)
        safe_addstr(stdscr, 6, 2, "enter confirm  ·  esc cancel", ATTR_HUD)
        stdscr.refresh()

        key = read_key(stdscr)
        if is_ctrl_c(key):
            return None
        if is_escape(key):
            return None
        if is_enter(key):
            val = int(digits) if digits else 0
            return max(min_val, min(max_val, val))
        if is_backspace(key):
            digits = digits[:-1]
        elif key is not None and len(key) == 1 and key.isdigit():
            candidate = digits + key
            if int(candidate) <= max_val:
                digits = candidate


def prompt_confirm(stdscr, title, detail):
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        safe_addstr(stdscr, 2, 2, title, ATTR_TITLE)
        if detail:
            safe_addstr(stdscr, 4, 2, detail[: max_x - 4], ATTR_HUD)
        safe_addstr(stdscr, max_y - 4, 4, "y confirm  ·  esc cancel", ATTR_HUD)
        stdscr.refresh()

        key = read_key(stdscr)
        if is_ctrl_c(key) or is_escape(key):
            return False
        if key is not None and key.lower() == "y":
            return True


def danger_zone_screen(stdscr):
    options = ["restore account to default", "reset stats"]
    selected = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        safe_addstr(stdscr, 2, max(0, (max_x - len("danger zone")) // 2), "danger zone", ATTR_ERROR)
        safe_addstr(stdscr, 4, 4, "destructive actions cannot be undone", ATTR_HUD)
        draw_menu_line(stdscr, 6, options[0], selected == 0)
        draw_menu_line(stdscr, 7, options[1], selected == 1)
        safe_addstr(stdscr, max_y - 3, 4, "enter select  ·  esc back", ATTR_HUD)
        menu_footer(stdscr)
        stdscr.refresh()

        key = read_key(stdscr)
        if is_ctrl_c(key) or is_escape(key):
            return

        nav = menu_next(key, selected, len(options))
        if nav is not None:
            selected = nav
            continue

        if not is_enter(key):
            continue

        if selected == 0:
            if prompt_confirm(
                stdscr,
                "restore account to default?",
                "resets preferences, theme, pacer, and list selection",
            ):
                restore_default_config()
                clamp_config_indices()
                init_colors(stdscr)
        elif selected == 1:
            if prompt_confirm(stdscr, "reset stats?", "clears all saved race history"):
                reset_stats()


def settings_screen(stdscr, word_lists):
    danger_zone_screen(stdscr)


def draw_home_stats(stdscr, start_y, period, max_x, max_y):
    filtered = filter_stats_by_period(load_stats(), period)
    summary = summarize_stats(filtered)
    y = start_y

    if not filtered:
        safe_addstr(stdscr, y, 4, "no races in this period", ATTR_HUD)
        return y + 1

    line = (
        f"max {summary['best']} wpm  ·  "
        f"avg {summary['avg']} wpm  ·  "
        f"acc {summary['avg_acc']}%"
    )
    safe_addstr(stdscr, y, 4, line[: max_x - 5], ATTR_HUD)
    return y + 1


def draw_style_preview(stdscr, start_row, max_x):
    sample = "the quick brown fox"
    caret_pos = sample.index("q")
    pacer_pos = sample.index("b", caret_pos + 1)
    x = max(2, (max_x - len(sample)) // 2)

    safe_addstr(stdscr, start_row, x, sample, ATTR_UNTYPED)
    try:
        stdscr.addch(start_row, x + caret_pos, sample[caret_pos], ATTR_CARET)
        stdscr.addch(start_row, x + pacer_pos, sample[pacer_pos], ATTR_PACER)
    except curses.error:
        pass

    legend = f"'{sample[caret_pos]}' user  ·  '{sample[pacer_pos]}' pacer"
    safe_addstr(stdscr, start_row + 2, max(2, (max_x - len(legend)) // 2), legend, ATTR_HUD)


def style_screen(stdscr):
    options = ["theme", "pacer", "pacer wpm", "pacer marker", "caret marker"]
    selected = 0
    pacer_idx = 1
    pacer_wpm_idx = 2

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        theme = THEME_NAMES[config["theme_idx"]]
        pacer_on = "on" if config.get("pacer_enabled", False) else "off"
        pacer_wpm = config.get("pacer", 0)
        pacer_wpm_label = f"{pacer_wpm} wpm" if pacer_wpm else "not set"
        pacer_marker = MARKER_NAMES[config["pacer_marker_idx"]]
        caret_marker = MARKER_NAMES[config["caret_marker_idx"]]

        safe_addstr(stdscr, 2, max(0, (max_x - len("style")) // 2), "style", ATTR_TITLE)
        draw_menu_line(stdscr, 5, f"theme: {theme}", selected == 0)
        draw_menu_line(stdscr, 6, f"pacer: {pacer_on}", selected == pacer_idx)
        draw_menu_line(stdscr, 7, f"pacer wpm: {pacer_wpm_label}", selected == pacer_wpm_idx)
        draw_menu_line(stdscr, 8, f"pacer marker: {pacer_marker}", selected == 3)
        draw_menu_line(stdscr, 9, f"caret marker: {caret_marker}", selected == 4)

        draw_style_preview(stdscr, 12, max_x)
        safe_addstr(stdscr, max_y - 3, 4, "enter cycle / edit  ·  esc back", ATTR_HUD)
        menu_footer(stdscr)
        stdscr.refresh()

        key = read_key(stdscr)
        if is_ctrl_c(key):
            return
        if is_escape(key):
            return

        nav = menu_next(key, selected, len(options))
        if nav is not None:
            selected = nav
            continue

        if not is_enter(key):
            continue

        if selected == 0:
            config["theme_idx"] = (config["theme_idx"] + 1) % len(THEME_NAMES)
            save_config()
            init_colors(stdscr)
        elif selected == pacer_idx:
            config["pacer_enabled"] = not config.get("pacer_enabled", False)
            save_config()
        elif selected == pacer_wpm_idx:
            result = prompt_number(stdscr, "pacer wpm", config["pacer"])
            if result is not None:
                config["pacer"] = result
                save_config()
            init_colors(stdscr)
        elif selected == 3:
            config["pacer_marker_idx"] = (config["pacer_marker_idx"] + 1) % len(MARKER_NAMES)
            save_config()
            init_colors(stdscr)
        elif selected == 4:
            config["caret_marker_idx"] = (config["caret_marker_idx"] + 1) % len(MARKER_NAMES)
            save_config()
            init_colors(stdscr)
        continue


def home_screen(stdscr, word_lists):
    options = ["race", "list", "style", "settings", "stats"]
    selected = 0
    style_idx = 2
    settings_idx = 3
    stats_idx = 4

    while True:
        word_lists.clear()
        word_lists.update(load_words())
        list_names = list(word_lists.keys())
        if config["list_idx"] >= len(list_names):
            config["list_idx"] = 0
            save_config()

        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        list_name = list_names[config["list_idx"]] if list_names else "none"
        period = STATS_PERIODS[config["stats_period_idx"]]

        safe_addstr(stdscr, 2, max(0, (max_x - len("vital typing")) // 2), "vital typing", ATTR_TITLE)

        draw_menu_line(stdscr, 5, "race", selected == 0)
        draw_menu_line(stdscr, 6, f"quotes: {list_name}", selected == 1)
        draw_menu_line(stdscr, 7, "style", selected == style_idx)
        draw_menu_line(stdscr, 8, "settings", selected == settings_idx)
        draw_menu_line(stdscr, 9, f"stats: {period}", selected == stats_idx)

        draw_home_stats(stdscr, 11, period, max_x, max_y)

        if selected == stats_idx:
            safe_addstr(stdscr, max_y - 3, 4, "enter change period", ATTR_HUD)

        menu_footer(stdscr)
        stdscr.refresh()

        key = read_key(stdscr)
        if is_ctrl_c(key):
            return "quit"
        if is_escape(key):
            return "quit"

        if selected == stats_idx and is_enter(key):
            config["stats_period_idx"] = (config["stats_period_idx"] + 1) % len(STATS_PERIODS)
            save_config()
            continue

        nav = menu_next(key, selected, len(options))
        if nav is not None:
            selected = nav
            continue

        if not is_enter(key):
            continue

        if selected == 0:
            return "race"
        if selected == 1:
            config["list_idx"] = (config["list_idx"] + 1) % len(list_names)
            save_config()
        elif selected == style_idx:
            style_screen(stdscr)
            init_colors(stdscr)
        elif selected == settings_idx:
            settings_screen(stdscr, word_lists)
            init_colors(stdscr)


def results_screen(stdscr, race_result):
    options = ["new race", "home"]
    selected = 0
    target = race_result["target"]
    current = race_result["current"]
    committed_overflow = race_result.get("committed_overflow", {})
    wpm = race_result["wpm"]
    accuracy = race_result["accuracy"]

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        render_race(
            stdscr,
            target,
            current,
            [],
            committed_overflow,
            wpm,
            race_result["time_elapsed"],
            True,
            0,
            race_result["list_name"],
            complete=True,
        )
        safe_addstr(
            stdscr,
            0,
            0,
            f"race complete  ·  {wpm} wpm  ·  acc {accuracy}%"[: max_x - 1],
            ATTR_TITLE,
        )

        menu_y = max_y - 4
        draw_menu_line(stdscr, menu_y, options[0], selected == 0)
        draw_menu_line(stdscr, menu_y + 1, options[1], selected == 1)
        menu_footer(stdscr)
        stdscr.refresh()

        key = read_key(stdscr)
        if is_ctrl_c(key):
            return "quit"
        if is_escape(key):
            return "home"

        nav = menu_next(key, selected, len(options))
        if nav is not None:
            selected = nav
            continue

        if is_enter(key):
            return "race" if selected == 0 else "home"


def restore_blocking_input(stdscr):
    stdscr.nodelay(False)
    stdscr.timeout(-1)


def run_quote_race(stdscr, word_lists):
    list_names = list(word_lists.keys())
    if config["list_idx"] >= len(list_names):
        config["list_idx"] = 0
        save_config()

    list_name, target_text = pick_quote(word_lists, list_names)
    current_text = []
    overflow = []
    committed_overflow = {}
    has_started = False
    start_time = 0
    word_spans = get_word_spans(target_text)
    keypresses = 0
    correct_keypresses = 0
    stdscr.nodelay(True)

    def finish_race():
        restore_blocking_input(stdscr)
        time_elapsed = max(time.time() - start_time, 0.1) if has_started else 0.0
        wpm = calc_wpm(len(current_text) + overflow_char_count(overflow, committed_overflow), time_elapsed)
        accuracy = round(correct_keypresses / keypresses * 100) if keypresses else 100
        return {
            "wpm": wpm,
            "accuracy": accuracy,
            "list_name": list_name,
            "target": target_text,
            "current": list(current_text),
            "committed_overflow": dict(committed_overflow),
            "time_elapsed": time_elapsed,
        }

    def load_new_quote():
        nonlocal target_text, current_text, word_spans, overflow, committed_overflow
        nonlocal has_started, start_time, keypresses, correct_keypresses
        _, target_text = pick_quote(word_lists, list_names, avoid=target_text)
        current_text = []
        overflow = []
        committed_overflow = {}
        word_spans = get_word_spans(target_text)
        has_started = False
        start_time = 0
        keypresses = 0
        correct_keypresses = 0

    while True:
        if has_started:
            time_elapsed = max(time.time() - start_time, 0.1)
        else:
            time_elapsed = 0.0

        wpm = calc_wpm(len(current_text) + overflow_char_count(overflow, committed_overflow), time_elapsed)

        stdscr.clear()
        render_race(
            stdscr,
            target_text,
            current_text,
            overflow,
            committed_overflow,
            wpm,
            time_elapsed,
            has_started,
            effective_pacer_wpm(),
            list_name,
        )
        stdscr.refresh()

        if len(current_text) == len(target_text) and has_started:
            return "completed", finish_race()

        key = read_key(stdscr)
        if key is None:
            time.sleep(0.01)
            continue

        if is_ctrl_c(key):
            restore_blocking_input(stdscr)
            return "quit", None
        if is_escape(key):
            restore_blocking_input(stdscr)
            return "home", None
        if is_tab(key):
            load_new_quote()
            continue
        if is_enter(key):
            continue

        if is_backspace(key):
            if overflow:
                overflow.pop()
            elif current_text:
                removed_idx = len(current_text) - 1
                current_text.pop()
                if removed_idx in committed_overflow:
                    overflow.extend(committed_overflow.pop(removed_idx))
            if has_started:
                keypresses += 1
            continue

        if len(key) != 1 or ord(key) < 32:
            continue

        pos = len(current_text)
        if pos >= len(target_text):
            continue
        if not can_type_char(key, pos, target_text):
            continue

        if not has_started:
            has_started = True
            start_time = time.time()

        if at_space_boundary(pos, target_text) and key != " ":
            overflow.append(key)
            keypresses += 1
            continue

        if at_space_boundary(pos, target_text) and key == " " and overflow:
            committed_overflow[pos] = list(overflow)
            overflow.clear()

        current_text.append(key)
        keypresses += 1
        if key == target_text[pos]:
            correct_keypresses += 1

        if len(current_text) == len(target_text):
            return "completed", finish_race()


def main(stdscr):
    if hasattr(curses, "set_escdelay"):
        curses.set_escdelay(25)
    init_colors(stdscr)
    stdscr.keypad(True)
    word_lists = load_words()

    while True:
        choice = home_screen(stdscr, word_lists)
        if choice == "quit":
            break
        if choice != "race":
            continue

        while True:
            status, race_result = run_quote_race(stdscr, word_lists)

            if status == "quit":
                return
            if status == "home":
                break

            if status == "completed":
                save_stat(race_result["wpm"], race_result["list_name"], race_result["accuracy"])
                action = results_screen(stdscr, race_result)
                if action == "quit":
                    return
                if action == "home":
                    break
                # action == "race" -> loop again
            else:
                break


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
