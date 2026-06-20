"""
Duplicate detection for articles.

Persian text on the web is frequently noisy: zero-width spaces (U+200B/C/D),
Arabic vs. Persian letter forms (ي/ی, ك/ک), tatweel, mixed punctuation and
extra whitespace. Two copies of the same story can therefore look different
character-by-character but be semantically identical.

This module provides:

  * ``normalize_title(text)`` – cleans and normalises a Persian title into a
    canonical form used for comparison.
  * ``title_hash(text)``      – a short SHA-1 of the normalised title, stored
    on ``Article.dedup_hash`` so duplicates can be found with a single indexed
    equality lookup.
  * ``is_duplicate(title, feed=None, exclude_pk=None)`` – convenience used by
    the RSS importer to decide whether to skip an incoming item.

These helpers are deliberately pure (no Django I/O) except ``is_duplicate``,
which keeps the query logic in one place.
"""

import hashlib
import re
import unicodedata

# ---------------------------------------------------------------------------
# Character maps
# ---------------------------------------------------------------------------
# Map Arabic letters commonly mixed with Persian to their Persian equivalents.
_ARABIC_TO_PERSIAN = {
    'ي': 'ی',   # Arabic Yeh -> Persian Yeh
    'ك': 'ک',   # Arabic Kaf -> Persian Keheh
    'ة': 'ه',   # Taa Marbuta -> Heh
    'ؤ': 'و',
    'إ': 'ا',
    'أ': 'ا',
    'آ': 'ا',
}

# Zero-width and invisible formatting characters we want to strip entirely.
_INVISIBLE_RE = re.compile(r'[\u200b\u200c\u200d\u200e\u200f\ufeff\u202a-\u202e]')

# Anything that is not a Persian letter/digit or latin alnum gets collapsed
# to a single space; this makes punctuation differences irrelevant.
_NON_WORD_RE = re.compile(r'[^\u0600-\u06FF\u0660-\u0669a-z0-9آ]+', re.UNICODE)

# Collapse multiple spaces.
_MULTISPACE_RE = re.compile(r'\s+')


def normalize_title(text: str) -> str:
    """
    Return a canonical, lower-cased, cleaned form of a Persian title.

    Steps:
      1. NFKC unicode normalisation (composition).
      2. Replace common Arabic look-alikes with their Persian forms.
      3. Strip zero-width / invisible formatting characters.
      4. Lower-case latin letters (Persian has no case).
      5. Replace any run of non-word characters with a single space.
      6. Trim and collapse repeated spaces.
    """
    if not text:
        return ''

    # 1. Unicode normalisation.
    s = unicodedata.normalize('NFKC', text)

    # 2. Arabic -> Persian letter mapping.
    s = ''.join(_ARABIC_TO_PERSIAN.get(ch, ch) for ch in s)

    # 3. Remove invisible / zero-width characters.
    s = _INVISIBLE_RE.sub('', s)

    # 4. Lower-case (affects latin characters; harmless for Persian).
    s = s.lower()

    # 5. Replace punctuation/separator runs with a single space.
    s = _NON_WORD_RE.sub(' ', s)

    # 6. Collapse whitespace and trim.
    s = _MULTISPACE_RE.sub(' ', s).strip()

    return s


def title_hash(text: str) -> str:
    """
    SHA-1 of the normalised title.

    A short, stable identifier suitable for a DB index. We hash so very long
    titles don't blow past the column width and so the index stays compact.
    """
    return hashlib.sha1(normalize_title(text).encode('utf-8')).hexdigest()


def is_duplicate(title: str, feed=None, exclude_pk=None) -> bool:
    """
    Return True if an article with the same normalised title already exists.

    ``feed`` (optional) restricts the search to a single feed — useful when you
    only care about duplicates *within* one source.
    ``exclude_pk`` (optional) ignores the article currently being edited.
    """
    from apps.news.models import Article

    h = title_hash(title)
    if not h:
        return False

    qs = Article.objects.filter(dedup_hash=h)
    if feed is not None:
        qs = qs.filter(feed=feed)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
