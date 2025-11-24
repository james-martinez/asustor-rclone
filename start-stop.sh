#!/bin/sh

# Define paths
PKG_NAME="rclone"
INSTALL_DIR="/usr/local/AppCentral/$PKG_NAME"
BIN_PATH="$INSTALL_DIR/bin/rclone"
PID_FILE="/var/run/$PKG_NAME.pid"
CONF_DIR="/volume1/RcloneConfig"
CONF_FILE="$CONF_DIR/rclone.conf"
SERVICE_CONF="$CONF_DIR/service.conf"

# Default Settings
RC_USER="admin"
RC_PASS="admin"
PORT="5572"

# --- 1. Load or Create Service Configuration ---
if [ ! -d "$CONF_DIR" ]; then
  mkdir -p "$CONF_DIR"
fi

if [ ! -f "$SERVICE_CONF" ]; then
  # Create default config if missing with ALL features listed
  echo "# Rclone Service Configuration" > "$SERVICE_CONF"
  echo "# ----------------------------------------------------------------" >> "$SERVICE_CONF"
  echo "# RCLONE_MODE Options:" >> "$SERVICE_CONF"
  echo "#   rcd       : Remote Control Daemon (Web GUI only)" >> "$SERVICE_CONF"
  echo "#   mount     : Mount remote as local disk (Requires FUSE)" >> "$SERVICE_CONF"
  echo "#" >> "$SERVICE_CONF"
  echo "#   --- SERVING PROTOCOLS ---" >> "$SERVICE_CONF"
  echo "#   dlna      : Serve remote over DLNA (Smart TVs)" >> "$SERVICE_CONF"
  echo "#   http      : Serve remote over HTTP" >> "$SERVICE_CONF"
  echo "#   webdav    : Serve remote over WebDAV" >> "$SERVICE_CONF"
  echo "#   ftp       : Serve remote over FTP" >> "$SERVICE_CONF"
  echo "#   sftp      : Serve remote over SFTP (SSH)" >> "$SERVICE_CONF"
  echo "#   nfs       : Serve remote over NFS (Requires kernel support)" >> "$SERVICE_CONF"
  echo "#   s3        : Serve remote as an S3 compatible API" >> "$SERVICE_CONF"
  echo "#   restic    : Serve remote as a Restic REST API" >> "$SERVICE_CONF"
  echo "#   docker    : Serve remote for Docker's volume plugin API" >> "$SERVICE_CONF"
  echo "# ----------------------------------------------------------------" >> "$SERVICE_CONF"
  
  # Set default mode (Requested: dlna)
  echo "RCLONE_MODE=\"dlna\"" >> "$SERVICE_CONF"
  echo "" >> "$SERVICE_CONF"
  
  echo "# SERVE_REMOTE: The remote name (e.g. MyRemote:) or local path (/volume1/Media)" >> "$SERVICE_CONF"
  echo "SERVE_REMOTE=\"/volume1/Media\"" >> "$SERVICE_CONF"
  echo "" >> "$SERVICE_CONF"
  
  echo "# MOUNT_POINT: Local path for 'mount' mode only" >> "$SERVICE_CONF"
  echo "MOUNT_POINT=\"/volume1/RcloneMount\"" >> "$SERVICE_CONF"
  echo "" >> "$SERVICE_CONF"
  
  echo "# EXTRA_FLAGS: Specific flags (e.g. --addr :8080, --vfs-cache-mode full, --read-only)" >> "$SERVICE_CONF"
  echo "SERVE_FLAGS=\"--read-only\"" >> "$SERVICE_CONF"
fi

# Load variables from config
. "$SERVICE_CONF"

# --- 2. Construct Command ---
# We ALWAYS enable the Remote Control (--rc) so the App Central icon/GUI works.
RC_FLAGS="--rc --rc-web-gui --rc-addr=0.0.0.0:$PORT --rc-user=$RC_USER --rc-pass=$RC_PASS --rc-web-gui-no-open-browser --config=$CONF_FILE"

case "$1" in
  start)
    echo "Starting $PKG_NAME in mode: $RCLONE_MODE..."

    if [ "$RCLONE_MODE" = "rcd" ]; then
      # Standard GUI Mode
      $BIN_PATH rcd $RC_FLAGS > /dev/null 2>&1 &
    
    elif [ "$RCLONE_MODE" = "mount" ]; then
      # Mount Mode
      if [ -z "$SERVE_REMOTE" ]; then
        echo "Error: SERVE_REMOTE must be set in service.conf for mode $RCLONE_MODE"
        exit 1
      fi
      
      if [ ! -d "$MOUNT_POINT" ]; then
        mkdir -p "$MOUNT_POINT"
      fi

      $BIN_PATH mount "$SERVE_REMOTE" "$MOUNT_POINT" \
        --allow-other \
        --allow-non-empty \
        $SERVE_FLAGS \
        $RC_FLAGS > /dev/null 2>&1 &

    elif [ -n "$RCLONE_MODE" ]; then
      # Universal Serve Mode (Handles http, ftp, s3, dlna, nfs, etc.)
      if [ -z "$SERVE_REMOTE" ]; then
        echo "Error: SERVE_REMOTE must be set in service.conf for mode $RCLONE_MODE"
        exit 1
      fi
      
      # Runs: rclone serve <PROTOCOL> <REMOTE> <FLAGS>
      $BIN_PATH serve $RCLONE_MODE "$SERVE_REMOTE" $SERVE_FLAGS $RC_FLAGS > /dev/null 2>&1 &
    else
      echo "Unknown mode"
      exit 1
    fi

    echo $! > "$PID_FILE"
    echo "$PKG_NAME started with PID $(cat $PID_FILE)."
    ;;

  stop)
    echo "Stopping $PKG_NAME..."
    
    # Reload config to safely unmount if needed
    if [ -f "$SERVICE_CONF" ]; then
        . "$SERVICE_CONF"
    fi

    if [ "$RCLONE_MODE" = "mount" ] && [ -n "$MOUNT_POINT" ]; then
        umount "$MOUNT_POINT" || fusermount -u "$MOUNT_POINT"
    fi

    if [ -f "$PID_FILE" ]; then
      kill $(cat "$PID_FILE")
      rm "$PID_FILE"
    else
      killall rclone
    fi
    echo "$PKG_NAME stopped."
    ;;

  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac

exit 0