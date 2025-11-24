#!/bin/sh

# Define paths
PKG_NAME="rclone"
INSTALL_DIR="/usr/local/AppCentral/$PKG_NAME"
BIN_PATH="$INSTALL_DIR/bin/rclone"
PID_FILE="/var/run/$PKG_NAME.pid"
CONF_DIR="/volume1/RcloneConfig"
CONF_FILE="$CONF_DIR/rclone.conf"

# Rclone Web GUI settings
RC_USER="admin"
RC_PASS="admin"
PORT="5572"

case "$1" in
  start)
    echo "Starting $PKG_NAME..."
    
    # Ensure config directory exists
    if [ ! -d "$CONF_DIR" ]; then
      mkdir -p "$CONF_DIR"
    fi

    # Start rclone in background using shell '&' operator
    # Output is discarded to /dev/null to avoid filling disk space
    $BIN_PATH rcd \
      --rc-web-gui \
      --rc-addr=0.0.0.0:$PORT \
      --rc-user=$RC_USER \
      --rc-pass=$RC_PASS \
      --config=$CONF_FILE \
      --rc-web-gui-no-open-browser \
      > /dev/null 2>&1 &
      
    # Capture the Process ID (PID) of the last background command
    echo $! > "$PID_FILE"
      
    echo "$PKG_NAME started with PID $(cat $PID_FILE)."
    ;;

  stop)
    echo "Stopping $PKG_NAME..."
    if [ -f "$PID_FILE" ]; then
      kill $(cat "$PID_FILE")
      rm "$PID_FILE"
    else
      # Fallback if PID file is missing
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
