#!/usr/bin/env python3
import argparse
import sys
import urllib.error
import urllib.request


def http_status(req):
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "ignore")
        except Exception:
            body = ""
        return exc.code, body[:300].strip()
    except Exception as exc:
        return None, str(exc)


def main():
    parser = argparse.ArgumentParser(description="Verify an OpenAI API key via /v1/models.")
    parser.add_argument("--key", help="OpenAI API key to verify (avoid shell history).")
    parser.add_argument("--stdin", action="store_true", help="Read API key from stdin.")
    parser.add_argument("--base-url", default="https://api.openai.com/v1", help="Override API base URL.")
    parser.add_argument("--project", default="", help="Optional OpenAI project id (proj_...).")
    args = parser.parse_args()

    if args.stdin:
        key = sys.stdin.read().strip()
    elif args.key:
        key = args.key.strip()
    else:
        parser.error("must provide --key or --stdin")

    if not key:
        print("error: key is empty", file=sys.stderr)
        return 2

    base = args.base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {key}"}
    if args.project:
        headers["OpenAI-Project"] = args.project

    req = urllib.request.Request(f"{base}/models", headers=headers, method="GET")
    status, body = http_status(req)
    if status == 200:
        print("ok: openai key valid (cli)")
        print(f"status: {status}")
        return 0

    print("error: openai key invalid (cli)")
    print(f"status: {status}")
    if body:
        print(f"response: {body}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
