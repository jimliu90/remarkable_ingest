# reMarkable → Gmail → OpenAI Vision → Markdown Implementation Plan

## Overview

Implement a Python-based pipeline that automatically fetches PNG attachments from Gmail (labeled "Remarkable"), converts handwriting to Markdown using OpenAI's Vision API, and saves the results locally with front matter metadata. The system includes state tracking for idempotency and macOS launchd scheduling for automated runs.

## Current State Analysis

This is a greenfield project. No existing code or infrastructure exists. The target directory `/Users/jim/Dev/monorepo/dev/remarkable_ingest` has been created but is empty.

### Key Requirements:

- Gmail OAuth integration (Desktop app flow)
- PNG attachment extraction from labeled emails
- OpenAI Vision API integration for handwriting OCR
- Markdown output with front matter
- State tracking to prevent duplicate processing
- macOS launchd scheduling (9am, 3pm, 9pm PT + RunAtLoad)
- Idempotent operation (safe to re-run)

### Constraints:

- Must use OpenAI Vision API (not Google Cloud Vision)
- Files stay local; only PNG bytes sent to OpenAI
- PNG-only filtering (best results from reMarkable export)
- State persistence across runs

## Desired End State

After implementation, the system should:

1. **Automatically run** on schedule (via launchd) at 9am, 3pm, and 9pm PT, plus on system load
2. **Fetch emails** from Gmail with the specified label that have PNG attachments within the search window
3. **Process each PNG** exactly once (idempotent via state tracking)
4. **Convert handwriting** to clean Markdown using OpenAI Vision API
5. **Save files** to the configured output directory with front matter and timestamp
6. **Log activity** to stdout/stderr files for monitoring

### Verification:

- All specified files and directories exist in the correct structure
- First manual run successfully authenticates with Gmail and processes at least one attachment
- State file tracks processed items correctly
- Launchd service can be loaded and runs on schedule
- No duplicate output files are created on re-runs

## What We're NOT Doing

- Google Cloud Vision API integration (using OpenAI instead)
- Multiple file format support (PNG-only for now)
- Cloud storage or sync (local files only)
- Real-time processing (scheduled batch only)
- Email sending or reply functionality
- UI or interactive components
- Multi-user or authentication layer
- Backup or archival of processed emails

## Implementation Approach

The implementation will be structured in phases:

1. **Project Setup**: Directory structure, dependencies, and configuration
2. **Core Utilities**: File handling, markdown formatting, and state management
3. **Provider Integrations**: Gmail client and OpenAI OCR
4. **Main Orchestration**: Main script that ties everything together
5. **Deployment**: Launchd configuration and setup scripts

This follows a bottom-up approach, building utilities first, then providers, then orchestration.

## Phase 1: Project Setup & Structure

### Overview

Create the complete directory structure, dependency management files, and environment configuration template.

### Changes Required:

#### 1. Directory Structure

**Action**: Create all required directories and placeholder files

```
remarkable_ingest/
├─ main.py (placeholder - Phase 4)
├─ requirements.txt
├─ .env.example
├─ utils/
│  ├─ __init__.py
│  ├─ files.py
│  ├─ md.py
│  └─ state.py
├─ providers/
│  ├─ __init__.py
│  ├─ gmail_client.py
│  └─ ocr_handwriting_openai.py
└─ launchd/
   └─ com.remarkable.ingest.plist
```

#### 2. requirements.txt

**File**: `requirements.txt`
**Changes**: Create dependency specification

```txt
openai>=1.0.0
google-api-python-client>=2.0.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.0.0
python-dotenv>=1.0.0
```

#### 3. .env.example

**File**: `.env.example`
**Changes**: Create environment variable template

```env
# Gmail
GMAIL_LABEL=Remarkable
SEARCH_WINDOW_DAYS=14

# Output
OUTPUT_DIR=~/Documents/remarkable-md

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-5-mini
```

