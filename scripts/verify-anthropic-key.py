#!/usr/bin/env python3
import os
import sys
import urllib.error
import urllib.request
import subprocess


def read_key():
    prefer_keychain = os.environ.get("MDE_SECRET_OVERRIDE", "1") == "1"
    env_key = os.environ.get("ANTHROPIC_API_KEY", "")
    keychain_key = ""
    try:
        keychain_key = subprocess.check_output(
            ["security", "find-generic-password", "-a", os.environ["USER"], "-s", "mde-anthropic-api-key", "-w"],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        keychain_key = ""

    if prefer_keychain and keychain_key:
        return keychain_key, "keychain"
    if env_key:
        return env_key, "env"
    if keychain_key:
        return keychain_key, "keychain"
    return "", ""


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
    key, source = read_key()
    if not key:
        print("error: ANTHROPIC_API_KEY missing (env or keychain: mde-anthropic-api-key)", file=sys.stderr)
        return 2

    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1").rstrip("/")
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    req = urllib.request.Request(f"{base}/models", headers=headers, method="GET")
    status, body = http_status(req)
    if status == 200:
        print(f"ok: anthropic key valid ({source})")
        print(f"status: {status}")
        return 0

    print(f"error: anthropic key invalid ({source})")
    print(f"status: {status}")
    if body:
        print(f"response: {body}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
