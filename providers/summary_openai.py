import os
from openai import OpenAI
from typing import List


MODEL = os.getenv("WEEKLY_SUMMARY_MODEL", "gpt-5")


def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=api_key)


def _read_markdown_files(file_paths: List[str]) -> str:
    """
    Read and combine all markdown files into a single string.
    Each file is separated by a clear delimiter.
    """
    combined = []
    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    # Extract filename for context
                    filename = os.path.basename(file_path)
                    combined.append(f"=== File: {filename} ===\n\n{content}\n")
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            continue
    
    return "\n\n".join(combined)


def generate_weekly_summary(markdown_files: List[str], user_prompt: str) -> str:
    """
    Generate a weekly summary from a list of markdown files using GPT-5.
    
    Args:
        markdown_files: List of file paths to markdown files
        user_prompt: User-provided prompt for summary generation
    
    Returns:
        Generated summary as markdown string
    """
    if not markdown_files:
        return "# Weekly Summary\n\nNo files found for this week.\n"
    
    client = _get_client()
    
    # Read all markdown files
    combined_content = _read_markdown_files(markdown_files)
    
    if not combined_content.strip():
        return "# Weekly Summary\n\nNo content found in files.\n"
    
    # Construct the full prompt
    system_prompt = (
        "You are a helpful assistant that creates concise, well-organized weekly summaries "
        "from markdown notes. Focus on key insights, themes, and important information. "
        "Format your response as clean Markdown."
    )
    
    user_message = f"""{user_prompt}

Here are the markdown files from this week:

{combined_content}

Please create a comprehensive weekly summary based on the above content."""
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_completion_tokens=4000  # Allow for longer summaries
    )
    
    summary = (response.choices[0].message.content or "").strip()
    return summary if summary else "# Weekly Summary\n\nSummary generation returned empty result.\n"

