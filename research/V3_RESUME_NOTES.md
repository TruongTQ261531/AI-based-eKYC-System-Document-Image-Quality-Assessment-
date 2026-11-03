# Additional completion work after the running supervisor

Update 2026-11-03: the additional replay, numeric audits, manuscript, browser
checks and main integration below have completed. The user's newer instruction
allows deleting merged branches. Preserve their exact tips as tags, use main for
future publication, and see PRIORITY_PROGRESS_VI.md for work still uncompleted.
The historical preserve-branches instruction at the end is superseded by this
newer user request; the frozen scientific artifacts remain protected.

This note supplements the durable workflow state. It does not change either
primary training/reference signature or the secondary fusion signature.

Windows slept because of battery on 2026-11-02 from 09:25:46 UTC to
14:45:48 UTC. One V1 generation, `vlm_v2/test/000/evaluation/0`, includes that
gap in its raw wall timer. The original result remains intact. Evidence is in
`results/vlm_lora_v2_r2/execution_interruptions.json`. AC power was confirmed
Online after resume. Do not subtract an invented active duration or remove
this row from accuracy. Both reports now append raw and documented-incident
latency sensitivity tables.

After the supervisor finishes, before loading a model through the web or
integrating main, execute the extra post-incident consistency check:

```powershell
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.vlm_setup run -- -m research.v2_interruptions replay
```

This is one additional cached-feature generation, not fresh vision inference,
and never replaces the primary output. If its hash differs, retain both and
investigate rather than claiming repeatability. Once it succeeds, regenerate
both reports to include the measured replay status, then build the English
working paper from the audited numbers:

```powershell
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.v2_report
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.v3_report
& D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.v3_paper
```

The English draft is generated only after primary and secondary audits pass.
Perform actual localhost specimen/new-fictional-specimen OCR, edit/clear checks
and save a result screenshot. Simulated camera tests are already passed;
physical-user camera and independent human legibility remain unperformed.
The user has no available human helpers and no new camera collection.

Then review all current local/remote branches, their functional boundaries,
API/dependency/launcher compatibility and ancestry before integrating main.
The user explicitly requested stopping the integration of a conflicting branch,
identifying the conflict and preserving that branch. Do not delete branch refs
or force conflict resolutions. Frozen V1/V4 and mentor must remain intact.
Keep images, private labels, raw OCR strings and all new weights local.