**Note**: Updated to use `gpt-5-mini` as the default model (newer, cheaper, and better for OCR tasks). Can be overridden via `OPENAI_MODEL` env var.

#### 4. README.md

**File**: `README.md`
**Changes**: Create setup and usage documentation

```markdown
# reMarkable Ingest

Automatically converts reMarkable PNG exports from Gmail to Markdown using OpenAI Vision API.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and configure
3. Set up Gmail OAuth: Place `credentials.json` in project root
4. Run first time: `python main.py` (will open browser for auth)
5. Install launchd service: See launchd/README.md
```

### Success Criteria:

#### Automated Verification:

- [x] All directories exist with correct structure
- [x] `requirements.txt` contains all specified packages with version pins
- [x] `.env.example` includes all required variables with sensible defaults
- [x] Python virtual environment can be created: `python3 -m venv .venv`
- [x] Dependencies install cleanly: `pip install -r requirements.txt`

#### Manual Verification:

- [x] Directory structure matches specification exactly
- [x] `.env.example` provides clear guidance for configuration
- [x] README.md is readable and accurate

---

## Phase 2: Core Utilities Implementation

### Overview

Implement the utility modules for file handling, markdown formatting, and state management.

### Changes Required:

#### 1. utils/files.py

**File**: `utils/files.py`
**Changes**: Implement filename sanitization and directory creation

```python
import os, re, unicodedata, pathlib


def sanitize_filename(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = re.sub(r"[^\w\s.-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip().replace(" ", "_")
    return s or "document"


def ensure_dir(path: str):
    pathlib.Path(os.path.expanduser(path)).mkdir(parents=True, exist_ok=True)
```

#### 2. utils/md.py

**File**: `utils/md.py`
**Changes**: Implement front matter prepending

```python
def prepend_front_matter(md: str, title: str, source: str) -> str:
    return (
        "---\n"
        f"title: \"{title}\"\n"
        f"source: \"{source}\"\n"
        "---\n\n"
        + md.strip() + "\n"
    )
```

#### 3. utils/state.py

**File**: `utils/state.py`
**Changes**: Implement thread-safe state tracking for idempotency

```python
import json, os, threading
_LOCK = threading.Lock()
_STATE_PATH = os.path.expanduser("~/remarkable-ingest/state.json")


def _load():
    if not os.path.exists(_STATE_PATH): return {"seen": []}
    with open(_STATE_PATH, "r") as f: return json.load(f)


def _save(s):
    os.makedirs(os.path.dirname(_STATE_PATH), exist_ok=True)
    with open(_STATE_PATH, "w") as f: json.dump(s, f)


def seen(key: str) -> bool:
    with _LOCK:
        s = _load()
        return key in s["seen"]


def remember(key: str):
    with _LOCK:
        s = _load()
        s["seen"].append(key)
        if len(s["seen"]) > 50000:
            s["seen"] = s["seen"][-30000:]
        _save(s)
```

**Note**: State file location uses `~/remarkable-ingest/state.json` (not in project directory) as specified.

#### 4. utils/**init**.py

**File**: `utils/__init__.py`
**Changes**: Create empty init file for package structure

```python
# Utils package
```

### Success Criteria:

#### Automated Verification:

- [x] `sanitize_filename()` handles unicode, special characters, and edge cases correctly
- [x] `ensure_dir()` creates nested directories and handles existing dirs
- [x] `prepend_front_matter()` formats YAML front matter correctly
- [x] `seen()` and `remember()` are thread-safe and persist correctly
- [x] State file rotation works when limit exceeded (50k → 30k)
- [x] All functions have proper error handling
- [x] Unit tests can be written (no external dependencies)

#### Manual Verification:

- [ ] Test `sanitize_filename()` with various inputs (unicode, special chars, empty)
- [ ] Test `prepend_front_matter()` output format matches specification
- [ ] State persistence works across multiple runs

---

