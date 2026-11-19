#!/usr/bin/env python3
"""Check every archive in data/, then write orchive.json and the one-file index.html."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HANDLE = re.compile(r"^[a-z0-9_]{1,20}$")
AT = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
ORIGINAL = re.compile(r"^https://x\.com/(i|[A-Za-z0-9_]{1,15})/status/\d{5,20}$")
LIMITS = {"name": 50, "kind": 40, "bio": 160}


def _text(v, most):
    return isinstance(v, str) and 0 < len(v.strip()) and len(v) <= most


def _count(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def validate(archives):
    """Return a list of plain-word problems; empty means the set is good.

    The same rules are in template.html (`problems`) for pasted uploads.
    """
    errs, ids, replies, seen = [], set(), [], set()
    for n, a in enumerate(archives):
        acct = a.get("account") if isinstance(a, dict) else None
        tweets = a.get("tweets") if isinstance(a, dict) else None
        if not isinstance(acct, dict) or not isinstance(tweets, list) or not tweets:
            errs.append(f"archive {n}: needs an account and at least one tweet")
            continue
        h = acct.get("handle")
        if not isinstance(h, str) or not HANDLE.fullmatch(h):
            errs.append(f"archive {n}: handle must be 1-20 of a-z, 0-9, _")
            continue
        if h in seen:
            errs.append(f"@{h}: handle used twice")
        seen.add(h)
        for k, most in LIMITS.items():
            if not _text(acct.get(k), most):
                errs.append(f"@{h}: {k} must be 1-{most} characters")
        if not _count(acct.get("followers")):
            errs.append(f"@{h}: followers must be a whole number")
        for i, t in enumerate(tweets):
            where = f"@{h} tweet {i + 1}"
            if not isinstance(t, dict):
                errs.append(f"{where}: not an object")
                continue
            if not isinstance(t.get("at"), str) or not AT.fullmatch(t["at"]):
                errs.append(f"{where}: at must look like 2522-07-14 10:02")
            if not _text(t.get("text"), 280):
                errs.append(f"{where}: text must be 1-280 characters")
            if not _count(t.get("likes")) or not _count(t.get("retweets")):
                errs.append(f"{where}: likes and retweets must be whole numbers")
            if "note" in t and not _text(t["note"], 280):
                errs.append(f"{where}: note must be 1-280 characters")
            if "parody_of" in t and not (isinstance(t["parody_of"], str) and ORIGINAL.fullmatch(t["parody_of"])):
                errs.append(f"{where}: parody_of must be a tweet link like https://x.com/name/status/123456")
            if "id" in t:
                if not isinstance(t["id"], str) or not HANDLE.fullmatch(t["id"]):
                    errs.append(f"{where}: id must be 1-20 of a-z, 0-9, _")
                elif f"{h}/{t['id']}" in ids:
                    errs.append(f"{where}: id {t['id']} used twice")
                else:
                    ids.add(f"{h}/{t['id']}")
            if "reply_to" in t:
                replies.append((where, t["reply_to"]))
    for where, target in replies:
        if not isinstance(target, str) or target not in ids:
            errs.append(f"{where}: reply_to {target!r} matches no tweet id")
    return errs or ([] if archives else ["no archives in data/"])


def load():
    out = []
    for p in sorted((HERE / "data").glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except ValueError as e:
            out.append(None)
            print(f"{p.name}: not JSON ({e})", file=sys.stderr)
    return out


def page(archives):
    blob = json.dumps(archives, ensure_ascii=False).replace("</", "<\\/")
    return (HERE / "template.html").read_text(encoding="utf-8").replace("__ORCHIVE_DATA__", blob)


APPS = {  # page name -> title; each is apps.html with its name filled in
    "krumpr": "Krumpr",
    "waaagh": "WAAAGH-o-meter",
    "short": "Short-Finder",
    "grudges": "Grudge Search",
    "freds": "Fred Unroller",
}


def write_site(archives, out):
    """Write the whole site into `out`: the page, the data files and one page per app."""
    def dump(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page(archives), encoding="utf-8")
    (out / "share.png").write_bytes((HERE / "share.png").read_bytes())
    dump(out / "orchive.json", archives)
    dump(out / "api" / "gitz.json", [dict(a["account"], posts=len(a["tweets"])) for a in archives])
    dump(out / "api" / "posts.json", [dict(t, handle=a["account"]["handle"]) for a in archives for t in a["tweets"]])
    for a in archives:
        dump(out / "api" / "gitz" / f"{a['account']['handle']}.json", a)
    shell = (HERE / "apps.html").read_text(encoding="utf-8")
    for name, title in APPS.items():
        (out / f"{name}.html").write_text(shell.replace("__APP__", name).replace("__TITLE__", title), encoding="utf-8")


def main():
    archives = load()
    errs = validate(archives)
    if errs:
        print("\n".join(errs), file=sys.stderr)
        return 1
    write_site(archives, HERE / "public")
    print(f"{len(archives)} gitz, {sum(len(a['tweets']) for a in archives)} posts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
