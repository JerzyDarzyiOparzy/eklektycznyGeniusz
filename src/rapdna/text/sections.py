"""Split Genius lyrics into sections ([Zwrotka 1: X], [Refren], [Verse 2: X & Y]) and attribute performers.

The header patterns are Polish and English, as they appear on Polish Genius pages.
"""
import re
from dataclasses import dataclass, field

HEADER_RE = re.compile(r"^\[(?P<body>[^\]]+)\]$")
SKIP_HEADERS = re.compile(r"^(tekst piosenki|lyrics)\b", re.I)
PERFORMER_SPLIT = re.compile(r"\s*(?:,|&|\+|\bi\b|\boraz\b|\band\b|\bx\b|\bfeat\.?|\bft\.?)\s*", re.I)
ADLIB_RE = re.compile(r"\([^)]*\)")
# Genius footer, sometimes glued to the last line without a newline („…nicTekst i adnotacje na Rap Genius Polska”)
FOOTER_RE = re.compile(r"\[?\s*Tekst(?: i adnotacje)?\s*(?:na|-)\s*(?:Rap )?Genius Polska\s*\]?", re.I)
# headers that name a part of the song, not a performer: „[Utwór 1: TRAWA]”, „[Część II]”
TITLE_HEADERS = re.compile(r"^\s*(utw[oó]r|cz[eę][sś][cć]|part|track)\b", re.I)
# „Obaj”, „Wszyscy” (both, everyone) mean the performers already named, together, not a separate person
GROUP_WORDS = {"obaj", "oboje", "obie", "wszyscy", "razem", "both", "all"}

SECTION_TYPES = [
    ("prechorus", r"przed[- ]?refren|pre[- ]?(chorus|hook)"),
    ("postchorus", r"po[- ]?refren|post[- ]?(chorus|hook)"),
    ("verse", r"zwrotka|verse|wers"),
    ("chorus", r"refren|chorus|hook"),
    ("intro", r"intro|wst[eę]p"),
    ("outro", r"outro|zako[nń]czenie"),
    ("bridge", r"bridge|most(ek)?|przej[sś]cie|interlude"),
    ("skit", r"skit|sample|interlude"),
]


@dataclass
class Section:
    type: str
    header: str
    performers: list[str]
    lines: list[str] = field(default_factory=list)
    is_dup: bool = False  # repeats an earlier section with identical text (e.g. a chorus)

    @property
    def text_key(self) -> str:
        return "\n".join(norm_line(ln) for ln in self.lines)


def section_type(label: str) -> str:
    label = label.lower()
    for name, pattern in SECTION_TYPES:
        if re.match(rf"\s*({pattern})\b", label):
            return name
    return "other"


def parse_header(body: str) -> tuple[str, list[str]]:
    label, _, who = body.partition(":")
    if TITLE_HEADERS.match(label):
        return "other", []
    if not who and re.fullmatch(r"\s*\?+\s*", label):  # „[?]”: unknown performer
        return "other", ["?"]
    performers = [p.strip() for p in PERFORMER_SPLIT.split(who) if p.strip()] if who else []
    performers = [re.sub(r"\s+x\d+$", "", p) for p in performers]  # vocal doubles: „Oxon x2”
    return section_type(label), [p for p in performers if p.casefold() not in GROUP_WORDS]


def norm_line(line: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", line.lower())).strip()


def strip_adlibs(line: str) -> str:
    """Remove ad-libs and backing vocals written in parentheses."""
    return re.sub(r"\s{2,}", " ", ADLIB_RE.sub("", line)).strip()


def parse_sections(text: str, primary: str, featured: list[str], aliases: list[str] = ()) -> list[Section]:
    known = [primary, *aliases, *featured]
    sections: list[Section] = []
    current: Section | None = None
    for raw in text.splitlines():
        line = FOOTER_RE.sub("", raw).strip()
        m = HEADER_RE.match(line)
        if m:
            body = m.group("body").strip()
            if SKIP_HEADERS.match(body):
                continue
            stype, performers = parse_header(body)
            # a bare name without a section type, e.g. „[Quebonafide]” in dialogues and skits
            if not performers and any(same_artist(body, n) for n in known):
                performers = [body]
            current = Section(stype, body, performers)
            sections.append(current)
            continue
        line = strip_adlibs(line)
        if not line:
            continue
        if current is None:  # text before the first header
            current = Section("other", "", [])
            sections.append(current)
        current.lines.append(line)

    # An unsigned section belongs to the primary artist when the song has no guests, or when every guest has a
    # signed part somewhere. If a guest is never named, we cannot tell which unsigned section is theirs, so those
    # sections stay without a performer. „DJ …” guests are ignored: they do scratches and cuts, not verses.
    named = [p for s in sections for p in s.performers]
    vocal_guests = [f for f in featured if not re.match(r"dj\b", f, re.I)]
    if all(any(same_artist(f, p) for p in named) for f in vocal_guests):
        for s in sections:
            if not s.performers:
                s.performers = [primary]

    seen: set[str] = set()
    for s in sections:
        key = s.text_key
        if key in seen:
            s.is_dup = True
        seen.add(key)
    return [s for s in sections if s.lines]


def same_artist(a: str, b: str) -> bool:
    return norm_line(a) == norm_line(b)


def attributed_to(section: Section, artist: str, aliases: list[str] = ()) -> bool:
    """A section counts towards a rapper's statistics only when he performs it alone (under any of his names)."""
    names = {artist, *aliases}
    return bool(section.performers) and all(any(same_artist(p, n) for n in names) for p in section.performers)
