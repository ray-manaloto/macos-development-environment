# Rust Tooling Backend and Cache Decision

- Decision: Rust runtime remains a direct `mise` entry; cargo-installed CLIs must move under declarative ownership rather than script-owned `cargo install` loops.
- Cache policy: reuse `CARGO_HOME` registry and git caches, plus rustup state in `RUSTUP_HOME`.
- Validation: prefer cargo-native validation and linting.
- Sources:
  - <https://mise.jdx.dev/lang/rust.html>
  - <https://doc.rust-lang.org/cargo/guide/cargo-home.html>
  - <https://doc.rust-lang.org/cargo/commands/cargo-fetch.html>
