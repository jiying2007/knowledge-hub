# PCR02 prog_tool CI Smoke Session Artifact Reference

## Artifact

- Source id: `pcr02-project-docs`
- Artifact URI: `source://pcr02-project-docs/runbooks/examples/prog-tool-ci-smoke.session`
- Source provenance: `registry/sources.json` origin_path for `pcr02-project-docs`; `registry/source-tombstones.jsonl`
- Source path: `runbooks/examples/prog-tool-ci-smoke.session`
- Size: `394`
- SHA256: `00bacb95fea9c9517edfa0db3e573d738d60659428f77f638cc2cf5774690247`
- Artifact type: `prog_tool session script`
- Knowledge Hub status: `reviewing`
- Review after: `2026-09-17`

## Boundary

This entry registers the session script as an artifact reference only. The script body is not imported as prose knowledge, and this file is not an execution instruction.

Knowledge Hub source metadata and registry provenance are the recovery authority for this artifact reference. Execute the referenced script only after confirming the target device, firmware build, `prog_tool` version, and PCR02 validation context.

## Usage

- Use this reference to verify artifact identity by `size` and `sha256`.
- Use this reference when linking PCR02 validation reports to the CI smoke session artifact.
- Do not treat the referenced script as a team-wide diagnostic standard.

## Review Boundary

- Keep the `source://pcr02-project-docs/...` URI only as logical provenance for the registered hash and size.
- Do not read the retired source project path by default and do not treat this artifact reference as executable guidance.
- Future replacement with a stable artifact store must preserve the SHA256, size and Hub registry provenance before updating this reference.
