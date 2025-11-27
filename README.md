# Rclone for Asustor NAS (ARM64)

This project builds an `.apk` package for Asustor NAS devices running on ARM64 architecture. It packages the official [Rclone](https://rclone.org/) binary with a Web GUI enabled by default.

## Features
- **Rclone v1.72.0** (ARM64)
- **Web GUI** enabled on port `5572`
- **Multiple Modes:** Supports `mount`, `dlna`, `webdav`, `sftp`, `http`, `docker`, and more.
- **Daemon mode** via Asustor's App Central
- **Persistent Configuration** stored in `/volume1/RcloneConfig`

## Ports Used
- **5572 TCP**: Web GUI (configurable)
- **7879 TCP**: DLNA HTTP Streaming (when in `dlna` mode)
- **1900 UDP**: DLNA SSDP Discovery (when in `dlna` mode)

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
