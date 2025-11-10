# Launchd Service Setup

## Installation

1. Copy the plist to LaunchAgents:

   ```bash
   cp com.remarkable.ingest.plist ~/Library/LaunchAgents/
   ```

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

- Service output: `~/dev/remarkable_ingest/run.log`
- Standard output: `~/dev/remarkable_ingest/stdout.log`
- Standard error: `~/dev/remarkable_ingest/stderr.log`

## Schedule

Runs every 3 hours:

- 12:00 AM (midnight)
- 3:00 AM
- 6:00 AM
- 9:00 AM
- 12:00 PM (noon)
- 3:00 PM
- 6:00 PM
- 9:00 PM
- On system load (RunAtLoad)

**Note**: Times are in system timezone. Ensure your Mac is set to PT if you want Pacific Time.

## Weekly Summary Service

The weekly summary service (`com.remarkable.weekly.plist`) generates a weekly summary every Sunday at 9:00 AM.

### Installation

1. Copy the plist to LaunchAgents:

   ```bash
   cp com.remarkable.weekly.plist ~/Library/LaunchAgents/
   ```

2. Load the service:

   ```bash
   launchctl load ~/Library/LaunchAgents/com.remarkable.weekly.plist
   ```

3. Verify it's loaded:
   ```bash
   launchctl list | grep remarkable.weekly
   ```

### Schedule

- Runs every Sunday at 9:00 AM
- If computer is asleep, runs when it wakes up (may be late)
- Uses fixed 7-day window ending on most recent Sunday 9am
- Skips if summary already exists for that week (use `--force` to regenerate)

### Manual Run

To test the service manually:

```bash
cd ~/dev/remarkable_ingest
source .venv/bin/activate
python weekly_summary.py
```

Or with dry-run to see what would happen:

```bash
python weekly_summary.py --dry-run
```

### Logs

- Standard output: `~/dev/remarkable_ingest/weekly_stdout.log`
- Standard error: `~/dev/remarkable_ingest/weekly_stderr.log`

### Configuration

Requires the following environment variables in `.env`:

- `WEEKLY_SUMMARY_PROMPT` - Your prompt for GPT to generate the summary
- `WEEKLY_SUMMARY_EMAIL` - Email address to send summary to (default: jim.liu90@gmail.com)
- `WEEKLY_SUMMARY_MODEL` - OpenAI model to use (default: gpt-5)

