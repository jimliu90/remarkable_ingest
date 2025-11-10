import os
import re
from datetime import datetime, timedelta
from typing import List, Tuple
from pathlib import Path


def get_most_recent_sunday_9am() -> datetime:
    """
    Calculate the most recent Sunday at 9:00 AM.
    If today is Sunday but before 9am, use last Sunday.
    If today is Sunday after 9am, use today at 9am.
    """
    now = datetime.now()
    
    # Find the most recent Sunday
    days_since_sunday = (now.weekday() + 1) % 7  # 0 = Monday, 6 = Sunday
    if days_since_sunday == 0:  # Today is Sunday
        if now.hour < 9 or (now.hour == 9 and now.minute < 0):
            # Before 9am, use last Sunday
            days_since_sunday = 7
    
    most_recent_sunday = now - timedelta(days=days_since_sunday)
    most_recent_sunday = most_recent_sunday.replace(hour=9, minute=0, second=0, microsecond=0)
    
    return most_recent_sunday


def get_weekly_date_range() -> Tuple[datetime, datetime]:
    """
    Get the date range for the weekly summary.
    Returns (start_date, end_date) where:
    - end_date: Most recent Sunday at 9:00 AM
    - start_date: 7 days before end_date (previous Sunday at 9:00 AM)
    """
    end_date = get_most_recent_sunday_9am()
    start_date = end_date - timedelta(days=7)
    return (start_date, end_date)


def extract_date_from_filename(filename: str) -> datetime:
    """
    Extract date from filename format: YYYY-MM-DD-HHMM-*.md
    Returns datetime object, or None if parsing fails.
    """
    # Pattern: YYYY-MM-DD-HHMM
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})-(\d{4})", filename)
    if match:
        year, month, day, time_str = match.groups()
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        try:
            return datetime(int(year), int(month), int(day), hour, minute)
        except ValueError:
            return None
    return None


def find_markdown_files_in_range(
    output_dir: str,
    start_date: datetime,
    end_date: datetime
) -> List[str]:
    """
    Find all markdown files in output_dir (including subdirectories)
    that fall within the date range [start_date, end_date).
    
    Returns list of full file paths.
    """
    output_path = Path(os.path.expanduser(output_dir))
    if not output_path.exists():
        return []
    
    matching_files = []
    
    # Search in all subdirectories (review/, general/, etc.)
    for md_file in output_path.rglob("*.md"):
        # Skip files in generated-weeklies directory
        if "generated-weeklies" in md_file.parts:
            continue
        
        filename = md_file.name
        file_date = extract_date_from_filename(filename)
        
        if file_date is None:
            # If we can't parse the date, skip it
            continue
        
        # Check if file date is within range [start_date, end_date)
        if start_date <= file_date < end_date:
            matching_files.append(str(md_file))
    
    # Sort by date
    matching_files.sort(key=lambda f: extract_date_from_filename(Path(f).name) or datetime.min)
    
    return matching_files


def get_weekly_summary_filename(sunday_date: datetime) -> str:
    """
    Generate filename for weekly summary: YYYY-MM-DD-weekly.md
    """
    return f"{sunday_date.strftime('%Y-%m-%d')}-weekly.md"


def weekly_summary_exists(output_dir: str, sunday_date: datetime) -> bool:
    """
    Check if weekly summary file already exists for the given Sunday date.
    """
    output_path = Path(os.path.expanduser(output_dir))
    weeklies_dir = output_path / "generated-weeklies"
    filename = get_weekly_summary_filename(sunday_date)
    summary_path = weeklies_dir / filename
    return summary_path.exists()

