# End-to-End Testing Guide

Complete step-by-step guide to get reMarkable ingest running and test it end-to-end.

## Prerequisites Check

Let's verify what's already set up:

```bash
cd ~/Dev/monorepo/dev/remarkable_ingest

# Check if credentials.json exists (Gmail OAuth)
ls -la credentials.json

# Check if .env exists with your API key
ls -la .env

# Check Python version (should be 3.8+)
python3 --version
```

## Step 1: Verify Virtual Environment

```bash
cd ~/Dev/monorepo/dev/remarkable_ingest

# Create virtual environment if it doesn't exist
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Verify you're in the venv (prompt should show (.venv))
which python  # Should point to .venv/bin/python
```

## Step 2: Install Dependencies

```bash
# Make sure venv is activated (you should see (.venv) in prompt)
pip install -r requirements.txt

# Verify key packages are installed
pip list | grep -E "(openai|google-api|dotenv)"
```

## Step 3: Verify Configuration Files

### Check .env file:
```bash
cat .env
```

Should contain:
- `OPENAI_API_KEY=sk-proj-...` (your actual key)
- `OPENAI_MODEL=gpt-5-mini`
- `GMAIL_LABEL=Remarkable`
- `SEARCH_WINDOW_DAYS=14`
- `OUTPUT_DIR=~/Documents/remarkable-md`

### Check credentials.json:
```bash
# Should exist and be valid JSON
python3 -m json.tool credentials.json > /dev/null && echo "✓ credentials.json is valid"
```

## Step 4: Test Gmail Connection

Before running end-to-end, let's verify Gmail API works:

```bash
cd ~/Dev/monorepo/dev/remarkable_ingest
source .venv/bin/activate

# This will open browser for OAuth on first run
python -c "
from providers.gmail_client import get_gmail_service
service = get_gmail_service()
print('✓ Gmail connection successful')
print('✓ Service object created:', type(service))
"
```

**First time:** Browser will open for OAuth authorization. Grant permissions and you should see `token.json` created.

## Step 5: Test OpenAI Connection

```bash
source .venv/bin/activate

python -c "
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', 'gpt-5-mini')
print(f'✓ OPENAI_API_KEY: {\"Set\" if api_key else \"Missing\"} ({len(api_key) if api_key else 0} chars)')
print(f'✓ OPENAI_MODEL: {model}')
"
```

## Step 6: Prepare Test Data

### Option A: Use Existing Gmail with "Remarkable" Label

1. Go to Gmail
2. Create a label called "Remarkable" (if it doesn't exist)
3. Find an email with a PNG attachment from the last 14 days
4. Apply the "Remarkable" label to it

### Option B: Send Test Email

1. Send yourself an email with a PNG attachment (can be any PNG, even a screenshot)
2. In Gmail, apply the "Remarkable" label
3. Wait a moment for Gmail to index it

## Step 7: Run End-to-End Test

```bash
cd ~/Dev/monorepo/dev/remarkable_ingest
source .venv/bin/activate

# Run the full pipeline
python main.py
```

### Expected Output:

```
Wrote /Users/jim/Documents/remarkable-md/filename__20251101_123456.md
Done. processed_messages=1 saved_files=1
```

### If you see no output:
- Check if there are emails matching the criteria (label "Remarkable", PNG attachment, last 14 days)
- Verify Gmail search: The script searches for `(label:Remarkable) (has:attachment) filename:png newer_than:14d`
- Check console output for any error messages

## Step 8: Verify Output

```bash
# Check output directory
ls -la ~/Documents/remarkable-md/

# View a generated file
cat ~/Documents/remarkable-md/*.md | head -20
```

Expected file format:
```markdown
---
title: "filename"
source: "Gmail/reMarkable"
---

[OCR'd markdown content here]
```

## Step 9: Test Idempotency

Run the script again immediately:

```bash
python main.py
```

Expected: Should not create duplicate files (should say `saved_files=0` if no new emails)

## Troubleshooting

### "OPENAI_API_KEY not set"
- Check `.env` file exists and has `OPENAI_API_KEY=sk-...`
- Verify you're in the project directory when running

### "credentials.json not found"
- File should be in project root: `~/Dev/monorepo/dev/remarkable_ingest/credentials.json`
- Verify it's valid JSON: `python3 -m json.tool credentials.json`

### "No module named 'openai'"
- Virtual environment not activated: `source .venv/bin/activate`
- Dependencies not installed: `pip install -r requirements.txt`

### "No messages found" or `saved_files=0`
- Verify email has "Remarkable" label applied
- Check email is within last 14 days
- Verify attachment is PNG (lowercase `.png`)
- Try searching Gmail directly: `label:Remarkable has:attachment filename:png newer_than:14d`

### Gmail OAuth errors
- Delete `token.json` and try again: `rm token.json`
- Check browser console if OAuth page shows errors
- Verify `credentials.json` is valid

### OpenAI API errors
- Check API key is valid and has credits
- Verify model name: `gpt-5-mini` (check OpenAI docs if changed)
- Check rate limits if you see 429 errors

## Quick Health Check Script

Run this to verify everything is ready:

```bash
cd ~/Dev/monorepo/dev/remarkable_ingest
source .venv/bin/activate

python3 << 'EOF'
import os
import sys
from pathlib import Path

print("=== Health Check ===\n")

# Check .env
env_path = Path(".env")
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    print(f"✓ .env file exists")
    print(f"  OPENAI_API_KEY: {'Set' if api_key else 'Missing'}")
    print(f"  OPENAI_MODEL: {model}")
else:
    print("✗ .env file missing")
    sys.exit(1)

# Check credentials.json
cred_path = Path("credentials.json")
if cred_path.exists():
    import json
    try:
        with open(cred_path) as f:
            json.load(f)
        print("✓ credentials.json exists and is valid JSON")
    except:
        print("✗ credentials.json is invalid JSON")
        sys.exit(1)
else:
    print("✗ credentials.json missing")
    sys.exit(1)

# Check token.json (optional - created on first run)
token_path = Path("token.json")
if token_path.exists():
    print("✓ token.json exists (Gmail already authorized)")
else:
    print("⚠ token.json missing (will be created on first run)")

# Check imports
try:
    from providers.gmail_client import get_gmail_service
    from providers.ocr_handwriting_openai import ocr_png_to_markdown_openai
    from utils.files import sanitize_filename, ensure_dir
    from utils.md import prepend_front_matter
    from utils.state import seen, remember
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

print("\n✓ All checks passed! Ready for end-to-end testing.")
EOF
```

## Success Criteria

You've successfully completed end-to-end testing when:

- [ ] Script runs without errors
- [ ] At least one markdown file is created in output directory
- [ ] Generated file has proper front matter (title, source)
- [ ] File contains OCR'd content (not empty)
- [ ] Running script again doesn't create duplicates (idempotent)
- [ ] State file exists: `~/remarkable-ingest/state.json`

## Next Steps

Once testing is successful:
1. Review output quality - adjust OCR prompt if needed
2. Set up launchd service for automatic runs: `launchd/README.md`
3. Adjust schedule if needed (9am, 3pm, 9pm)
4. Monitor logs for issues