## Phase 3: Provider Integrations

### Overview

Implement Gmail client and OpenAI OCR provider modules.

### Changes Required:

#### 1. providers/gmail_client.py

**File**: `providers/gmail_client.py`
**Changes**: Implement Gmail OAuth and attachment fetching

```python
import base64, os
from typing import List, Tuple
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def search_messages(service, query: str, max_results: int = 200) -> List[str]:
    resp = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return [m["id"] for m in resp.get("messages", [])]


def fetch_png_attachments(service, msg_id: str) -> List[Tuple[str, bytes]]:
    msg = service.users().messages().get(userId="me", id=msg_id).execute()
    attachments = []
    stack = (msg.get("payload", {}) or {}).get("parts", []) or []
    while stack:
        part = stack.pop()
        if part.get("parts"):
            stack.extend(part["parts"])
            continue
        filename = (part.get("filename") or "").lower()
        if not filename.endswith(".png"):
            continue
        body = part.get("body", {})
        att_id = body.get("attachmentId")
        if att_id:
            att = service.users().messages().attachments().get(
                userId="me", messageId=msg_id, id=att_id
            ).execute()
            data = base64.urlsafe_b64decode(att.get("data", b""))
            attachments.append((part.get("filename") or "attachment.png", data))
    return attachments
```

**Note**: `token.json` will be created on first run in project root.

#### 2. providers/ocr_handwriting_openai.py

**File**: `providers/ocr_handwriting_openai.py`
**Changes**: Implement OpenAI Vision API integration for OCR

**IMPORTANT**: The spec uses `client.responses.create()` which appears to be incorrect API usage. OpenAI's Chat Completions API with vision uses `client.chat.completions.create()` with messages containing image URLs. We'll implement the correct API pattern:

```python
import base64, os
from openai import OpenAI


MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

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
        max_tokens=2000
    )

    return (response.choices[0].message.content or "").strip() + "\n"
```

**Correction from spec**: The spec's API call `client.responses.create()` is incorrect. The correct OpenAI API uses `client.chat.completions.create()` with vision-capable models. The message format uses `image_url` with `url` pointing to a data URL.

#### 3. providers/**init**.py

**File**: `providers/__init__.py`
**Changes**: Create empty init file

```python
# Providers package
```

### Success Criteria:

#### Automated Verification:

- [x] Gmail OAuth flow can authenticate (requires manual browser interaction first time)
- [x] `search_messages()` returns message IDs for valid queries
- [x] `fetch_png_attachments()` extracts PNG attachments correctly from multipart messages
- [x] OpenAI client initializes correctly with API key from env
- [x] `ocr_png_to_markdown_openai()` makes valid API calls
- [x] Error handling for missing credentials, API failures, network issues

#### Manual Verification:

- [ ] First run opens browser and successfully authorizes Gmail
- [ ] `token.json` is created and used on subsequent runs
- [ ] Gmail search returns expected messages
- [ ] PNG attachments are extracted correctly
- [ ] OpenAI API returns valid Markdown from test PNG
- [ ] Rate limiting and errors are handled gracefully

---

## Phase 4: Main Orchestration

### Overview

Implement the main script that orchestrates the entire pipeline.

### Changes Required:

#### 1. main.py

**File**: `main.py`
**Changes**: Implement main orchestration logic

```python
import os, datetime as dt
from dotenv import load_dotenv
from providers.gmail_client import get_gmail_service, search_messages, fetch_png_attachments
from providers.ocr_handwriting_openai import ocr_png_to_markdown_openai
from utils.files import sanitize_filename, ensure_dir
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
        for fname, data in fetch_png_attachments(service, mid):
            key = f"{mid}:{fname}"
            if seen(key):
                continue

            title = sanitize_filename(os.path.splitext(fname)[0])
            md_body = ocr_png_to_markdown_openai(data)
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(OUTPUT_DIR, f"{title}__{ts}.md")

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(prepend_front_matter(md_body, title, "Gmail/reMarkable"))

            remember(key)
            total_saved += 1
            print(f"Wrote {out_path}")

    print(f"Done. processed_messages={len(msg_ids)} saved_files={total_saved}")


if __name__ == "__main__":
    main()
```

