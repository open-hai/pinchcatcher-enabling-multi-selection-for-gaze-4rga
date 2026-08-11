# Sources

## The paper

| Field | Value |
|---|---|
| Title | PinchCatcher: Enabling Multi-selection for Gaze+Pinch |
| Authors | Jinwook Kim, Sangmin Park, Qiushi Zhou, Mar Gonzalez-Franco, Jeongmi Lee, Ken Pfeuffer |
| Affiliations | KAIST (Graduate School of Culture Technology); Aarhus University; Google |
| Venue | CHI '25 — Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems, Yokohama, Japan, article 853 |
| DOI | [10.1145/3706598.3713530](https://doi.org/10.1145/3706598.3713530) |
| Published | 2025-04-25 |
| Pages | 1–16 |
| Preprint | [arXiv:2503.05456](https://arxiv.org/abs/2503.05456) (v1 2025-03-07, v2 2025-03-12) |
| DBLP | conf/chi/KimPZGLP25 |
| Corresponding authors | Jeongmi Lee, Ken Pfeuffer (both marked co-corresponding) |
| Funding | NST grant CRC21014 (Korea, MSIT); STEAM R&D Project, NRF Korea RS-2024-00454458 (Acknowledgments) |

### Which text this audit was performed against

The ACM version of record is gold open access under CC BY 4.0 (confirmed via
Crossref, Unpaywall and OpenAlex, all three fetched successfully — see below),
but `dl.acm.org` returns HTTP 403 to this environment, so the VoR PDF could not
be retrieved. **All section, figure and page references in this repository
point to arXiv:2503.05456v2**, downloaded and text-extracted locally:

```
curl -sL -o /tmp/paper/pinchcatcher.pdf https://arxiv.org/pdf/2503.05456v2
# 11,291,441 bytes, 16 pages, extracted with pypdf 3.17.4
curl -sL -o /tmp/paper/src.tar.gz https://arxiv.org/src/2503.05456
# LaTeX source: CHI25_MOS.tex, CHI25_MOS.bib, acmart.cls, 14 figures
```

The LaTeX source was also read in full. Its preamble still carries the
placeholder `doi: XXXXXXX.XXXXXXX` and `isbn: 978-1-4503-XXXX-X/18/06`, so the
preprint is a camera-ready-format draft rather than the typeset VoR. Any
difference between the preprint and the VoR is therefore **unverified** — this
is recorded in `UNVERIFIED.md`.

## Artifact search — every place looked, and what was found

The paper contains **no data-availability statement, no artifact appendix, no
footnote URL and no supplementary-material reference of any kind**. Verified by
grepping both the extracted PDF text and the original LaTeX source for
`github`, `osf.io`, `zenodo`, `available`, `supplement`, `open science`,
`repository`, `data availab`, `preregist` — the only hit in the entire document
is the word "available" in the first sentence of the introduction, describing
headset availability.

| # | Where | What was looked for | Command / URL | Result |
|---|---|---|---|---|
| 1 | Paper PDF, all 16 pages | availability statement, footnote URLs, appendix | grep over extracted text | **none** — no appendix, no availability statement |
| 2 | Paper LaTeX source | commented-out URLs, `\footnote` links, artifact macros | grep over `CHI25_MOS.tex` | **none** |
| 3 | arXiv ancillary files | dataset or code shipped alongside the preprint | `https://arxiv.org/src/2503.05456` (HTTP 200) | **none** — tarball holds only `.tex`, `.bib`, `.cls`, `Figures/` |
| 4 | arXiv abstract page | "Code, Data, Media" / Links-to-Code panel | `https://arxiv.org/abs/2503.05456` (HTTP 200) | no linked code or data |
| 5 | ACM DL landing page | artifacts / supplementary-material tab | `https://dl.acm.org/doi/10.1145/3706598.3713530` | **HTTP 403** — Cloudflare block, could not inspect |
| 6 | ACM DL PDF | version-of-record text | `https://dl.acm.org/doi/pdf/10.1145/3706598.3713530` | **HTTP 403** |
| 7 | Crossref | license, VoR metadata, linked resources | `https://api.crossref.org/works/10.1145/3706598.3713530` (HTTP 200) | **CC BY 4.0**, VoR, no dataset relation recorded |
| 8 | Unpaywall | OA locations | `https://api.unpaywall.org/v2/10.1145/3706598.3713530` (HTTP 200) | gold OA; 3 locations, none a data repository |
| 9 | OpenAlex | OA locations, linked datasets | `https://api.openalex.org/works/doi:10.1145/3706598.3713530` (HTTP 200) | same 3 locations; no dataset |
| 10 | Semantic Scholar | OA PDF, linked artifacts | `https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/3706598.3713530` (HTTP 200) | gold/CCBY, ACM PDF only |
| 11 | GitHub repo search | a project repository | `api.github.com/search/repositories?q=pinchcatcher` (HTTP 200) | **`total_count: 0`** |
| 12 | GitHub repo search | technique names | `q=PinchCatcher+OR+SemiSwipe in:name,description,readme` (HTTP 200) | **`total_count: 0`** |
| 13 | GitHub, first author | all public repos of `jinwook31` (the account linked from the author's own homepage) | both pages of `github.com/jinwook31?tab=repositories` | **49 repos, none PinchCatcher-related.** Full list captured; only one has an XR title, `xr-prototypes`, and its README and LICENSE (fetched raw, HTTP 200) show it is a fork of Oleg Frolov's unrelated MIT-licensed Quest prototype collection — keyboards and palm menus, no multi-selection. Filtering the repo list by `pinch`, `gaze`, `select`, `catcher` matches nothing else |
| 14 | GitHub, last author | repos of `kenpfeuffer` | `api.github.com/users/kenpfeuffer/repos` | HTTP 403 rate-limited; no PinchCatcher repo surfaced by the two repo searches above either |
| 15 | Zenodo | dataset or software deposit | `zenodo.org/api/records?q=PinchCatcher` (HTTP 200) | **0 hits**; `q="semi-pinch"` also **0 hits** |
| 16 | OSF | project, dataset, or preregistration | `api.osf.io/v2/nodes/?filter[title]=PinchCatcher` (HTTP 200) | **0 hits** |
| 17 | OSF registrations | a preregistration | `api.osf.io/v2/registrations/?filter[title]=multi-selection gaze` (HTTP 200) | **0 hits** |
| 18 | OSF | alternate title spelling | `filter[title]=gaze+pinch` (HTTP 200) | **0 hits** |
| 19 | First author homepage | project page, code link, data link | `http://jinwook.me/` (HTTP 200, full text read) | publication list only; links to CV, Scholar, LinkedIn, GitHub, blog. **No PinchCatcher artifact link** |
| 20 | First author CV | artifact mention | `jinwook.me/CV.pdf`, `CV_Industrial.pdf` | lists PinchCatcher as a project; no repository |
| 21 | Last author homepage | project page for the paper | `https://kenpfeuffer.com/` (HTTP 200, publication entry located and read) | title, authors and venue only; **no code or data link** |
| 22 | Aarhus University Pure | institutional record, attached files | `pure.au.dk/portal/en/publications/a7edd45a-…` | **HTTP 403** — Cloudflare block. OpenAlex records this location as `other-oa`; contents not inspectable |
| 23 | Aarhus Pure API | research-output record | `pure.au.dk/ws/api/research-outputs?q=PinchCatcher` | **HTTP 403** (Cloudflare challenge page) |
| 24 | SIGCHI CHI 2025 programme | supplementary material entry | `programs.sigchi.org/chi/2025/program/content/188999` (HTTP 200) | client-rendered shell, no artifact links in the served HTML |
| 25 | ResearchGate | author-uploaded supplement | search results for both RG entry IDs | full-text preprint only, no artifacts |
| 26 | YouTube | the CHI presentation / video figure | `youtube.com/watch?v=oVrsMkHCTj0` | HTTP 429 on direct fetch; the video is indexed under the paper's title and author list, but **the URL could not be verified from this environment**, so it is not counted as a found artifact |

### What that adds up to

No code, no dataset, no preregistration and no supplementary artifact exists for
this paper anywhere that could be reached. The one open-science criterion that
is satisfied is the licence: the version of record is CC BY 4.0 and a full-text
preprint is freely available. Everything else is a genuine "none found".

Note the distinction the scorecard preserves: every negative above is `none`
(nothing was ever published there), not `dead` (something was published and no
longer resolves). No broken artifact link was found, because no artifact link
was ever given.

## Related work used as an external check

| Work | Use here |
|---|---|
| Bashar, Mutasim, Pfeuffer & Batmaz, "Eyes on Many: Evaluating Gaze, Hand, and Voice for Multi-Object Selection in Extended Reality", CHI '26, [10.1145/3772318.3790513](https://doi.org/10.1145/3772318.3790513) | A follow-up sharing the last author. It re-uses the semi-pinch quasi-mode and states the pinch bands as full `d < 2 cm`, semi `2 cm ≤ d ≤ 7 cm`, release `d > 7 cm`. Its full-pinch figure of 2 cm independently supports the value this repository had to assume for PinchCatcher's unstated contact threshold; its release threshold of 7 cm differs from PinchCatcher's 10 cm, showing the value is a free design choice rather than a hardware constant. It also reports a supplementary statistics file, which PinchCatcher does not have. |
| Zhu et al., PinchLens (ref. 83 in the paper) | Origin of the semi-pinch gesture PinchCatcher builds on; cited by the paper for the fingertip-distance thresholding approach. |

## Tools used

`curl`, `pypdf` 3.17.4, Python 3.11, `numpy` 2.4.6, `pandas` 3.0.3,
`scipy` 1.17.1, `pingouin` 0.6.1.

All downloads were written to `/tmp/paper/`. Nothing third-party is committed to
this repository.
