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
