# Unverified

Everything this audit could not confirm, each with the specific thing that
blocked it. Nothing on this list is asserted anywhere else in this repository.

## Blocked by the missing dataset

The authors released no data. 28 385 subselections across 6750 trials from 30
participants were collected (§5) and none of it is public. That blocks:

| # | Claim | Specific blocker |
|---|---|---|
| 1 | Every descriptive mean and SD in §5.1–§5.7 | No trial-level or participant-level data. The means were checked against each other (`src/audit_reported_stats.py`) but cannot be recomputed |
| 2 | Every F, χ², t, W and p in §5 | Same. The reported values were checked for internal consistency; 19/21 p-values and all 21 η²ₚ reproduce *from the reported F and df*, which is not the same as reproducing them from data |
| 3 | That the two-way RM ANOVA was in fact run on cell means with these exclusions applied | The pipeline in `src/analyze.py` implements the declared plan and runs, but has never touched the authors' input. Any agreement with their output is unverified |
| 4 | Whether the Greenhouse–Geisser epsilons recovered from the printed dfs were the epsilons actually computed | The df ratios are consistent with a single correction factor per test, which is necessary but not sufficient. Huynh–Feldt applied to the same data would give a slightly different epsilon and the same *ratio* structure |
| 5 | The 6.5% figure for the error-free TCT exclusion | 445 trials is 6.59% of 6750 or 6.62% of the 6720 retained; neither rounds to 6.5%. Without the data it is impossible to tell whether the count, the percentage, or the denominator is the error |
| 6 | The reported 24.4 s / 10.77 multi-selections per training phase | Training-phase logs were not released |
| 7 | Whether the reported ranking counts sum correctly across all five positions | Only five of the 25 cells of the ranking matrix are stated in the text; Fig. 12B holds the rest as pixels |

## Blocked by the missing implementation

No Unity project, scene, prefab or build was released. That blocks:

| # | Claim | Specific blocker |
|---|---|---|
| 8 | That the pinch thresholds behaved as Fig. 3 describes on the actual Meta Hand Pose Detection SDK | The SDK's fingertip-distance estimate, its own smoothing and its latency are not reproducible in a Python reimplementation, and no build exists to instrument |
| 9 | The SemiSwipe activation distance | Never stated. Estimated at 0.060–0.162 m from the paper's own hand-movement means (`src/recover_unstated_params.py`) under assumptions listed there. **This is an estimate, not a recovered fact** |
| 10 | The number of rows and columns in the object grid | §4.1.2 gives 40 objects, 1 m spacing and a 58.12° × 25.06° window, which are mutually over-determined and do not agree — the window holds 112 lattice cells. The intended layout is unknown; Fig. 7A is a rendered screenshot from which a grid could be counted only approximately, and no vector source was released |
| 11 | The visual indicator geometry for SemiSwipe and SemiTilt (three spheres, sizes, offsets) | Described qualitatively in §3.3.2–§3.3.3 and shown in Fig. 7B; no dimensions given, no asset released. The indicators are visible to participants and part of what was evaluated |
| 12 | Whether the gaze signal was filtered before hit-testing | The paper reports the eye tracker's 30 Hz sample rate and nothing about filtering. This interacts with both the dwell timer and the collider tie-break |
| 13 | The two application probes' behaviour (§7) | Prose and one figure each. Not enough to rebuild, and no build or video figure was reachable |
| 14 | That the invisible collider was 60 cm and the visible object 20 cm *in the shipped build* | Stated in §4.1.3, consistent internally, but unverifiable without the project |

## Blocked by the missing questionnaire items

| # | Claim | Specific blocker |
|---|---|---|
| 15 | The SUS results in §5.7 | The three positive and three negative statements of the six-item variant are never printed. The scoring arithmetic is implemented and the 4.05 criterion checks out as 68/100 on a 0–6 scale, but the instrument itself cannot be reconstructed |
| 16 | The satisfaction result | "a single question about satisfaction" — the question is not given |
| 17 | Whether NASA-TLX was raw or weighted | §4.3 lists the six subscales; no weighting procedure is described. Fig. 12 plots them individually, which is consistent with raw, but this is inference |
| 18 | The demographics and prior-experience items | The four 6-point prior-experience ratings (VR, controller, hand, gaze) are summarised but the question wording is not given |

## Blocked by access restrictions from this environment

| # | Claim | Specific blocker |
|---|---|---|
| 19 | That the ACM version of record is textually identical to arXiv v2 | `dl.acm.org` returns HTTP 403 to this environment (Cloudflare). All section, figure and page references in this repository are to arXiv:2503.05456v2, whose LaTeX preamble still carries the placeholder DOI `XXXXXXX.XXXXXXX`. If the VoR added an availability statement, this audit would not have seen it |
| 20 | Whether the ACM DL record carries supplementary material or an artifact badge | HTTP 403; the supplementary tab could not be inspected. The absence of supplementary material is inferred from the arXiv source, the paper's own lack of any reference to one, and the CHI '26 follow-up's explicit contrast (it *does* ship a supplementary statistics file) |
| 21 | Whether Aarhus University's Pure record has files attached | `pure.au.dk` returns HTTP 403 for both the landing page and the web API. OpenAlex classifies this location as `other-oa`, which usually means an accepted manuscript, not data |
| 22 | The conference talk video | A YouTube video is indexed under the paper's exact title and author list, but a direct fetch returned HTTP 429. Not counted as a found artifact anywhere in this audit |
| 23 | Whether the last author's GitHub account holds an unlisted or differently named repository | `api.github.com/users/kenpfeuffer/repos` returned HTTP 403 (unauthenticated rate limit). The two GitHub *search* queries that did succeed returned zero repositories matching the paper or its technique names, which covers public repos under any owner |

## Judgements, not verified facts

Stated plainly so they are not mistaken for findings:

| # | Judgement | Status |
|---|---|---|
| 24 | That the two §5.4 p-values are transpositions rather than a different analysis | An inference from their adjacency and from the recomputed values landing on each other's printed figures. The recomputation is verified; the explanation is a guess |
| 25 | That the Fig. 10 caption meant "SemiDwell and SemiTilt" | The most economical reading given the printed means and the body text. Not confirmed |
| 26 | That "consisting of 45 trials" is an error rather than a different sense of "trial" | 2 training trials × 5 blocks = 10. §4.2 reports 10.77 multi-selections per training *phase*, so ~108 selections total — neither reading gives 45 |
| 27 | That SemiDwell is the correct movement floor for the parameter-recovery estimator | Justified by §3.3.1 and by §5.5's means, but it is a modelling choice; using SemiNDH as the floor changes the estimate slightly |
| 28 | That the 18-component decomposition in `REPRODUCIBILITY.md` is the right granularity | It is one defensible slicing. The counts, and any rate derived from them, move with it |
| 29 | That the CHI '26 follow-up's `d < 2 cm` full-pinch threshold reflects PinchCatcher's | Shared last author and shared technique, but it is a different paper with a different release threshold (7 cm vs 10 cm). Supporting evidence, not confirmation |

## Not attempted, by design

The outer loop. No participant data was collected, simulated, imputed or
estimated, and no claim is made anywhere in this repository about what a user
study would have found. The eight outer-loop components are listed in
`REPRODUCIBILITY.md` and carry the outcome `not_scored` in `verdict.json`.
