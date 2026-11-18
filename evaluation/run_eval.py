"""Run the real pipeline on labelled cases and report accuracy, speed and token use.

    python -m evaluation.run_eval
    python -m evaluation.run_eval --models gemini-3.5-flash-lite,gemini-2.5-flash

A case is FILE.pdf/.jpg/.png plus FILE.json: [{"name": "...", "value_number": 1.0, "status": "LOW|NORMAL|HIGH"}]
"""
import argparse
import glob
import json
import os
import time

import main
from evaluation.scoring import health, score, summarize
from metrics import Usage

HERE = os.path.dirname(__file__)


def run_case(c, path):
    with open(path, "rb") as f:
        data = f.read()
    pages, keep = main.load_pages([(os.path.basename(path), data)])
    u, t0 = Usage(), time.time()
    results = [main.extract_page(c, p[1], u) for p in pages]
    items, _, _, failed = main.collect(results, pages)
    n = len(pages)
    for d in keep:
        d.close()
    return items, u, time.time() - t0, failed, n


def cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=os.path.join(HERE, "cases"))
    ap.add_argument("--models", default=main.MODEL)
    ap.add_argument("--out", default=os.path.join(HERE, "results.json"))
    a = ap.parse_args()
    c = main.client()
    files = sorted(f for ext in ("pdf", "jpg", "jpeg", "png") for f in glob.glob(os.path.join(a.cases, f"*.{ext}")))
    files = [f for f in files if os.path.exists(os.path.splitext(f)[0] + ".json")]
    report = {}
    for model in a.models.split(","):
        main.MODEL = model.strip()
        rows, secs, tin, tout, bad, failed, total = [], 0.0, 0, 0, 0, 0, 0
        print(f"\n== {main.MODEL} ==")
        for f in files:
            truth = json.load(open(os.path.splitext(f)[0] + ".json", encoding="utf8"))
            items, u, s, fp, n = run_case(c, f)
            rows.append(score(items, truth))
            failed += fp; total += n
            r = rows[-1]
            print(f"  {os.path.basename(f)}: {r['matched']}/{r['truth']} rows found, {fp}/{n} pages failed, {s:.0f}s")
            secs += s; tin += u.tokens_in; tout += u.tokens_out; bad += u.invalid
        status = health(failed, total)
        res = {"status": status, "failed_pages": f"{failed}/{total}", **summarize(rows), "cases": len(files), "avg_seconds": round(secs / max(len(files), 1), 1),
               "tokens_in": tin, "tokens_out": tout, "invalid_items": bad}
        report[main.MODEL] = res
        print(f"{main.MODEL}: {res}")
        if status != "ok":
            print(f"  WARNING: {status.upper()} run. {failed} of {total} pages got no answer, so recall is not a reading-accuracy score.")
    with open(a.out, "w", encoding="utf8") as f:
        json.dump(report, f, indent=2)
    print("saved", a.out)


if __name__ == "__main__":
    cli()
