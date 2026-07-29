"""Identity generation — names, usernames and login emails.

The office sheet gives one string per member of staff ("Dr. S. Ravindra"). An
account needs a first name, a last name, a username and a unique email, and two
sheets a term apart must resolve to the SAME account rather than a second copy.
Everything needed for that lives here so the rules stay in one place.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Set

# Titles are stripped before a name is split, but kept: "dr.s.ravindra" is one
# of the username forms the institution uses.
TITLES = {
    "dr", "prof", "mr", "mrs", "ms", "miss", "smt", "sri", "shri", "sh",
    "er", "capt", "lt", "rev", "adv", "mx",
}

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_NAME_NOISE = re.compile(r"[^A-Za-z\s.]")


@dataclass
class PersonName:
    title: Optional[str]
    first_name: str
    last_name: str
    initials: List[str]

    @property
    def display_name(self) -> str:
        parts = [p for p in (self.title, self.first_name, self.last_name) if p]
        return " ".join(parts)


def normalise_person_key(raw: str) -> str:
    """The key two spellings of the same person must share.

    "Dr. S. Ravindra", "S Ravindra" and "Ravindra S." all collapse to
    "ravindra s" — title dropped, punctuation dropped, name parts sorted — so a
    second upload reuses the existing account instead of creating a twin.
    """
    text = _NAME_NOISE.sub(" ", raw or "").lower()
    tokens = [t.strip(". ") for t in text.split() if t.strip(". ")]
    tokens = [t for t in tokens if t not in TITLES]
    return " ".join(sorted(tokens))


def split_person_name(raw: str) -> PersonName:
    """Split an office-written staff name into first/last name.

    Follows the South Indian convention the sheets use: in "S. Ravindra" the
    single letter is the family initial and "Ravindra" is the given name, so the
    account reads first="Ravindra", last="S".
    """
    text = _NAME_NOISE.sub(" ", raw or "").strip()
    tokens = [t for t in re.split(r"[\s.]+", text) if t]

    title: Optional[str] = None
    while tokens and tokens[0].lower().strip(".") in TITLES:
        title = tokens[0].strip(".").capitalize() + "."
        tokens = tokens[1:]

    if not tokens:
        return PersonName(title=title, first_name="Unnamed", last_name="Counsellor", initials=[])

    initials = [t.upper() for t in tokens if len(t) == 1]
    words = [t for t in tokens if len(t) > 1]

    if not words:
        # Nothing but initials — keep them as the name rather than inventing one.
        return PersonName(
            title=title, first_name="".join(initials), last_name="", initials=initials
        )

    if initials:
        # An initial present means the convention is in play: the initial is the
        # family name and every spelled-out word is the given name. This holds
        # however many given-name words there are — "G. Naga Lakshmi" is
        # Naga Lakshmi, of family G, not Naga of family Lakshmi.
        return PersonName(
            title=title,
            first_name=" ".join(w.capitalize() for w in words),
            last_name="".join(initials),
            initials=initials,
        )

    if len(words) == 1:
        return PersonName(title=title, first_name=words[0].capitalize(), last_name="", initials=initials)

    # No initials at all: fall back to the ordinary reading, last word is the
    # surname.
    return PersonName(
        title=title,
        first_name=" ".join(w.capitalize() for w in words[:-1]),
        last_name=words[-1].capitalize(),
        initials=initials,
    )


def slugify(value: str) -> str:
    """Lowercase, dot-separated, safe as the local part of an email address."""
    slug = _NON_ALNUM.sub(".", (value or "").lower()).strip(".")
    return re.sub(r"\.{2,}", ".", slug)


def counsellor_username_candidates(name: PersonName) -> List[str]:
    """The username forms the institution uses, most preferred first.

    "Dr. S. Ravindra" yields "ravindra.s" then "dr.s.ravindra".
    """
    candidates: List[str] = []

    surname_part = slugify(name.last_name) or "".join(i.lower() for i in name.initials)
    given = slugify(name.first_name)
    if given:
        candidates.append(".".join(p for p in (given, surname_part) if p))

    titled = ".".join(
        p for p in (slugify(name.title or ""), "".join(i.lower() for i in name.initials), given) if p
    )
    if titled:
        candidates.append(titled)

    if given and surname_part:
        candidates.append(f"{surname_part}.{given}")

    seen: Set[str] = set()
    ordered: List[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered or ["counsellor"]


def allocate_counsellor_identity(
    name: PersonName, email_domain: str, taken_usernames: Set[str], taken_emails: Set[str]
) -> tuple[str, str]:
    """Pick the first username/email pair that collides with nothing.

    Both must be free together: an account whose username is free but whose
    email is taken would fail the unique constraint at flush time.
    """
    for candidate in counsellor_username_candidates(name):
        email = f"{candidate}@{email_domain}"
        if candidate not in taken_usernames and email not in taken_emails:
            return candidate, email

    base = counsellor_username_candidates(name)[0]
    counter = 2
    while True:
        candidate = f"{base}{counter}"
        email = f"{candidate}@{email_domain}"
        if candidate not in taken_usernames and email not in taken_emails:
            return candidate, email
        counter += 1


def student_username(roll_number: str) -> str:
    """A student's username is their roll number — the identifier they already
    know and the one printed on every office list."""
    return (roll_number or "").strip().upper()


def student_email(roll_number: str, email_domain: str) -> str:
    return f"{student_username(roll_number).lower()}@{email_domain}"
