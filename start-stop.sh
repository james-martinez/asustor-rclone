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
  echo "# Rclone Service Configuration" > "$SERVICE_CONF"
  echo "# ----------------------------------------------------------------" >> "$SERVICE_CONF"
  echo "# RCLONE_MODE Options:" >> "$SERVICE_CONF"
  echo "#   rcd       : Remote Control Daemon (Web GUI only)" >> "$SERVICE_CONF"
  echo "#   mount     : Mount remote as local disk (Requires FUSE)" >> "$SERVICE_CONF"
  echo "#   dlna      : Serve remote over DLNA" >> "$SERVICE_CONF"
  echo "#   http, webdav, ftp, sftp, nfs, s3, restic, docker" >> "$SERVICE_CONF"
  echo "# ----------------------------------------------------------------" >> "$SERVICE_CONF"
  
  echo "RCLONE_MODE=\"dlna\"" >> "$SERVICE_CONF"
  echo "" >> "$SERVICE_CONF"
  
  echo "# ENABLE_WEB_GUI: Set to 'true' to enable the Web UI (port 5572) alongside other modes." >> "$SERVICE_CONF"
  echo "# If 'false', the App Central icon will not connect when running in mount/serve modes." >> "$SERVICE_CONF"
  echo "ENABLE_WEB_GUI=\"false\"" >> "$SERVICE_CONF"
  echo "" >> "$SERVICE_CONF"

  echo "SERVE_REMOTE=\"/volume1/Media\"" >> "$SERVICE_CONF"
  echo "MOUNT_POINT=\"/volume1/RcloneMount\"" >> "$SERVICE_CONF"
  echo "SERVE_FLAGS=\"--read-only\"" >> "$SERVICE_CONF"
fi

# Load variables from config
. "$SERVICE_CONF"

# Set cache directory to a persistent location
export XDG_CACHE_HOME="$CONF_DIR/cache"
mkdir -p "$XDG_CACHE_HOME"

# --- 2. Construct Command Flags ---
# Always use the config file
COMMON_FLAGS="--config=$CONF_FILE"

# Construct GUI Flags (Only if enabled OR if mode is explicitly 'rcd')
GUI_FLAGS=""
if [ "$ENABLE_WEB_GUI" = "true" ] || [ "$RCLONE_MODE" = "rcd" ]; then
    GUI_FLAGS="--rc --rc-web-gui --rc-addr=0.0.0.0:$PORT --rc-user=$RC_USER --rc-pass=$RC_PASS --rc-web-gui-no-open-browser"
fi

case "$1" in
  start)
    echo "Starting $PKG_NAME in mode: $RCLONE_MODE..."

    if [ "$RCLONE_MODE" = "rcd" ]; then
      # Standard GUI Mode
      nohup $BIN_PATH rcd $COMMON_FLAGS $GUI_FLAGS > "$CONF_DIR/rclone.log" 2>&1 &
    
    elif [ "$RCLONE_MODE" = "mount" ]; then
      # Mount Mode
      if [ -z "$SERVE_REMOTE" ]; then echo "Error: SERVE_REMOTE missing"; exit 1; fi
      if [ ! -d "$MOUNT_POINT" ]; then mkdir -p "$MOUNT_POINT"; fi

      nohup $BIN_PATH mount "$SERVE_REMOTE" "$MOUNT_POINT" \
        --allow-other \
        --allow-non-empty \
        $SERVE_FLAGS \
        $COMMON_FLAGS $GUI_FLAGS > "$CONF_DIR/rclone.log" 2>&1 &

    elif [ -n "$RCLONE_MODE" ]; then
      # Universal Serve Mode
      if [ -z "$SERVE_REMOTE" ]; then echo "Error: SERVE_REMOTE missing"; exit 1; fi

      # Specific handling for DLNA to enforce port 7879 (and SSDP port 1900 UDP implicitly)
      EXTRA_FLAGS=""
      if [ "$RCLONE_MODE" = "dlna" ]; then
          EXTRA_FLAGS="--addr :7879"
      fi
      
      nohup $BIN_PATH serve $RCLONE_MODE "$SERVE_REMOTE" $SERVE_FLAGS $COMMON_FLAGS $GUI_FLAGS $EXTRA_FLAGS > "$CONF_DIR/rclone.log" 2>&1 &
    else
      echo "Unknown mode"
      exit 1
    fi

    echo $! > "$PID_FILE"
    echo "$PKG_NAME started with PID $(cat $PID_FILE)."
    ;;

  stop)
    echo "Stopping $PKG_NAME..."
    if [ -f "$SERVICE_CONF" ]; then . "$SERVICE_CONF"; fi

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
