# reMarkable Ingest

Automatically converts reMarkable PNG exports from Gmail to Markdown using OpenAI Vision API.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and configure
3. Set up Gmail OAuth: Place `credentials.json` in project root
4. Run first time: `python main.py` (will open browser for auth)
5. Install launchd service: See launchd/README.md

## Quick Start (End-to-End Testing)

See **[TESTING.md](TESTING.md)** for complete step-by-step guide.

Quick version:

1. **Verify setup:**

   ```bash
   cd ~/dev/remarkable_ingest
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run:**

   ```bash
   python main.py
   ```

   - First run will open browser for Gmail OAuth
   - Processes emails with "Remarkable" label + PNG attachments
   - Saves to `~/Documents/remarkable-md/`

3. **Check output:**
   ```bash
   ls -la ~/Documents/remarkable-md/
   ```

## Manual Testing

### Normal Run (with deduplication)

To manually trigger a pull/run:

```bash
cd ~/dev/remarkable_ingest
source .venv/bin/activate
python main.py
```

Or use the convenience script:

```bash
./run.sh
```

This will skip attachments that have already been processed (based on `application_state.json` in the output directory).

### Force Reprocessing

To reprocess all attachments (bypassing deduplication), use the `--force` flag:

```bash
python3 main.py --force
```

**Note**: This is useful for testing or reprocessing after code changes. The `--force` flag will:

- Process all attachments, even if previously seen
- Still mark them as seen after processing (so future runs won't reprocess them)
- **Automatic runs via launchd do NOT use `--force`**, so deduplication is always active in scheduled runs

## Weekly Summary Generation

The project includes a weekly summary feature that automatically generates summaries of your markdown files every Sunday at 9:00 AM.

### Setup

1. Add to your `.env` file:

   ```env
   WEEKLY_SUMMARY_PROMPT="Your prompt here for GPT to generate the summary"
   WEEKLY_SUMMARY_EMAIL=jim.liu90@gmail.com
   WEEKLY_SUMMARY_MODEL=gpt-5
   ```

2. Install the launchd service (see `launchd/README.md`)

### Manual Run

```bash
cd ~/dev/remarkable_ingest
source .venv/bin/activate
python weekly_summary.py
```

Use `--dry-run` to see what would happen without actually generating:

```bash
python weekly_summary.py --dry-run
```

### How It Works

- Generates summary for the past 7 days ending on the most recent Sunday at 9:00 AM
- Finds all markdown files in `OUTPUT_DIR` (including `review/` and `general/` subdirectories)
- Sends files to GPT-5o with your custom prompt
- Saves summary to `{OUTPUT_DIR}/generated-weeklies/YYYY-MM-DD-weekly.md`
- Emails the summary as an attachment to your configured email address
- Skips generation if summary already exists for that week (use `--force` to regenerate)

**Note**: If your computer is asleep on Sunday at 9am, the job will run when it wakes up (may be late, but will still generate for the correct week).