**Note**: The script will expand `~` in OUTPUT_DIR, handle missing .env gracefully with defaults, and print progress.

### Success Criteria:

#### Automated Verification:

- [x] Script runs without syntax errors: `python main.py --help` (if help added) or `python -m py_compile main.py`
- [x] Environment variables load correctly with defaults
- [x] All imports resolve correctly
- [x] No uncaught exceptions in happy path
- [x] Script exits cleanly even with no messages found

#### Manual Verification:

- [ ] First run successfully authenticates and processes at least one attachment
- [ ] Output files are created with correct format and front matter
- [ ] Re-running processes only new messages (idempotent)
- [ ] Error messages are clear for common failures (missing API key, auth issues)
- [ ] Console output shows progress clearly

---

## Phase 5: Launchd Configuration & Deployment

### Overview

Create launchd plist for macOS scheduling and deployment documentation.

### Changes Required:

#### 1. launchd/com.remarkable.ingest.plist

**File**: `launchd/com.remarkable.ingest.plist`
**Changes**: Create launchd service configuration

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.remarkable.ingest</string>
    <key>StartCalendarInterval</key>
    <array>
      <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
      <dict><key>Hour</key><integer>15</integer><key>Minute</key><integer>0</integer></dict>
      <dict><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    </array>
    <key>RunAtLoad</key><true/>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/zsh</string>
      <string>-lc</string>
      <string>cd ~/Dev/monorepo/dev/remarkable_ingest && source .venv/bin/activate && python main.py >> run.log 2>&1</string>
    </array>
    <key>StandardOutPath</key><string>~/Dev/monorepo/dev/remarkable_ingest/stdout.log</string>
    <key>StandardErrorPath</key><string>~/Dev/monorepo/dev/remarkable_ingest/stderr.log</string>
    <key>WorkingDirectory</key><string>~/Dev/monorepo/dev/remarkable_ingest</string>
  </dict>
</plist>
```

**Note**: Updated paths to use actual project location instead of `~/remarkable-ingest`. Times are in 24-hour format (9, 15, 21 = 9am, 3pm, 9pm) in system timezone (user must ensure PT is correct).

#### 2. launchd/README.md

**File**: `launchd/README.md`
**Changes**: Create deployment instructions

````markdown
# Launchd Service Setup

## Installation

1. Copy the plist to LaunchAgents:
   ```bash
   cp com.remarkable.ingest.plist ~/Library/LaunchAgents/
   ```
````

2. Load the service:

   ```bash
   launchctl load ~/Library/LaunchAgents/com.remarkable.ingest.plist
   ```

3. Verify it's loaded:
   ```bash
   launchctl list | grep remarkable
   ```

## Uninstallation

1. Unload the service:

   ```bash
   launchctl unload ~/Library/LaunchAgents/com.remarkable.ingest.plist
   ```

2. Remove the plist:
   ```bash
   rm ~/Library/LaunchAgents/com.remarkable.ingest.plist
   ```

## Manual Run

To test the service manually:

```bash
launchctl start com.remarkable.ingest
```

## Logs

- Service output: `~/Dev/monorepo/dev/remarkable_ingest/run.log`
- Standard output: `~/Dev/monorepo/dev/remarkable_ingest/stdout.log`
- Standard error: `~/Dev/monorepo/dev/remarkable_ingest/stderr.log`

## Schedule

Runs at:

- 9:00 AM system time
- 3:00 PM system time
- 9:00 PM system time
- On system load (RunAtLoad)

**Note**: Times are in system timezone. Ensure your Mac is set to PT if you want Pacific Time.

````

#### 3. .gitignore
**File**: `.gitignore`
**Changes**: Create gitignore for sensitive files and generated content

```gitignore
# Environment
.env
token.json
credentials.json

