"""Utilities for parsing emails and removing signature blocks.

This module exposes a single public function, :func:`convert`, that takes the
path of a plaintext email, scores each line using a lightweight spaCy powered
heuristic, and writes a new file with the signature block removed.
"""

from __future__ import annotations

from functools import lru_cache
from html import unescape
from pathlib import Path
from typing import Iterable, Tuple

import re
import string
import numpy as np
import spacy
from mailparser import parse_from_file


DEFAULT_MODEL = "en_core_web_sm"
SIGNATURE_CLOSINGS = {
    "best",
    "best regards",
    "best wishes",
    "thanks",
    "thank you",
    "thanks a lot",
    "regards",
    "kind regards",
    "warm regards",
    "cheers",
    "sincerely",
    "yours truly",
    "yours sincerely",
    "many thanks",
}
SIGNATURE_START_PREFIXES = (
    "sent from my",
    "sent from mail for",
    "sent from outlook for",
    "sent from windows",
    "get outlook for",
    "sent with my",
)
CONTACT_KEYWORDS = {
    "tel",
    "phone",
    "mobile",
    "cell",
    "fax",
    "email",
    "www",
    "http",
    "linkedin",
}
CONTACT_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
CONTACT_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d)")
QUOTE_DELIMITER_KEYWORDS = (
    "original message",
    "forwarded message",
    "forwarded by",
)
EMAIL_HEADER_PREFIXES = (
    "from ",
    "from:",
    "to:",
    "subject:",
    "date:",
    "message-id",
    "in-reply-to",
    "references:",
    "mime-version",
    "content-type",
)


def convert(
    fname: str | Path,
    threshold: float = 0.9,
    model: str = DEFAULT_MODEL,
    /,
) -> str:
    """Parse *fname* and write a ``*_clean`` copy without the signature block.

    Parameters
    ----------
    fname:
        Path to the plaintext email that should be cleaned.
    threshold:
        Upper bound on ``prob(signature | line)`` for a line to be kept.
    model:
        Name of the spaCy language model used for part-of-speech tagging.

    Returns
    -------
    str
        The path of the generated ``*_clean`` file, relative to the current
        working directory.
    """

    input_path = Path(fname).expanduser()
    if not input_path.is_file():
        raise FileNotFoundError(f"Email file not found: {input_path}")

    output_path = _derive_output_path(input_path)

    original_email = _extract_email_body(input_path)
    sentences = _corpus_to_sentences(original_email)

    tagger = _get_tagger(model)
    _write_clean_email(sentences, output_path, tagger, threshold)

    return str(output_path)


def _derive_output_path(input_path: Path) -> Path:
    suffix = input_path.suffix or ""
    stem = input_path.stem
    clean_name = f"{stem}_clean{suffix}"
    return input_path.with_name(clean_name)


def _corpus_to_sentences(corpus: str) -> Iterable[str]:
    return corpus.splitlines(keepends=True)


def _extract_email_body(input_path: Path) -> str:
    raw_text = input_path.read_text(encoding="utf-8")

    body = _parse_body_with_mailparser(input_path)
    if not body.strip():
        body = raw_text

    if re.search(r"<[^>]+>", body):
        body = _html_to_text(body)

    body = body.strip()
    if body.startswith('"') and body.endswith('"'):
        body = body[1:-1].strip()

    return body.replace("\r\n", "\n")


def _parse_body_with_mailparser(input_path: Path) -> str:
    try:
        mail = parse_from_file(str(input_path))
    except Exception:
        return ""

    if not mail:
        return ""

    text_parts = [part for part in (mail.text_plain or []) if part and part.strip()]
    if text_parts:
        return "\n\n".join(text_parts)

    body = mail.body or ""
    if not body and getattr(mail, "body_html", None):
        html_content = mail.body_html
        if isinstance(html_content, (list, tuple)):
            html_content = "\n".join(html_content)
        body = _html_to_text(html_content)

    if "<" in body and ">" in body:
        body = _html_to_text(body)

    return body


