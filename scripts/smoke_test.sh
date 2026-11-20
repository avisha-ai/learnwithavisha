#!/usr/bin/env bash
# Smoke test for the LWA AI tutor endpoint. Run against a preview URL before every
# production deploy:
#   scripts/smoke_test.sh https://learnwithavisha-xxxx.vercel.app
# Passes when POST /api/ask returns HTTP 200 and JSON with a non-empty "text".
set -euo pipefail

url="${1:?usage: scripts/smoke_test.sh <deployment-url>}"
url="${url%/}"
question="${2:-What is fouling?}"

payload=$(python3 -c 'import json,sys; print(json.dumps({"question": sys.argv[1]}))' "$question")
body=$(mktemp); trap 'rm -f "$body"' EXIT
curl_args=(-sS -o "$body" -w '%{http_code}' --max-time 40 -X POST
           -H 'Content-Type: application/json' -d "$payload")
case "$url" in
  # Preview deployments sit behind Vercel Deployment Protection (plain curl gets 401);
  # `vercel curl` uses the CLI login to get through. Run from the repo root (linked project).
  *.vercel.app) code=$(npx --yes vercel curl "$url/api/ask" --yes -- "${curl_args[@]}" 2>/dev/null | tail -c 3) ;;
  *)            code=$(curl "${curl_args[@]}" "$url/api/ask") ;;
esac

python3 - "$code" "$body" <<'EOF'
import json, sys
code, path = sys.argv[1], sys.argv[2]
raw = open(path, encoding="utf-8", errors="replace").read()
try:
    data = json.loads(raw)
except ValueError:
    sys.exit(f"FAIL: HTTP {code}, response is not JSON: {raw[:200]!r}")
text = (data.get("text") or "").strip()
if code != "200" or not text:
    sys.exit(f"FAIL: HTTP {code}, error={data.get('error')!r}")
audio = "with audio" if data.get("audio") else "no audio"
print(f"PASS: HTTP 200, {len(text)} chars of text, {audio}")
print("  " + text[:160].replace("\n", " ") + ("…" if len(text) > 160 else ""))
EOF