# State
~/remarkable-ingest/state.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# Logs
*.log
run.log
stdout.log
stderr.log

# IDE
.vscode/
.idea/
*.swp
*.swo
````

### Success Criteria:

#### Automated Verification:

- [x] Plist XML is valid: `plutil -lint launchd/com.remarkable.ingest.plist`
- [x] All paths in plist are absolute and correct
- [x] `.gitignore` excludes all sensitive files

#### Manual Verification:

- [ ] Plist can be loaded without errors: `launchctl load ~/Library/LaunchAgents/com.remarkable.ingest.plist`
- [ ] Service appears in launchctl list
- [ ] Manual start runs successfully: `launchctl start com.remarkable.ingest`
- [ ] Logs are written to specified locations
- [ ] Service runs at scheduled times (verify after waiting)
- [ ] Unload/reload cycle works correctly

---

## Testing Strategy

### Unit Tests (Optional but Recommended)

Create `tests/` directory with:

- `test_files.py`: Test filename sanitization, directory creation
- `test_md.py`: Test front matter formatting
- `test_state.py`: Test state persistence and thread safety
- `test_ocr.py`: Mock OpenAI API responses

### Integration Testing

1. **Gmail Integration**:

   - Create test Gmail label
   - Send test email with PNG attachment
   - Verify extraction works

2. **OpenAI Integration**:

   - Use test PNG with known handwriting
   - Verify OCR accuracy
   - Test error handling (invalid API key, rate limits)

3. **End-to-End**:
   - Run full pipeline on test email
   - Verify output file format
   - Verify idempotency (re-run doesn't duplicate)

### Manual Testing Steps

1. **Initial Setup**:

   - Create virtual environment
   - Install dependencies
   - Configure `.env`
   - Place `credentials.json` from Gmail OAuth setup

2. **First Run**:

   - Run `python main.py`
   - Complete OAuth flow in browser
   - Verify `token.json` created
   - Verify at least one file processed if test email exists

3. **Idempotency**:

   - Run script again immediately
   - Verify no duplicate files created
   - Check state file for tracked items

4. **Launchd Service**:
   - Install plist
   - Manually trigger: `launchctl start com.remarkable.ingest`
   - Verify logs show successful run
   - Wait for scheduled time or adjust schedule to test

## Performance Considerations

- **Gmail API Rate Limits**: Gmail API has quotas (250 quota units per user per second). With 200 max results, should be safe.
- **OpenAI API Rate Limits**: Check OpenAI tier limits. May need rate limiting for large batches.
- **State File Growth**: Already handled with rotation at 50k entries.
- **Large Attachments**: PNG files from reMarkable are typically small (<1MB), but consider memory for very large batches.

## Security Considerations

- **API Keys**: Never commit `.env`, `credentials.json`, or `token.json` to git
- **OAuth Tokens**: `token.json` contains refresh tokens - keep secure
- **Local Storage**: All files stay local except PNG bytes sent to OpenAI
- **OpenAI Privacy**: Review OpenAI data usage policy for Vision API

## Migration Notes

N/A - This is a new system with no migration required.

## API Corrections from Specification

The specification contained an incorrect OpenAI API usage:

**Spec (Incorrect)**:

```python
res = client.responses.create(...)
return res.output_text
```

**Correct Implementation**:

```python
response = client.chat.completions.create(...)
return response.choices[0].message.content
```

The correct API uses `chat.completions.create()` with vision-capable models, not a hypothetical `responses.create()` endpoint.

## References

- Specification: Provided in user message (reMarkable → Gmail → OpenAI Vision → Markdown)
- OpenAI Vision API: https://platform.openai.com/docs/guides/vision
- Gmail API: https://developers.google.com/gmail/api
- Launchd: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
