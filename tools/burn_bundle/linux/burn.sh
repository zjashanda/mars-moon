#!/usr/bin/env bash

set -euo pipefail

FIRMWARE_BIN=""
CTRL_PORT="/dev/ttyACM0"
BURN_PORT="/dev/ttyACM1"
CTRL_BAUD=115200
LOG_BAUD=115200
BURN_BAUD=1500000
CMD_DELAY_MS=300
PRE_BURN_WAIT_MS=1500
POST_POWER_ON_READ_SECONDS=8
POST_LOGLEVEL_READ_SECONDS=3
MAX_RETRY=3
VERIFY_ONLY=0
SKIP_LOGLEVEL=0

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BURN_TOOL="$ROOT_DIR/Uart_Burn_Tool"
LOG_FILE="$ROOT_DIR/burn.log"
TOOL_LOG="$ROOT_DIR/burn_tool.log"

usage() {
    cat <<'EOF'
Usage: burn.sh [options]

Options:
  -FirmwareBin <path>
  -CtrlPort <device>
  -BurnPort <device>
  -CtrlBaud <int>
  -LogBaud <int>
  -BurnBaud <int>
  -CmdDelayMs <int>
  -PreBurnWaitMs <int>
  -PostPowerOnReadSeconds <int>
  -PostLoglevelReadSeconds <int>
  -MaxRetry <int>
  -VerifyOnly
  -SkipLoglevel
  -h, --help
EOF
}

sleep_ms() {
    local ms="$1"
    python3 - "$ms" <<'PY'
import sys, time
time.sleep(max(float(sys.argv[1]), 0.0) / 1000.0)
PY
}

write_log() {
    local message="$1"
    local line
    line="[$(date '+%Y-%m-%d %H:%M:%S')] $message"
    echo "$line"
    printf '%s\n' "$line" >> "$LOG_FILE"
}

configure_port() {
    local port="$1"
    local baud="$2"
    stty -F "$port" "$baud" cs8 -cstopb -parenb -ixon -ixoff -icanon -echo min 0 time 1
}

wait_port() {
    local port="$1"
    local attempts="${2:-20}"
    local delay_ms="${3:-500}"
    local i
    for ((i = 0; i < attempts; i++)); do
        if [[ -e "$port" ]]; then
            write_log "Detected port $port"
            return 0
        fi
        sleep_ms "$delay_ms"
    done
    echo "Timeout waiting for port $port" >&2
    return 1
}

send_ctrl_sequence() {
    local commands=("$@")
    wait_port "$CTRL_PORT"
    configure_port "$CTRL_PORT" "$CTRL_BAUD"
    exec 3<>"$CTRL_PORT"
    write_log "Opened control port $CTRL_PORT"
    for cmd in "${commands[@]}"; do
        write_log "Send control command -> $CTRL_PORT : $cmd"
        printf '%s\r\n' "$cmd" >&3
        sleep_ms "$CMD_DELAY_MS"
    done
    exec 3>&-
    exec 3<&-
    write_log "Closed control port $CTRL_PORT"
}

