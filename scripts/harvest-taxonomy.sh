#!/usr/bin/env bash
# harvest-taxonomy.sh: shallow clone the taxonomy sources that live in raw/taxonomy/.
#
# These were cloned by hand in an earlier session and no script existed, which meant a fresh clone could
# not rebuild taxonomy coverage at all. This is that script.
#
# Two of the six taxonomies are NOT cloned here, and that is a real gap rather than an omission:
#   WSTG and ASVS are read from ~/web-universe-work/universe-nodes.json, a sibling project outside this
#   repo. Without it, taxonomy-reconcile.py cannot rebuild the WSTG and ASVS rows, so the 624 of 706
#   figure is not reproducible from this repo alone. See RECHECK.md section 7.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

repos=(
  "bugcrowd/vulnerability-rating-taxonomy"
  "OWASP/API-Security"
  "OWASP/wstg"
  "OWASP/ASVS"
  "mitre-atlas/atlas-data"
)

mkdir -p raw/taxonomy
for r in "${repos[@]}"; do
  slug="${r//\//_}"
  dest="raw/taxonomy/$slug"
  if [ -d "$dest/.git" ]; then
    echo "SKIP  $slug (already present)"
    continue
  fi
  if git clone --depth 1 --quiet "https://github.com/$r.git" "$dest" 2>/dev/null; then
    sha=$(git -C "$dest" rev-parse HEAD 2>/dev/null || echo unknown)
    echo "$r $sha" >> raw/taxonomy/PROVENANCE.txt
    echo "OK    $slug $sha"
  else
    echo "FAIL  $slug (clone failed; the reconciler will report it missing)"
  fi
done

echo
echo "harvested into raw/taxonomy/. WSTG and ASVS rows additionally need"
echo "~/web-universe-work/universe-nodes.json, which this script cannot fetch."
