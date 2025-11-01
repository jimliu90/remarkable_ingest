def prepend_front_matter(md: str, title: str, source: str, email_date: str = None) -> str:
    front_matter = "---\n"
    front_matter += f"title: \"{title}\"\n"
    front_matter += f"source: \"{source}\"\n"
    if email_date:
        front_matter += f"email_date: \"{email_date}\"\n"
    front_matter += "---\n\n"
    return front_matter + md.strip() + "\n"

