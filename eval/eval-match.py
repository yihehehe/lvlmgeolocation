#!/usr/bin/env python3
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Optional, Tuple

import pandas as pd



PRED_CSV = r" "
GT_CSV   = r" "

OUT_CSV  = " "
# ================================

UNKNOWN_TOKENS = {"", "na", "n/a", "none", "null", "unknown", "unk", "-", "--", "?", "nan"}

ADMIN_STOPWORDS = {
    "city", "town", "village", "district", "county", "province", "state",
    "region", "prefecture", "municipality", "governorate", "dept", "department",
    "metropolitan", "area"
}

SEP_RE = re.compile(r"[,\;/\|\(\)\[\]\{\}]+")
SPACE_RE = re.compile(r"\s+")


def strip_diacritics(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    if s.lower() in UNKNOWN_TOKENS:
        return ""
    s = s.lower()
    s = strip_diacritics(s)
    s = s.replace("’", "'")
    s = re.sub(r"[^a-z0-9\s'-]", " ", s)
    s = SEP_RE.sub(" ", s)
    s = SPACE_RE.sub(" ", s).strip()
    return s


def tokenize(s: str) -> Tuple[str, ...]:
    if not s:
        return tuple()
    toks = [t for t in s.split(" ") if t and t not in ADMIN_STOPWORDS]
    return tuple(toks)


def seq_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def match_city_inclusive(gt_city_raw: Optional[str], pr_city_raw: Optional[str]) -> bool:
    gt = normalize_text(gt_city_raw)
    pr = normalize_text(pr_city_raw)
    if not gt or not pr:
        return False

    if gt == pr:
        return True

    gt_toks = tokenize(gt)
    pr_toks = tokenize(pr)

    if gt_toks and pr_toks:
        gt_set = set(gt_toks)
        pr_set = set(pr_toks)

        # inclusive containment: "miami" vs "miami florida"
        if pr_set.issubset(gt_set) or gt_set.issubset(pr_set):
            return True

        # high token overlap
        inter = len(gt_set & pr_set)
        union = len(gt_set | pr_set)
        if union > 0 and (inter / union) >= 0.75:
            return True

        # fuzzy on token-joined
        if seq_ratio(" ".join(gt_toks), " ".join(pr_toks)) >= 0.70:
            return True

    # fuzzy on whole normalized strings
    return seq_ratio(gt, pr) >= 0.70


def match_exactish(a_raw: Optional[str], b_raw: Optional[str]) -> bool:
    a = normalize_text(a_raw)
    b = normalize_text(b_raw)
    return bool(a) and a == b


def match_fuzzy(a_raw: Optional[str], b_raw: Optional[str], threshold: float) -> bool:
    a = normalize_text(a_raw)
    b = normalize_text(b_raw)
    if not a or not b:
        return False
    if a == b:
        return True
    return seq_ratio(a, b) >= threshold


def match_field(level: str, gt_val: Optional[str], pr_val: Optional[str]) -> int:
    if level == "city":
        return int(match_city_inclusive(gt_val, pr_val))

    # stricter for country/continent
    if match_exactish(gt_val, pr_val):
        return 1
    return int(match_fuzzy(gt_val, pr_val, threshold=0.85))


def main():
    pred = pd.read_csv(PRED_CSV, encoding='latin-1')
    gt = pd.read_csv(GT_CSV, encoding='latin-1')

    required = {"filename", "city", "country", "continent"}
    if not required.issubset(pred.columns):
        raise ValueError(f"pred_csv missing columns: {sorted(required - set(pred.columns))}")
    if not required.issubset(gt.columns):
        raise ValueError(f"gt_csv missing columns: {sorted(required - set(gt.columns))}")

    pred = pred.drop_duplicates(subset=["filename"], keep="last")
    gt = gt.drop_duplicates(subset=["filename"], keep="last")

    df = gt.merge(pred, on="filename", how="inner", suffixes=("_gt", "_pred"))
    if df.empty:
        raise RuntimeError("No overlapping filenames between GT and predictions.")

    for level in ["city", "country", "continent"]:
        df[f"match_{level}"] = df.apply(
            lambda r: match_field(level, r[f"{level}_gt"], r[f"{level}_pred"]),
            axis=1,
        )

    n = len(df)
    print(f"Matched rows (by filename): {n}")
    print(f"City accuracy:      {df['match_city'].mean():.4f} ({df['match_city'].sum()}/{n})")
    print(f"Country accuracy:   {df['match_country'].mean():.4f} ({df['match_country'].sum()}/{n})")
    print(f"Continent accuracy: {df['match_continent'].mean():.4f} ({df['match_continent'].sum()}/{n})")

    out_cols = [
        "filename",
        "city_gt", "city_pred", "match_city",
        "country_gt", "country_pred", "match_country",
        "continent_gt", "continent_pred", "match_continent",
    ]
    df[out_cols].to_csv(OUT_CSV, index=False)
    print(f"Wrote per-row matches to: {OUT_CSV}")


if __name__ == "__main__":
    main()