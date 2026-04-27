#!/usr/bin/env bash
set -euo pipefail

DEVICE="${1:-/dev/video0}"
FOCUS="${FOCUS:-144}"
EXPOSURE="${EXPOSURE:-157}"
WHITE_BALANCE="${WHITE_BALANCE:-4600}"
POWER_LINE="${POWER_LINE:-1}"

echo "Locking camera controls on ${DEVICE}"
echo "Focus=${FOCUS} Exposure=${EXPOSURE} WhiteBalance=${WHITE_BALANCE} PowerLine=${POWER_LINE}"

v4l2-ctl -d "${DEVICE}" \
  --set-ctrl=focus_automatic_continuous=0 \
  --set-ctrl=focus_absolute="${FOCUS}" \
  --set-ctrl=auto_exposure=1 \
  --set-ctrl=exposure_dynamic_framerate=0 \
  --set-ctrl=exposure_time_absolute="${EXPOSURE}" \
  --set-ctrl=white_balance_automatic=0 \
  --set-ctrl=white_balance_temperature="${WHITE_BALANCE}" \
  --set-ctrl=power_line_frequency="${POWER_LINE}"

echo
v4l2-ctl -d "${DEVICE}" --get-ctrl=focus_automatic_continuous,focus_absolute,auto_exposure,exposure_time_absolute,white_balance_automatic,white_balance_temperature,power_line_frequency
