import os, datetime as dt
from dotenv import load_dotenv
from providers.gmail_client import get_gmail_service, search_messages, fetch_png_attachments
from providers.ocr_handwriting_openai import ocr_png_to_markdown_openai
from utils.files import sanitize_filename, ensure_dir, clean_filename_for_ocr
from utils.md import prepend_front_matter
from utils.state import seen, remember


load_dotenv()
LABEL = os.getenv("GMAIL_LABEL", "Remarkable")
OUTPUT_DIR = os.path.expanduser(os.getenv("OUTPUT_DIR", "~/Documents/remarkable-md"))
WINDOW_DAYS = int(os.getenv("SEARCH_WINDOW_DAYS", "14"))


QUERY = f'(label:{LABEL}) (has:attachment) filename:png newer_than:{WINDOW_DAYS}d'


def main():
    ensure_dir(OUTPUT_DIR)
    service = get_gmail_service()

    msg_ids = search_messages(service, QUERY)
    total_saved = 0

    for mid in msg_ids:
        for fname, data, internal_date_ms in fetch_png_attachments(service, mid):
            key = f"{mid}:{fname}"
            if seen(key):
                continue

            # Use email receipt date for filename
            email_date = dt.datetime.fromtimestamp(internal_date_ms / 1000)
            date_str = email_date.strftime("%Y-%m-%d")
            
            # Clean the filename according to convention
            cleaned_name = clean_filename_for_ocr(fname)
            
            # Route to subdirectory based on title content
            title_lower = cleaned_name.lower()
            if "weekly" in title_lower or "daily" in title_lower:
                subdirectory = "review"
            else:
                subdirectory = "general"
            
            # Format: YYYY-MM-DD-lower-case-hyphenated-name.md
            filename = f"{date_str}-{cleaned_name}.md"
            subdir_path = os.path.join(OUTPUT_DIR, subdirectory)
            ensure_dir(subdir_path)
            out_path = os.path.join(subdir_path, filename)
            
            # Use original filename (sanitized) for title in front matter
            title = sanitize_filename(os.path.splitext(fname)[0])
            md_body = ocr_png_to_markdown_openai(data)

            # Include email date in front matter
            email_date_str = email_date.strftime("%Y-%m-%d %H:%M:%S")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(prepend_front_matter(md_body, title, "Gmail/reMarkable", email_date_str))

            remember(key)
            total_saved += 1
            print(f"Wrote {out_path}")

    print(f"Done. processed_messages={len(msg_ids)} saved_files={total_saved}")


if __name__ == "__main__":
    main()
