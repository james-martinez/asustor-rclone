# Rclone for Asustor NAS (ARM64)

This project builds an `.apk` package for Asustor NAS devices running on ARM64 architecture. It packages the official [Rclone](https://rclone.org/) binary with a Web GUI enabled by default.

## Features
- **Rclone v1.72.0** (ARM64)
- **Web GUI** enabled on port `5572`
- **Daemon mode** via Asustor's App Central
- **Persistent Configuration** stored in `/volume1/RcloneConfig`

## Build Instructions

1. Ensure you have Python 3 installed.
2. Run the build script:
   ```bash
   python3 build_rclone_apk.py
   ```
3. The output file `rclone_v1.72.0_arm64.apk` will be generated in the current directory.

## Installation

1. Log in to ADM.
2. Go to **App Central** > **Management** > **Manual Install**.
3. Upload the `.apk` file.
4. Once installed, click the icon to open the Web UI.
5. **Default Credentials:** `admin` / `admin` (Change these immediately in the Rclone Web UI settings).
