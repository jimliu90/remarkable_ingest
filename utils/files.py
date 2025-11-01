import os, re, unicodedata, pathlib


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


def ensure_dir(path: str):
    pathlib.Path(os.path.expanduser(path)).mkdir(parents=True, exist_ok=True)