def _write_clean_email(
    sentences: Iterable[str],
    output_path: Path,
    tagger,
    threshold: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    signature_mode = False
    recent_delimiter = False

    with output_path.open("w", encoding="utf-8") as new_file:
        for sentence in sentences:
            stripped = sentence.strip()

            if signature_mode:
                if _is_signature_terminator(stripped):
                    signature_mode = False
                    recent_delimiter = _is_quote_delimiter(stripped)
                    new_file.write(sentence)
                    continue

                if _is_email_header_line(stripped):
                    signature_mode = False
                    recent_delimiter = False
                else:
                    if not stripped:
                        continue

                    if _looks_like_contact_info(stripped):
                        continue

                    if _should_consider_probability(stripped):
                        score, token_count = _prob_block(stripped, tagger)
                        if token_count and score >= threshold:
                            continue

                    continue

            if not stripped:
                new_file.write(sentence)
                # Preserve delimiter context for blank lines
                continue

            if _is_signature_start(stripped):
                signature_mode = True
                recent_delimiter = False
                continue

            if _is_quote_delimiter(stripped):
                recent_delimiter = True
                new_file.write(sentence)
                continue

            if _is_quote_header(stripped):
                recent_delimiter = False
                new_file.write(sentence)
                continue

            if recent_delimiter and _looks_like_contact_info(stripped):
                signature_mode = True
                recent_delimiter = False
                continue

            if _is_email_header_line(stripped):
                new_file.write(sentence)
                continue

            recent_delimiter = False
            new_file.write(sentence)


def _prob_block(sentence: str, tagger) -> Tuple[float, int]:
    doc = tagger(sentence)
    if not doc:
        return 0.0, 0

    verb_absence = np.sum(token.pos_ != "VERB" for token in doc)
    return float(verb_absence) / len(doc), len(doc)


@lru_cache(maxsize=None)
def _get_tagger(model_name: str):
    return spacy.load(model_name)


def _should_consider_probability(sentence: str) -> bool:
    length = len(sentence)
    word_count = len(sentence.split())
    return length <= 60 and word_count <= 4


def _is_signature_start(sentence: str) -> bool:
    normalized = _normalize_sentence(sentence)
    if normalized in SIGNATURE_CLOSINGS:
        return True
    return any(normalized.startswith(prefix) for prefix in SIGNATURE_START_PREFIXES)


def _looks_like_contact_info(sentence: str) -> bool:
    if CONTACT_EMAIL_RE.search(sentence):
        return True
    if CONTACT_PHONE_RE.search(sentence):
        return True

    normalized = sentence.lower()
    if any(keyword in normalized for keyword in CONTACT_KEYWORDS) and len(sentence) <= 80:
        return True

    if "|" in sentence and len(sentence) <= 120:
        return True

    capitalized_words = sum(word[:1].isupper() for word in sentence.split())
    if len(sentence.split()) <= 4 and capitalized_words >= 2:
        return True

    return False


def _is_signature_terminator(sentence: str) -> bool:
    return _is_quote_delimiter(sentence) or _is_quote_header(sentence)


def _is_quote_header(sentence: str) -> bool:
    lower = sentence.lower()
    return lower.startswith("on ") and " wrote:" in lower


def _is_quote_delimiter(sentence: str) -> bool:
    stripped = sentence.strip()
    if not stripped:
        return False
    lower = stripped.lower()
    if stripped in {"---", "--"}:
        return True
    if stripped.startswith(">"):
        return True
    if any(keyword in lower for keyword in QUOTE_DELIMITER_KEYWORDS):
        return True
    if len(stripped) >= 3 and len(set(stripped)) == 1 and stripped[0] in {"-", "_", "·", "=", "*", "#"}:
        return True
    return False


def _is_email_header_line(sentence: str) -> bool:
    lower = sentence.lower()
    return lower.startswith(EMAIL_HEADER_PREFIXES)


def _normalize_sentence(sentence: str) -> str:
    return sentence.strip(string.punctuation + " ").lower()


def _html_to_text(html: str) -> str:
    if not html:
        return ""

    text = html
    text = text.replace("\r\n", "\n")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"(?i)</div>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
