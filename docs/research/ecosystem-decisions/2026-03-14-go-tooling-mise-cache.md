# Go Tooling Backend and Cache Decision

- Decision: Go runtime remains a direct `mise` entry; legacy `go install` flows are transition-only until each CLI is declared declaratively.
- Cache policy: reuse `GOCACHE` and `GOMODCACHE` across setup and verification.
- Validation: prefer `go env`, `go test`, and other Go-native commands over shell-only checks.
- Sources:
  - <https://mise.jdx.dev/lang/go.html>
  - <https://go.dev/ref/mod>
  - <https://pkg.go.dev/cmd/go#hdr-Build_and_test_caching>
