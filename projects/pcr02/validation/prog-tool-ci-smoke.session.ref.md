# PCR02 prog_tool CI Smoke Session Artifact Reference

## Artifact

- Source id: `pcr02-project-docs`
- Artifact URI: `source://pcr02-project-docs/runbooks/examples/prog-tool-ci-smoke.session`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Source path: `runbooks/examples/prog-tool-ci-smoke.session`
- Size: `394`
- SHA256: `00bacb95fea9c9517edfa0db3e573d738d60659428f77f638cc2cf5774690247`
- Artifact type: `prog_tool session script`
- Knowledge Hub status: `reviewing`
- Review after: `2026-09-17`

## Boundary

This entry registers the session script as an artifact reference only. The script body is not imported as prose knowledge, and this file is not an execution instruction.

The source project remains the content authority for the session script. Execute it only after confirming the target device, firmware build, `prog_tool` version, and PCR02 validation context.

## Usage

- Use this reference to verify artifact identity by `size` and `sha256`.
- Use this reference when linking PCR02 validation reports to the CI smoke session artifact.
- Do not treat the referenced script as a team-wide diagnostic standard.

## Open Review

- Confirm the `source://pcr02-project-docs/...` URI format with the PCR02 registry owner.
- Confirm whether a stable artifact store should replace the local source path.
- Confirm whether the session script belongs to a validation package, CI fixture, or project-local example set.
