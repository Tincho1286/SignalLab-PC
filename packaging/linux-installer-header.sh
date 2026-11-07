#!/bin/sh
# The payload is the complete Linux application, including its own interpreter.
set -eu
umask 077
parent=0
target=
headless=no
while [ "$#" -gt 0 ]; do
    case "$1" in
        --update) [ "$#" -ge 2 ] || exit 2; parent=$2; shift 2 ;;
        --target) [ "$#" -ge 2 ] || exit 2; target=$2; shift 2 ;;
        --headless) headless=yes; shift ;;
        *) printf '%s\n' 'Opción de instalador desconocida.' >&2; exit 2 ;;
    esac
done
case "$parent" in *[!0-9]*|'') exit 2 ;; esac
temporary=$(mktemp -d "${TMPDIR:-/tmp}/signallab-install.XXXXXXXX")
trap 'rm -rf -- "$temporary"' EXIT HUP INT TERM
payload_line=$(awk '/^__SIGNALLAB_PAYLOAD__$/ {print NR + 1; exit}' "$0")
[ -n "$payload_line" ] || exit 2
tail -n +"$payload_line" "$0" | tar -xzf - -C "$temporary" --no-same-owner
chmod u+x "$temporary/SignalLab-PC"
set -- --install-linux --source "$temporary" --update "$parent"
if [ -n "$target" ]; then set -- "$@" --target "$target"; fi
if [ "$headless" = yes ]; then set -- "$@" --headless; fi
"$temporary/SignalLab-PC" "$@"
exit 0
__SIGNALLAB_PAYLOAD__
