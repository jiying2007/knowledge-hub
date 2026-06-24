# Engineering Archive

This directory stores local engineering notes, validation records, release guides, and troubleshooting conclusions.

## Structure

```text
archive/
  README.md
  pcr02/
    README.md
    ota-release/
    partition-storage/
    ubifs-squashfs/
    boot-flash/
    hardware-power/
    runtime-io/
    validation/
    source-audit/
```

## Rules

- Keep reusable decisions, evidence, commands, and release/validation guides.
- Do not store raw full serial logs by default; extract the relevant evidence snippets.
- Do not store credentials, private keys, tokens, or runtime secrets.
- Do not copy large release binaries by default; record path, size, hash, and NAS location.
- Use a topic directory for complex workstreams with multiple notes or artifacts.
- Use a single Markdown file for small, self-contained notes.

## Projects

- [PCR02](pcr02/README.md)
