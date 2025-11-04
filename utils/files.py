import os, re, unicodedata, pathlib
from typing import Optional


def sanitize_filename(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = re.sub(r"[^\w\s.-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip().replace(" ", "_")
    return s or "document"


def clean_filename_for_ocr(name: str) -> str:
    """
    Clean filename for OCR output:
    - Remove page numbers (e.g., "page_9", "page9", "-_page_9")
    - Remove filler punctuation and underscores
    - Convert to lowercase
    - Replace spaces/underscores with hyphens
    - Remove multiple hyphens
    """
    # Remove extension if present
    name = os.path.splitext(name)[0]
    
    # Normalize unicode
    s = unicodedata.normalize("NFKD", name)
    
    # Remove page numbers and variations
    s = re.sub(r"[_\s-]*page[_\s-]*\d+[_\s-]*", "", s, flags=re.IGNORECASE)
    
    # Remove common filler words/patterns
    s = re.sub(r"[_\s-]+(the|a|an|and|or|of|in|on|at|to|for)[_\s-]+", " ", s, flags=re.IGNORECASE)
    
    # Replace underscores and multiple spaces with single space
    s = re.sub(r"[_\s]+", " ", s)
    
    # Remove all non-alphanumeric except spaces (keep letters and numbers)
    s = re.sub(r"[^\w\s]", "", s)
    
    # Normalize spaces to single spaces
    s = re.sub(r"\s+", " ", s).strip()
    
    # Convert to lowercase
    s = s.lower()
    
    # Replace spaces with hyphens
    s = s.replace(" ", "-")
    
    # Remove multiple consecutive hyphens
    s = re.sub(r"-+", "-", s)
    
    # Remove leading/trailing hyphens
    s = s.strip("-")
    
    return s or "document"


def extract_page_number(filename: str) -> Optional[int]:
    """
    Extract page number from filename like "daily review- page 3" or "document_page_5".
    Returns page number as int, or None if no page number found.
    """
    # Look for patterns like "page 3", "page3", "page_3", "- page 3", etc.
    match = re.search(r"[_\s-]*(?:page|p)[_\s-]*(\d+)", filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def extract_base_name(filename: str) -> str:
    """
    Extract base name from filename by removing page numbers.
    Used to group multi-page documents together.
    """
    name = os.path.splitext(filename)[0]
    # Remove page number patterns
    base = re.sub(r"[_\s-]*(?:page|p)[_\s-]*\d+[_\s-]*", "", name, flags=re.IGNORECASE)
    # Clean up trailing/leading separators
    base = re.sub(r"[_\s-]+$", "", base)
    base = re.sub(r"^[_\s-]+", "", base)
    return base.strip() or "document"


def ensure_dir(path: str):
    pathlib.Path(os.path.expanduser(path)).mkdir(parents=True, exist_ok=True)

