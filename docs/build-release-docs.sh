#!/usr/bin/env bash
# Build release documentation artifacts (PDF, EPUB, plain text) from the
# Markdown sources. Requires pandoc, weasyprint (PDF engine), and griffe2md.
# Usage: docs/build-release-docs.sh [output-dir]
set -euo pipefail

out="${1:-docs-dist}"
mkdir -p "$out"

pages=(index quick-start creating-bots api-reference)

tmp_en="$(mktemp -d)"
tmp_ru="$(mktemp -d)"
trap 'rm -rf "$tmp_en" "$tmp_ru"' EXIT

griffe2md lxmfy 2>/dev/null \
    | sed -E 's/\[([^]]+)\]\(#[^)]*\)/\1/g' \
    > "$tmp_en/90-api-generated.md"
cp "$tmp_en/90-api-generated.md" "$tmp_ru/90-api-generated.md"

prepare() {
    local lang_dir="$1" tmp="$2" i
    for i in "${!pages[@]}"; do
        src="docs/${lang_dir:+$lang_dir/}${pages[$i]}.md"
        sed '/^:::/d' "$src" > "$tmp/$(printf '%02d' "$i")-${pages[$i]}.md"
    done
}

render() {
    local tmp="$1" base="$out/lxmfy-docs-$2" title="$3"
    pandoc "$tmp"/*.md --toc --metadata title="$title" -o "$base.epub"
    pandoc "$tmp"/*.md --toc --metadata title="$title" \
        --pdf-engine=weasyprint -o "$base.pdf"
    pandoc "$tmp"/*.md --toc --metadata title="$title" -t plain \
        -o "$base.txt"
}

prepare "" "$tmp_en"
prepare "ru" "$tmp_ru"

render "$tmp_en" en "LXMFy Documentation"
render "$tmp_ru" ru "Документация LXMFy"

ls -lh "$out"
