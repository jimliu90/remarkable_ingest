import base64, os
from openai import OpenAI


MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=api_key)


def _png_bytes_to_data_url(png_bytes: bytes) -> str:
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64}"


SYSTEM_PROMPT = (
    "You are a precise handwriting OCR assistant. "
    "Extract all legible text from the image and return **only Markdown**. "
    "Preserve headings with `#`, bullets, numbered lists, and spacing. "
    "Do not invent content; transcribe faithfully."
)


def ocr_png_to_markdown_openai(png_bytes: bytes) -> str:
    client = _get_client()
    data_url = _png_bytes_to_data_url(png_bytes)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Convert this handwritten note to clean Markdown."},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url}
                    }
                ]
            }
        ],
        max_completion_tokens=2000
    )

    return (response.choices[0].message.content or "").strip() + "\n"

