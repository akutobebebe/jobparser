import re

_EXCLUDE = re.compile(
    r"\b(senior|sr\.?|middle|mid[- ]level|intermediate|lead|principal|"
    r"architect|head|team\s*lead|tl)\b",
    re.IGNORECASE,
)

_JUNIOR = re.compile(
    r"\b(junior|jun\.?|trainee|intern|entry[- ]level|graduate|"
    r"початк|без досвіду|no experience)\b",
    re.IGNORECASE,
)


def detect_level(title: str, description: str = "") -> str | None:
    t = title.lower()
    if _EXCLUDE.search(t):
        return "senior" if "senior" in t or "lead" in t or "principal" in t else "middle"
    if _JUNIOR.search(t):
        return "junior"
    combined = (title + " " + description).lower()
    if _EXCLUDE.search(combined):
        return "senior" if re.search(r"\b(senior|lead|principal)\b", combined) else "middle"
    if _JUNIOR.search(combined):
        return "junior"
    return None


def is_junior(title: str) -> bool:
    """
    True якщо вакансія підходить для junior/strong junior/без досвіду.
    Рішення виключно по title — не по опису, щоб уникнути хибного senior.
    """
    if _EXCLUDE.search(title):
        return False
    # Якщо є явний junior-маркер — точно беремо.
    # Якщо маркера нема — вакансія прийшла з exp-звуженого фіду, тому теж беремо.
    return True
