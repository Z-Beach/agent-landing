# Pre-registration: E3 Inter-Annotator Reliability

**Committed before data collection.**

## Design
- 3 independent raters code 60 items into S1..S5.
- Each item presented twice: once as AIL expression, once as English paraphrase,
  in separate sessions, counterbalanced order across raters.
- Raters are not the author; have read only the codebook (5-label taxonomy),
  not the AIL spec.

## Metric
- Krippendorff's alpha (nominal) per condition, with 95% CI via bootstrap (1000
  resamples).

## Thresholds
- Adopt condition: alpha_AIL >= 0.67 AND (alpha_AIL - alpha_English) >= 0.15 AND
  the 95% CI of the difference excludes 0.
- Fail (project kill for v0.2): alpha_AIL < 0.67 OR gap < 0.15.

## Power
- 60 items x 3 raters -> 95% CI width ~0.12 on alpha. Sufficient to detect 0.15 gap.
