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

