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

