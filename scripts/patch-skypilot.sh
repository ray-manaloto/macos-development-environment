#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

python_bin=""
if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  log "python3 not available; cannot patch skypilot templates."
  exit 1
fi

uv_tools_dir="${UV_TOOL_DIR:-}"
if [[ -z "$uv_tools_dir" ]]; then
  if command -v uv >/dev/null 2>&1; then
    uv_tools_dir="$(uv tool dir 2>/dev/null || true)"
  fi
fi
if [[ -z "$uv_tools_dir" ]]; then
  uv_tools_dir="$HOME/.local/share/uv/tools"
fi

skypilot_root="${SKYPILOT_TOOL_DIR:-$uv_tools_dir/skypilot}"
if [[ ! -d "$skypilot_root" ]]; then
  log "skypilot tool directory not found at $skypilot_root."
  exit 1
fi

site_packages="$(find "$skypilot_root/lib" -maxdepth 2 -type d -name site-packages | head -n 1)"
if [[ -z "$site_packages" ]]; then
  log "skypilot site-packages not found under $skypilot_root/lib."
  exit 1
fi

export SKY_CONSTANTS="$site_packages/sky/skylet/constants.py"
export SKY_AWS_TEMPLATE="$site_packages/sky/templates/aws-ray.yml.j2"

if [[ ! -f "$SKY_CONSTANTS" ]]; then
  log "Missing $SKY_CONSTANTS"
  exit 1
fi
if [[ ! -f "$SKY_AWS_TEMPLATE" ]]; then
  log "Missing $SKY_AWS_TEMPLATE"
  exit 1
fi

log "Patching skypilot templates for clean provisioning logs."

"$python_bin" - <<'PY'
import os
from pathlib import Path

constants = Path(os.environ["SKY_CONSTANTS"])
aws_template = Path(os.environ["SKY_AWS_TEMPLATE"])

constants_data = constants.read_text()
new_block = """COPY_SKYPILOT_TEMPLATES_COMMANDS = (
    f'{ACTIVATE_SKY_REMOTE_PYTHON_ENV}; '
    f"{SKY_PYTHON_CMD} -c '"
    'import sky_templates, shutil, os; '
    'src = os.path.dirname(sky_templates.__file__); '
    'dst = os.path.expanduser("~/sky_templates"); '
    'print(f"Copying templates from {src} to {dst}..."); '
    'same = os.path.realpath(src) == os.path.realpath(dst); '
    'print("Templates already in place") if same else '
    'shutil.copytree(src, dst, dirs_exist_ok=True); '
    'print("Templates ready")'
    "'; "
    # Make scripts executable.
    'if [ -d ~/sky_templates ]; then '
    'find ~/sky_templates -type f ! -name "*.py" ! -name "*.md" '
    '-exec chmod +x {} \\\\; ; '
    'fi; ')
"""

start = constants_data.find("COPY_SKYPILOT_TEMPLATES_COMMANDS = (")
end = constants_data.find("SKYPILOT_WHEEL_INSTALLATION_COMMANDS")
if start == -1 or end == -1 or end < start:
    raise SystemExit("skypilot constants block not found")

constants_data = constants_data[:start] + new_block + "\n\n" + constants_data[end:]
constants.write_text(constants_data)

aws_data = aws_template.read_text()
old = 'conda config --remove channels "https://aws-ml-conda-ec2.s3.us-west-2.amazonaws.com" || true;'
new = (
    'if conda config --show channels 2>/dev/null | '
    'grep -q "aws-ml-conda-ec2"; then '
    'conda config --remove channels "https://aws-ml-conda-ec2.s3.us-west-2.amazonaws.com" '
    '>/dev/null 2>&1 || true; fi;'
)
if old in aws_data:
    aws_data = aws_data.replace(old, new)
    aws_template.write_text(aws_data)
PY

log "skypilot patch applied."
