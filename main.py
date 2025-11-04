import os, datetime as dt, argparse
from collections import defaultdict
from typing import List, Tuple
from dotenv import load_dotenv
from providers.gmail_client import get_gmail_service, search_messages, fetch_png_attachments
from providers.ocr_handwriting_openai import ocr_png_to_markdown_openai
from utils.files import sanitize_filename, ensure_dir, clean_filename_for_ocr, extract_page_number, extract_base_name
from utils.md import prepend_front_matter
from utils.state import seen, remember


load_dotenv()
LABEL = os.getenv("GMAIL_LABEL", "Remarkable")
OUTPUT_DIR = os.path.expanduser(os.getenv("OUTPUT_DIR", "~/Documents/remarkable-md"))
WINDOW_DAYS = int(os.getenv("SEARCH_WINDOW_DAYS", "14"))


QUERY = f'(label:{LABEL}) (has:attachment) filename:png newer_than:{WINDOW_DAYS}d'


def process_attachments(msg_id: str, attachments: List[Tuple[str, bytes, int]], service, force: bool = False) -> int:
    """
    Process attachments from a single email, grouping multi-page documents.
    Returns number of files saved.
    
    Args:
        force: If True, bypass deduplication check and process all attachments
    """
    if not attachments:
        return 0
    
    # Group attachments by base name (documents with same base name are treated as multi-page)
    grouped = defaultdict(list)
    for fname, data, internal_date_ms in attachments:
        key = f"{msg_id}:{fname}"
        if not force and seen(key):
            continue
        # Mark as seen immediately to prevent reprocessing (unless force mode)
        if not force:
            remember(key)
        
        base_name = extract_base_name(fname)
        page_num = extract_page_number(fname)
        grouped[base_name].append((fname, data, internal_date_ms, page_num))
    
    if not grouped:
        return 0
    
    # Get email date from first attachment (all from same email)
    first_att = attachments[0]
    internal_date_ms = first_att[2]
    internal_date_ms_int = int(internal_date_ms) if isinstance(internal_date_ms, str) else internal_date_ms
    email_date = dt.datetime.fromtimestamp(internal_date_ms_int / 1000)
    date_str = email_date.strftime("%Y-%m-%d")
    time_str = email_date.strftime("%H%M")  # Format: 1100 for 11:00am, 2330 for 11:30pm
    email_date_str = email_date.strftime("%Y-%m-%d %H:%M:%S")
    
    total_saved = 0
    
    for base_name, att_list in grouped.items():
        # Sort by page number (None goes first, then by page number)
        att_list.sort(key=lambda x: (x[3] is None, x[3] if x[3] is not None else 0))
        
        # Determine if this is a multi-page document
        has_pages = any(att[3] is not None for att in att_list)
        
        # Clean base name for filename
        cleaned_name = clean_filename_for_ocr(base_name)
        
        # Route to subdirectory based on title content
        title_lower = cleaned_name.lower()
        if "weekly" in title_lower or "daily" in title_lower:
            subdirectory = "review"
        else:
            subdirectory = "general"
        
        # Format: YYYY-MM-DD-HHMM-lower-case-hyphenated-name.md
        filename = f"{date_str}-{time_str}-{cleaned_name}.md"
        subdir_path = os.path.join(OUTPUT_DIR, subdirectory)
        ensure_dir(subdir_path)
        out_path = os.path.join(subdir_path, filename)
        
        # If file exists, add seconds to make it unique
        if os.path.exists(out_path):
            ts_sec = dt.datetime.now().strftime("%S")
            filename = f"{date_str}-{time_str}{ts_sec}-{cleaned_name}.md"
            out_path = os.path.join(subdir_path, filename)
        
        # Process all pages through OCR and combine
        md_parts = []
        for fname, data, _, page_num in att_list:
            if has_pages:
                print(f"  Processing page {page_num} of {base_name}")
            md_body = ocr_png_to_markdown_openai(data)
            if md_body.strip():
                md_parts.append(md_body.strip())
        
        # Combine all markdown parts with separator
        combined_md = "\n\n---\n\n".join(md_parts) if len(md_parts) > 1 else md_parts[0] if md_parts else ""
        
        # Use original base name (sanitized) for title in front matter
        title = sanitize_filename(base_name)
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(prepend_front_matter(combined_md, title, "Gmail/reMarkable", email_date_str))
        
        total_saved += 1
        print(f"Wrote {out_path} ({len(att_list)} page{'s' if len(att_list) > 1 else ''})")
    
    return total_saved


def main():
    parser = argparse.ArgumentParser(description="Process reMarkable notes from Gmail")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of all attachments, bypassing deduplication check"
    )
    args = parser.parse_args()
    
    ensure_dir(OUTPUT_DIR)
    service = get_gmail_service()

    msg_ids = search_messages(service, QUERY)
    total_saved = 0

    if args.force:
        print("Force mode enabled: processing all attachments (bypassing deduplication)")

    for mid in msg_ids:
        attachments = fetch_png_attachments(service, mid)
        if attachments:
            saved = process_attachments(mid, attachments, service, force=args.force)
            total_saved += saved

    print(f"Done. processed_messages={len(msg_ids)} saved_files={total_saved}")


if __name__ == "__main__":
    main()
