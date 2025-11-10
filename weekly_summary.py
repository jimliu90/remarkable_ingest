#!/usr/bin/env python3
"""
Weekly Summary Generator

Generates a weekly summary of markdown files from the past week (7 days ending on most recent Sunday 9am)
and emails it to the configured email address.
"""

import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
from providers.gmail_client import get_gmail_service, send_email
from providers.summary_openai import generate_weekly_summary
from utils.weekly import (
    get_weekly_date_range,
    find_markdown_files_in_range,
    get_weekly_summary_filename,
    weekly_summary_exists,
    get_most_recent_sunday_9am
)
from utils.files import ensure_dir
from utils.md import prepend_front_matter


load_dotenv()
OUTPUT_DIR = os.path.expanduser(os.getenv("OUTPUT_DIR", "~/Documents/remarkable-md"))
WEEKLY_SUMMARY_PROMPT = os.getenv("WEEKLY_SUMMARY_PROMPT", "")
WEEKLY_SUMMARY_EMAIL = os.getenv("WEEKLY_SUMMARY_EMAIL", "jim.liu90@gmail.com")


def main():
    parser = argparse.ArgumentParser(description="Generate weekly summary of markdown files")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if summary already exists"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually generating or sending"
    )
    args = parser.parse_args()
    
    # Check if prompt is configured
    if not WEEKLY_SUMMARY_PROMPT:
        print("Error: WEEKLY_SUMMARY_PROMPT not set in environment")
        print("Please add WEEKLY_SUMMARY_PROMPT to your .env file")
        return 1
    
    # Get date range
    start_date, end_date = get_weekly_date_range()
    sunday_date = get_most_recent_sunday_9am()
    
    print(f"Weekly Summary Generation")
    print(f"Date range: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"Summary date: {sunday_date.strftime('%Y-%m-%d')}")
    
    # Check if summary already exists
    if not args.force and weekly_summary_exists(OUTPUT_DIR, sunday_date):
        print(f"Summary already exists for {sunday_date.strftime('%Y-%m-%d')}. Use --force to regenerate.")
        return 0
    
    # Find markdown files in range
    markdown_files = find_markdown_files_in_range(OUTPUT_DIR, start_date, end_date)
    
    if not markdown_files:
        print(f"No markdown files found in date range.")
        if args.dry_run:
            print("(Dry run - would skip generation)")
        return 0
    
    print(f"Found {len(markdown_files)} markdown file(s) in range:")
    for f in markdown_files[:5]:  # Show first 5
        print(f"  - {os.path.basename(f)}")
    if len(markdown_files) > 5:
        print(f"  ... and {len(markdown_files) - 5} more")
    
    if args.dry_run:
        print("\n(Dry run - would generate summary and send email)")
        return 0
    
    # Generate summary
    print("\nGenerating summary with GPT...")
    try:
        summary_content = generate_weekly_summary(markdown_files, WEEKLY_SUMMARY_PROMPT)
    except Exception as e:
        print(f"Error generating summary: {e}")
        return 1
    
    # Save summary file
    weeklies_dir = os.path.join(OUTPUT_DIR, "generated-weeklies")
    ensure_dir(weeklies_dir)
    filename = get_weekly_summary_filename(sunday_date)
    summary_path = os.path.join(weeklies_dir, filename)
    
    # Add front matter
    title = f"Weekly Summary - {sunday_date.strftime('%Y-%m-%d')}"
    full_content = prepend_front_matter(
        summary_content,
        title,
        "Weekly Summary Generator",
        sunday_date.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    
    print(f"Saved summary to: {summary_path}")
    
    # Send email
    print(f"Sending email to {WEEKLY_SUMMARY_EMAIL}...")
    try:
        service = get_gmail_service()
        subject = f"Weekly Summary - {sunday_date.strftime('%Y-%m-%d')}"
        body = f"""Weekly Summary for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

Generated from {len(markdown_files)} markdown file(s).

See attached file for the full summary.
"""
        success = send_email(service, WEEKLY_SUMMARY_EMAIL, subject, body, summary_path)
        
        if success:
            print("Email sent successfully!")
        else:
            print("Warning: Email sending failed, but summary file was saved.")
            return 1
    except Exception as e:
        print(f"Error sending email: {e}")
        print("Summary file was saved, but email was not sent.")
        return 1
    
    print("Done!")
    return 0


if __name__ == "__main__":
    exit(main())

