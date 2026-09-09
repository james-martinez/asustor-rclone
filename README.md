# Rclone for Asustor NAS (ARM64)

This project builds an `.apk` package for Asustor NAS devices running on ARM64 architecture. It packages the official [Rclone](https://rclone.org/) binary with an optional Web GUI (enabled via `ENABLE_WEB_GUI` in `service.conf`).

## Features
- **Rclone v1.75.1** (ARM64)
- **Web GUI** on port `5572`
- **Multiple Modes:** Supports `mount`, `dlna`, `webdav`, `sftp`, `http`, `docker`, and more.
- **Daemon mode** via Asustor's App Central
- **Persistent Configuration** stored in `/volume1/RcloneConfig`

## Ports Used
- **5572 TCP**: Web GUI (fixed, set in `start-stop.sh`)
- **7879 TCP**: DLNA HTTP Streaming (when in `dlna` mode)
- **1900 UDP**: DLNA SSDP Discovery (when in `dlna` mode)
- Other serve modes: configurable via `SERVE_FLAGS` (e.g. `--addr :8080`)

## Build Instructions

1. Ensure you have Python 3 installed.
2. Run the build script:
   ```bash
   python3 build_rclone_apk.py
   ```
3. The output file `rclone_1.75.1_arm64.apk` will be generated in the current directory.

## Installation

1. Log in to ADM.
2. Go to **App Central** > **Management** > **Manual Install**.
3. Upload the `.apk` file.
4. The app starts in **DLNA mode** serving `/volume1/Media`.

## First-Time Setup

The Web GUI is **disabled by default** (the App Central icon will not connect until you enable it). To configure your remotes:

1. Open **File Explorer** → `/volume1/RcloneConfig/` → edit `service.conf`.
2. Set `ENABLE_WEB_GUI="true"` (GUI alongside the current mode) or `RCLONE_MODE="rcd"` (GUI only).
3. Toggle the Rclone app **OFF** then **ON** in App Central.
4. Browse to `http://<NAS-IP>:5572` — login **admin / admin** (change these immediately in the Web UI).
5. Click **Configure** to set up your remotes (Google Drive, S3, WebDAV, ...). Remotes are stored in `/volume1/RcloneConfig/rclone.conf` and survive app upgrades.
6. Point `SERVE_REMOTE` at your new remote (see below) and restart the app.

## Configuration & Modes

By default, the app starts in **DLNA** mode serving `/volume1/Media`. To change this behavior (e.g., to Mount a drive or use the Web GUI), follow these steps:

1.  **Access the Config File:**
    * Open Asustor File Explorer.
    * Navigate to `/volume1/RcloneConfig/`.
    * Open `service.conf` with a text editor.

2.  **Edit the Mode:**
    Change the `RCLONE_MODE` variable to one of the following:
    * `rcd`     : Remote Control Daemon (Web GUI only)
    * `mount`   : Mount a remote as a local disk (Requires FUSE)
    * `dlna`    : Serve files to Smart TVs (Default)
    * `http`    : Serve files over HTTP
    * `webdav`  : Serve files over WebDAV
    * `ftp`     : Serve files over FTP
    * `sftp`    : Serve files over SFTP (SSH)
    * `docker`  : Serve remote for Docker's volume plugin API

3.  **Set the Target:**
    * Update `SERVE_REMOTE` to point to your configured remote (e.g., `MyGoogleDrive:`) or a local path (e.g., `/volume1/Media`).
    * *Note: You must first configure your remotes using the Web GUI (Mode: `rcd`) before you can serve/mount them.*

4.  **Apply Changes:**
    * Go to **App Central**.
    * Toggle the Rclone App **OFF** and then **ON** to restart the service with the new settings.

### Example: Mounting Google Drive
To mount a remote named `gdrive` to a local folder:
```bash
RCLONE_MODE="mount"
SERVE_REMOTE="gdrive:"
MOUNT_POINT="/volume1/RcloneMount"
```
*Note: `mount` mode requires FUSE, which is not installed by default on ADM.*

### Example: WebDAV Server
To serve local media over WebDAV on port 8080:
```bash
RCLONE_MODE="webdav"
SERVE_REMOTE="/volume1/Media"
SERVE_FLAGS="--addr :8080"
```

## Project Structure

- `build_rclone_apk.py`: Main builder script. Downloads rclone, fixes permissions, and creates the nested tarball structure required by ADM 2.0+.
- `config.json`: Asustor package metadata.
- `start-stop.sh`: Service control script used by ADM to handle startup logic and mode switching.