resolve_firmware_path() {
    if [[ "$VERIFY_ONLY" -eq 1 ]]; then
        printf '\n'
        return 0
    fi

    if [[ ! -f "$BURN_TOOL" ]]; then
        echo "Burn tool does not exist: $BURN_TOOL" >&2
        return 1
    fi
    chmod +x "$BURN_TOOL" || true

    if [[ -n "$FIRMWARE_BIN" ]]; then
        python3 - "$FIRMWARE_BIN" <<'PY'
import os, sys
print(os.path.realpath(sys.argv[1]))
PY
        return 0
    fi

    shopt -s nullglob
    local bins=("$ROOT_DIR"/*.bin)
    shopt -u nullglob
    if [[ "${#bins[@]}" -eq 1 ]]; then
        write_log "Use default firmware: ${bins[0]}"
        printf '%s\n' "${bins[0]}"
        return 0
    fi
    if [[ "${#bins[@]}" -eq 0 ]]; then
        echo "No firmware bin found in $ROOT_DIR. Provide -FirmwareBin." >&2
        return 1
    fi

    echo "Multiple firmware bins found in $ROOT_DIR. Provide -FirmwareBin." >&2
    return 1
}

enter_burn_ready_state() {
    write_log "Prepare device for burn: power off -> boot on -> power on -> boot off"
    send_ctrl_sequence \
        "uut-switch1.off" \
        "uut-switch2.on" \
        "uut-switch1.on" \
        "uut-switch2.off"
    sleep_ms "$PRE_BURN_WAIT_MS"
}

restore_normal_power() {
    write_log "Restore normal boot: power off -> boot off -> power on"
    send_ctrl_sequence \
        "uut-switch1.off" \
        "uut-switch2.off" \
        "uut-switch1.on"
}

recover_after_failure() {
    if ! send_ctrl_sequence "uut-switch1.off" "uut-switch2.off"; then
        write_log "Recovery sequence also failed"
    fi
}

test_burn_success() {
    local exit_code="$1"
    if [[ "$exit_code" -ne 0 ]]; then
        write_log "Burn tool returned non-zero exit code: $exit_code"
        return 1
    fi

    local markers=(
        "CONNECT ROM AND DOWNLOAD RAM LOADER SUCCESS"
        "SEND MD5 COMMAND WITH RAM SUCCESS"
        "SEND END COMMAND SUCCESS"
    )
    local marker
    for marker in "${markers[@]}"; do
        if ! grep -Fq "$marker" "$TOOL_LOG"; then
            write_log "Missing success marker: $marker"
            return 1
        fi
    done
    return 0
}

invoke_burn_tool() {
    local fw_path="$1"
    wait_port "$BURN_PORT"
    : > "$TOOL_LOG"

    local args=(
        -b "$BURN_BAUD"
        -p "$BURN_PORT"
        -f "$fw_path"
        -m
        -d
        -a 0x0
        -i adaptive-duplex
        -s
    )

    write_log "Run burn tool: $BURN_TOOL ${args[*]}"
    set +e
    "$BURN_TOOL" "${args[@]}" 2>&1 | tee -a "$TOOL_LOG" | tee -a "$LOG_FILE"
    local exit_code="${PIPESTATUS[0]}"
    set -e

    if ! test_burn_success "$exit_code"; then
        echo "Burn tool failed. Check $TOOL_LOG and $LOG_FILE" >&2
        return 1
    fi

    write_log "Burn tool reported success"
}

capture_serial_window() {
    local port="$1"
    local baud="$2"
    local seconds="$3"
    local tmp_file
    tmp_file="$(mktemp)"
    configure_port "$port" "$baud"
    timeout "$seconds" cat "$port" > "$tmp_file" 2>/dev/null || true
    cat "$tmp_file" >> "$LOG_FILE"
    cat "$tmp_file"
    rm -f "$tmp_file"
}

test_boot_log_observed() {
    local serial_text="$1"
    python3 - "$serial_text" <<'PY'
import sys
text = sys.argv[1]
lines = []
for raw in text.replace("\r", "\n").split("\n"):
    item = raw.strip()
    if item and item != "loglevel 4":
        lines.append(item)
print("1" if lines else "0")
PY
}

verify_serial_after_burn() {
    wait_port "$BURN_PORT"
    write_log "Opened burn/log port $BURN_PORT for final power-on verification"
    write_log "----- device serial capture begin -----"

    restore_normal_power
    local serial_text
    serial_text="$(capture_serial_window "$BURN_PORT" "$LOG_BAUD" "$POST_POWER_ON_READ_SECONDS")"

    if [[ "$SKIP_LOGLEVEL" -eq 0 ]]; then
        configure_port "$BURN_PORT" "$LOG_BAUD"
        write_log "Send loglevel 4 to $BURN_PORT"
        printf 'loglevel 4\r\n' > "$BURN_PORT"
        local extra_text
        extra_text="$(capture_serial_window "$BURN_PORT" "$LOG_BAUD" "$POST_LOGLEVEL_READ_SECONDS")"
        serial_text+=$'\n'"$extra_text"
    fi

    write_log "----- device serial capture end -----"

    if [[ "$(test_boot_log_observed "$serial_text")" != "1" ]]; then
        echo "No boot log observed on $BURN_PORT after final power on" >&2
        return 1
    fi

    local markers=("VER:" "SDK:" "version" "volume" "work mode" "curtain" "root:/" "reset=")
    local marker
    for marker in "${markers[@]}"; do
        if grep -Fqi "$marker" <<< "$serial_text"; then
            write_log "Observed boot marker on $BURN_PORT: $marker"
            return 0
        fi
    done

    write_log "Observed serial output on $BURN_PORT after final power on"
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -FirmwareBin) FIRMWARE_BIN="$2"; shift 2 ;;
        -CtrlPort) CTRL_PORT="$2"; shift 2 ;;
        -BurnPort) BURN_PORT="$2"; shift 2 ;;
        -CtrlBaud) CTRL_BAUD="$2"; shift 2 ;;
        -LogBaud) LOG_BAUD="$2"; shift 2 ;;
        -BurnBaud) BURN_BAUD="$2"; shift 2 ;;
        -CmdDelayMs) CMD_DELAY_MS="$2"; shift 2 ;;
        -PreBurnWaitMs) PRE_BURN_WAIT_MS="$2"; shift 2 ;;
        -PostPowerOnReadSeconds) POST_POWER_ON_READ_SECONDS="$2"; shift 2 ;;
        -PostLoglevelReadSeconds) POST_LOGLEVEL_READ_SECONDS="$2"; shift 2 ;;
        -MaxRetry) MAX_RETRY="$2"; shift 2 ;;
        -VerifyOnly) VERIFY_ONLY=1; shift ;;
        -SkipLoglevel) SKIP_LOGLEVEL=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *)
            echo "Unknown argument: $1" >&2
            usage
            exit 1
            ;;
    esac
done

if [[ "$MAX_RETRY" -lt 1 ]]; then
    MAX_RETRY=1
fi

: > "$LOG_FILE"
: > "$TOOL_LOG"

FW_PATH="$(resolve_firmware_path)"
write_log "========== burn flow start =========="
write_log "CtrlPort=$CTRL_PORT CtrlBaud=$CTRL_BAUD BurnPort=$BURN_PORT LogBaud=$LOG_BAUD BurnBaud=$BURN_BAUD VerifyOnly=$VERIFY_ONLY"

if [[ "$VERIFY_ONLY" -eq 1 ]]; then
    verify_serial_after_burn
    write_log "Verification-only flow completed"
    exit 0
fi

attempt=0
while [[ "$attempt" -lt "$MAX_RETRY" ]]; do
    attempt=$((attempt + 1))
    if {
        write_log "Burn attempt $attempt/$MAX_RETRY"
        enter_burn_ready_state
        invoke_burn_tool "$FW_PATH"
        verify_serial_after_burn
    }; then
        write_log "Burn flow completed"
        exit 0
    fi

    write_log "Attempt failed"
    if [[ "$attempt" -ge "$MAX_RETRY" ]]; then
        write_log "Burn flow failed"
        exit 1
    fi
    recover_after_failure
    sleep 2
done

write_log "Burn flow failed"
exit 1
