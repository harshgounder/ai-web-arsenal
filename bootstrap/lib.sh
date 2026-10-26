#!/usr/bin/env bash
# lib.sh: shared helpers. Sourced by every generated script.
# Design rules:
#   - never run as root, refuse early
#   - never pipe curl to sh
#   - every install is idempotent (skip when already present)
#   - --dry-run prints what would happen and changes nothing
#   - everything is logged to bootstrap/logs/<script>-<timestamp>.log

DRY=${DRY:-0}
LOG_DIR="$HERE/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(basename "${BASH_SOURCE[1]:-bootstrap}")-$(date +%Y%m%d-%H%M%S).log"

c_reset=$'\033[0m'; c_ok=$'\033[32m'; c_warn=$'\033[33m'; c_err=$'\033[31m'; c_dim=$'\033[2m'

log()  { printf '%s\n' "$*" | tee -a "$LOG" >/dev/null; printf '%s\n' "$*"; }
ok()   { printf '%s  ok  %s%s\n' "$c_ok" "$*" "$c_reset"; log "OK   $*"; }
warn() { printf '%s warn %s%s\n' "$c_warn" "$*" "$c_reset"; log "WARN $*"; }
err()  { printf '%s fail %s%s\n' "$c_err" "$*" "$c_reset"; log "FAIL $*"; }

require_user() {
  if [ "$(id -u)" -eq 0 ]; then
    err "do not run this as root. run as your normal user; the script asks for sudo when needed."
    exit 1
  fi
}

require_arch() {
  if ! command -v pacman >/dev/null 2>&1; then
    err "pacman not found. this bootstrap is Arch first (Arch, CachyOS, EndeavourOS, Manjaro)."
    err "on another distro read docs/INSTALL-OTHER.md, which lists the same tools per channel."
    exit 1
  fi
}

aur_helper() {
  for h in paru yay pikaur; do
    if command -v "$h" >/dev/null 2>&1; then printf '%s' "$h"; return 0; fi
  done
  printf ''
}

have() { command -v "$1" >/dev/null 2>&1; }

run() {
  if [ "$DRY" = "1" ]; then
    printf '%s[dry-run] %s%s\n' "$c_dim" "$*" "$c_reset"
    log "DRY  $*"
    return 0
  fi
  log "RUN  $*"
  "$@"
}

p_pacman() {
  local pkg="$1"
  if pacman -Qi "$pkg" >/dev/null 2>&1; then ok "pacman: $pkg already installed"; return 0; fi
  run sudo pacman -S --needed --noconfirm "$pkg" || { err "pacman failed: $pkg"; return 1; }
  ok "pacman: $pkg"
}

p_aur() {
  local pkg="$1" helper
  helper="$(aur_helper)"
  if [ -z "$helper" ]; then
    err "no AUR helper (paru/yay/pikaur). install one first: sudo pacman -S --needed base-devel git; then build paru from AUR."
    return 1
  fi
  if pacman -Qi "${pkg%-bin}" >/dev/null 2>&1 || pacman -Qi "$pkg" >/dev/null 2>&1; then
    ok "aur: $pkg already installed"; return 0
  fi
  run "$helper" -S --needed --noconfirm "$pkg" || { err "aur failed: $pkg"; return 1; }
  ok "aur: $pkg"
}

p_pipx() {
  local pkg="$1"
  have pipx || { err "pipx missing, run 00-prereqs.sh first"; return 1; }
  if pipx list --short 2>/dev/null | grep -q "^${pkg} "; then ok "pipx: $pkg already installed"; return 0; fi
  run pipx install "$pkg" || { err "pipx failed: $pkg"; return 1; }
  ok "pipx: $pkg"
}

p_git() {
  local url="$1" dest="${2:-}"
  if [ -z "$dest" ]; then dest="$HOME/$(basename "$url" .git)"; fi
  if [ -d "$dest/.git" ]; then
    ok "git: $dest present"; return 0
  fi
  run git clone --depth 1 "$url" "$dest" || { err "clone failed: $url"; return 1; }
  ok "git: $url -> $dest"
}

summary() {
  local failed="${1:-0}"
  echo
  if [ "$failed" -eq 0 ]; then ok "done. log: $LOG"; else warn "$failed step(s) failed. log: $LOG"; fi
  printf '%snext: bash bootstrap/90-verify.sh%s\n' "$c_dim" "$c_reset"
}
