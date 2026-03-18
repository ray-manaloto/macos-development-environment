# Python CLI Backend and Cache Decision

- Decision: global Python CLIs remain `mise`-owned and should converge on declarative `pipx:` backend entries; repo Python dependencies remain in `pyproject.toml` and lockfiles.
- Cache policy: reuse `UV_CACHE_DIR` for uv downloads and `PIPX_HOME` plus pip cache for installed CLI environments. Do not treat `uv tool install` as the authoritative path.
- Validation: prefer Python-native validation and cache-aware reads such as `uv cache dir` and `python3 -m pipx --version`.
- Sources:
  - <https://mise.jdx.dev/dev-tools/backends/pipx.html>
  - <https://docs.astral.sh/uv/concepts/cache/>
  - <https://docs.astral.sh/uv/reference/environment/#uv_cache_dir>
  - <https://pipx.pypa.io/stable/installation/>
