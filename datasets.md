# Datasets for fitting mortality hazard ratios

All you need from a dataset is: covariates at baseline, vital status later,
and a defensible way to weight it. Below, ranked by how quickly you can get
something working.

## The two main options

| | **NHIS-LMF** | **NHANES-LMF** |
|---|---|---|
| Linked adults | ~1M+ | ~50k |
| Covariates | Self-report only | Self-report **plus labs and measured anthropometry** |
| Survey years | 1986-2018 (public) | NHANES III + 1999-2018 |
| Follow-up | Through 2019 (public) | Through 2019 (public) |
| Best for | Behavioural HRs, rare outcomes | Biomarkers, measurement-error work |
| Easiest access | IPUMS NHIS (free, registration) | Kaggle `nguyenvy/nhanes-19882018` |

**NHIS** wins on power. Twenty times the sample means you can actually
estimate age-interacted hazard ratios, which is the one thing that would
let you replace the guessed attenuation function with something fitted.

**NHANES** wins on quality. Measured BMI and blood pressure instead of
self-report, plus blood panels. Smaller, but it's the only one of the two
where you can quantify how much regression dilution is costing you.

Both are free and public. A newer 2022 NHIS linkage (follow-up through
2022) exists but is restricted-use, via the NCHS Research Data Center only.

## Also worth considering

**HRS (Health and Retirement Study)** — ~43k, age 50+, biennial follow-up
since 1992, NDI-linked. The important difference: *repeated measures of the
same people*. That's the direct fix for regression dilution and exposure
change, which neither NHIS nor NHANES can give you. Cost is the age
restriction — useless for anything under 50.

**UK Biobank** — 500k, deep phenotyping, genotypes, imaging. The best
single-cohort model available (Ubble was built on it). Requires an approved
application and a fee, has severe healthy-volunteer selection bias, and is
UK-specific. Probably not worth it unless you outgrow the free options.

**NHLBI BioLINCC** (Framingham, ARIC, CARDIA, MESA) — decades of
longitudinal follow-up with clinical depth. Free but application-gated, and
each is a few thousand to tens of thousands of people in specific
geographies. Good for validation, bad for a first pass.

## Not useful for this

**CDC WONDER / NVSS**, **HMD**, **SSA cohort tables** — population rates
with no individual covariates. These give you the *baseline* hazard, which
you already have. They cannot give you hazard ratios.

## Start here

IPUMS NHIS. Build a custom extract, let them handle 30 years of
questionnaire redesigns, and pull `MORTSTAT`, `MORTWT`/`MORTWTSA`,
`MORTUCODLD`, plus whatever covariates you want.

Three things that silently give wrong answers:

- **`MORTSTAT` is not binary.** 0 = alive, 1 = dead via NDI, 2 = dead via
  another source, 3 = ineligible but known dead, missing = ineligible.
  Treating it as 0/1 turns real deaths into survivors.
- **Use the eligibility-adjusted weight**, not `PERWEIGHT`. `MORTWT` for
  person-file years, `MORTWTSA` from 2015 on. People who couldn't be linked
  differ systematically from those who could.
- **Age is the timescale.** Respondents enter the risk set at their survey
  age, so this is left-truncated survival. Fit with delayed entry
  (`entry_col` in lifelines), not time-since-interview.
