#!/usr/bin/env python3
import argparse
import hashlib
import os
import subprocess
import sys


def read_value(args):
    if args.stdin:
        return sys.stdin.read().strip()
    if args.value is not None:
        return args.value.strip()
    return ""


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Set a Keychain generic password from stdin or --value.")
    parser.add_argument("--service", required=True, help="Keychain service name, e.g. mde-openai-api-key")
    parser.add_argument("--account", default=os.environ.get("USER", ""), help="Keychain account (default: $USER)")
    parser.add_argument("--stdin", action="store_true", help="Read secret from stdin")
    parser.add_argument("--value", help="Secret value (avoid shell history)")
    parser.add_argument("--no-verify", action="store_true", help="Skip read-back hash verification")
    args = parser.parse_args()

    value = read_value(args)
    if not value:
        parser.error("secret is empty; provide --stdin or --value")

    # Delete any existing entry first (ignore errors).
    subprocess.run(
        ["security", "delete-generic-password", "-a", args.account, "-s", args.service],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Add the new entry.
    subprocess.run(
        ["security", "add-generic-password", "-a", args.account, "-s", args.service, "-w", value],
        check=True,
    )

    if args.no_verify:
        print("ok: secret stored (verification skipped)")
        return 0

    try:
        stored = subprocess.check_output(
            ["security", "find-generic-password", "-a", args.account, "-s", args.service, "-w"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        print("error: failed to read back secret", file=sys.stderr)
        return 1

    if sha256(stored) == sha256(value):
        print("ok: secret stored and verified")
        return 0

    print("error: stored secret does not match input", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
