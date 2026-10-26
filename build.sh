#!/usr/bin/env bash
# Build the static site into _site/ for Cloudflare Pages.
# Cloudflare Pages: build command `bash build.sh`, output directory `_site`.
set -euo pipefail
cd "$(dirname "$0")"

MINT_VERSION="${MINT_VERSION:-4.2.1128}"

python3 tools/build_site.py

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
npx --yes "mint@${MINT_VERSION}" export --output "$tmp/export.zip"

rm -rf _site
mkdir _site
unzip -q "$tmp/export.zip" -d _site
# Drop the export's local-viewer helpers; Cloudflare serves the files directly.
rm -f _site/serve.js "_site/Start Docs.command" "_site/Start Docs.bat" _site/README.md
cp _headers _site/_headers
# Raw machine-readable files for agents and tooling.
cp shipping.md openapi.yaml _site/
mkdir -p _site/openapi && cp openapi/*.yaml _site/openapi/
mkdir -p _site/graphql && cp graphql/schema.graphql graphql/operations.json _site/graphql/
echo "built _site ($(find _site -type f | wc -l | tr -d ' ') files)"
