# Post-hoc sanity controls, after inspecting v3

These controls are added after the five v3 policies were measured. They are
explicitly post-hoc and are not used to rewrite v3 or claim confirmation.
All predictions, IDs, .95 frame gate and targets remain fixed.

1. For exactly-three-corner cases, pass the **whole frame** to OCR instead of
   rejecting. This tests whether automatic coverage gains arise merely from
   permitting a partial-document route. Geometry loss and crop area remain
   full-frame; only this control overrides the .95 gate for its full-frame
   passthrough cases. Report that gate difference explicitly.
2. Parallelogram completion with fixed outward margins .05 or .10 times the
   square root of completed quad area, clipped to the frame. These are simple
   baselines using the same fixed fractions as v1, not fitted after outcomes.

Keep originally valid neural predictions unchanged for all controls; other
failed corner patterns still require review. Reuse cached predictions, no new
inference/training. Report all three controls, every split and external case.
Measure the candidate's polygon-area reduction against the full-frame route
on the same rescued cases, but do not call polygon area an observed OCR runtime
speedup: an actual masked/bounding-box OCR pipeline has not been benchmarked.

If coverage/utility gains disappear against these controls, report that result
and lower the novelty assessment. Do not turn the best fixed margin into a
claimed newly invented algorithm.
