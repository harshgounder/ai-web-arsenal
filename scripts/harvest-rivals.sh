#!/usr/bin/env bash
# harvest-rivals.sh: shallow clone every rival collection in data/rivals.json.
# Frozen instrument. Re-runnable. Writes into raw/rivals/<slug>/.
# Provenance: each repo is cloned with depth 1 so the on-disk copy is one commit,
# and the commit sha is recorded next to it for later diffing.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
mkdir -p raw/rivals

python3 - <<'PY' > /tmp/rival-repos.txt
import json
for r in json.load(open("data/rivals.json")):
    print(r["repo"].replace("/", "__"))
PY

while read -r slug; do
  dest="raw/rivals/$slug"
  if [ -d "$dest/.git" ]; then
    echo "SKIP  $slug (already present)"
    continue
  fi
  rm -rf "$dest"
  if timeout 120 git clone --depth 1 --quiet "https://github.com/${slug/__//}.git" "$dest" 2>/tmp/clone.err; then
    sha=$(git -C "$dest" rev-parse HEAD 2>/dev/null)
    date=$(git -C "$dest" log -1 --format=%cI 2>/dev/null)
    printf '%s\t%s\t%s\n' "$slug" "$sha" "$date" >> raw/rivals/CLONES.tsv
    echo "OK    $slug  ${sha:0:8}"
  else
    echo "FAIL  $slug  $(head -1 /tmp/clone.err)"
  fi
done < /tmp/rival-repos.txt
