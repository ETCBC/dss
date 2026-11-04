"""Make data version 2.0.4: corrections of individual words.

The corrections are given in `CORRECTIONS`, per word node and feature,
with the value before and after. The program checks that the old value is
still present, so that a correction is never applied to data that has
changed in the meantime.

Where `lex_etcbc` changes, `lex_utf8_etcbc` is derived again, in the same way
as in `morphemes.py`: from the BHSA, else from the `dss_lex.csv` files.
Words of the parsed scrolls that had a lexeme without `lex_utf8_etcbc` get one
as well, if it is now available in the `dss_lex.csv` files.

Corrections in this version:

*   lexemes of four words that disagreed with the BHSA parallel,
    found by `check_lexemes.py` of the hebrew_spelling_variation project
    (2026-10-19): Isa 38:16 in 1Qisaa and 1Q8, Amos 1:3 in 5Q4, Nah 2:13 in Mur88;
*   `lex_utf8_etcbc` for the lexemes KTJJM/ (Kittim) and BRX/ (fleeing)
    in 1Qisaa, added to `import/1Qisaa/dss_lex.csv`;
*   the verbal stems and participles of all scrolls follow the conventions
    of the BHSA (see `bhsaConventions()`).

Run this program before `addExtrabiblical.py`, which adds to the result.
"""

import collections
import csv
import os
import sys
from shutil import copy

from tf.fabric import Fabric

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add1QpHab import analyse, stem  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_BASE = f"{BASE}/tf"
IMPORT_BASE = f"{BASE}/import"
BHSA_CANDIDATES = (
    "~/text-fabric-data/github/ETCBC/bhsa/tf/2021",
    "~/text-fabric-data/etcbc/bhsa/tf/2021",
)

SOURCE = "2.0.3"
DEST = "2.0.4"

PARSED_SCROLLS = ("11Q19", "1Qisaa", "1QpHab")
LEX_FILES = ("TempleSroll", "1Qisaa", "1QpHab")

# node: {feature: (old value, new value)}; None means: no value
CORRECTIONS = {
    # 1Qisaa Isa 38:16 TXLJMNJ: be healthy, not dream (BHSA 225299)
    1908704: dict(lex_etcbc=("XLM[", "XLM=[")),
    # 1Q8 Isa 38:16 TXLJMNJ: idem
    1921610: dict(lex_etcbc=("XLM[", "XLM=[")),
    # 5Q4 Amos 1:3 XRYWT: lexeme was missing (BHSA 295453)
    2073004: dict(lex_etcbc=(None, "XRWY/")),
    # Mur88 Nah 2:13 M<NTJW: dwelling, as in the BHSA (301849)
    2096889: dict(lex_etcbc=("M<NH/", "M<WN/"), gn_etcbc=("f", "m")),
}


# verbal stems of the BHSA (Hebrew)
BHSA_STEMS = {
    "qal", "nif", "piel", "pual", "hit", "hif", "hof", "hsht",
    "hotp", "pasq", "poel", "poal", "tif", "nit", "htpo",
}
# stems that the BHSA uses only for a few lexemes
RARE_STEMS = {"poel", "poal", "htpo", "hotp", "tif", "nit"}
# the BHSA counterpart of stems that it does not distinguish
TO_BHSA = {
    "polel": "piel", "pilpel": "piel", "poel": "piel", "palel": "piel",
    "polal": "pual", "pulal": "pual", "poal": "pual",
    "hitopel": "hit", "hitpalpel": "hit", "htpo": "hit",
}
# participles of these stems are passive participles in the BHSA
PASSIVE = {"pual", "hof", "pasq"}


def bhsaLexStems():
    TFB = Fabric(locations=bhsaPath(), silent="deep")
    FB = TFB.load("lex language vs", silent="deep").F
    stems = collections.defaultdict(set)
    for w in FB.otype.s("word"):
        if FB.language.v(w) == "Hebrew" and FB.vs.v(w) != "NA":
            stems[FB.lex.v(w)].add(FB.vs.v(w))
    return stems


def bhsaConventions(F, L, data, changes):
    """Verbal stems and participles as in the BHSA, in all scrolls.

    The BHSA does not distinguish polel, pilpel, polal, hitpolel etc.:
    they are piel, pual and hitpael. Poel, poal and hitpolel are used by the
    BHSA for a few lexemes only; elsewhere they are piel, pual and hitpael.
    The new stem is given by `TO_BHSA`. Words whose `morph_etcbc` does not
    fit the new stem (e.g. a missing `:d`) are reported: their morphology
    must be checked by hand.

    The participles of pual, hofal and passive qal are passive participles
    (`ptcp`) in the BHSA.
    """
    lexStems = bhsaLexStems()
    doubtful = []
    for w in F.otype.s("word"):
        vs = data["vs_etcbc"].get(w)
        lex = data["lex_etcbc"].get(w)
        morph = data["morph_etcbc"].get(w)
        if vs in TO_BHSA and not (vs in RARE_STEMS and vs in lexStems.get(lex, set())):
            new = TO_BHSA[vs]
            if morph and not morphAgrees(morph, new):
                doubtful.append((w, lex, morph, vs, new))
            data["vs_etcbc"][w] = new
            changes.append((w, "vs_etcbc", vs, new))
            vs = new
        vt = data["vt_etcbc"].get(w)
        if vt == "ptca" and vs in PASSIVE:
            data["vt_etcbc"][w] = "ptcp"
            changes.append((w, "vt_etcbc", vt, "ptcp"))
    return doubtful


def morphAgrees(morph, vs):
    """Whether the stem derived from the morphology is the given stem."""
    if "[" not in morph:
        return False
    a = analyse(morph)
    a["reduplicated"] = False
    return stem(a) == vs


def bhsaPath():
    for path in BHSA_CANDIDATES:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return path
    raise FileNotFoundError("BHSA 2021 not found")


def readLexUtf8():
    TFB = Fabric(locations=bhsaPath(), silent="deep")
    FB = TFB.load("lex language voc_lex_utf8", silent="deep").F

    mapping = {}
    for w in FB.otype.s("word"):
        if FB.language.v(w) == "Hebrew":
            mapping.setdefault(FB.lex.v(w), FB.voc_lex_utf8.v(w))

    for name in LEX_FILES:
        with open(f"{IMPORT_BASE}/{name}/dss_lex.csv", encoding="utf8") as fh:
            for row in csv.DictReader(fh):
                if row["voc_lex_utf8"]:
                    mapping.setdefault(row["lex"], row["voc_lex_utf8"])
    return mapping


def produce():
    sourceDir = f"{TF_BASE}/{SOURCE}"
    destDir = f"{TF_BASE}/{DEST}"

    features = sorted(
        {f for fixes in CORRECTIONS.values() for f in fixes}
        | {"lex_etcbc", "lex_utf8_etcbc", "vs_etcbc", "vt_etcbc", "morph_etcbc"}
    )
    TF = Fabric(locations=sourceDir, silent="deep")
    api = TF.load(f"scroll {' '.join(features)}", silent="deep")
    F, L = api.F, api.L

    data = {f: dict(TF.features[f].data) for f in features}
    meta = {f: dict(TF.features[f].metaData) for f in features}

    stale = []
    for (w, fixes) in CORRECTIONS.items():
        for (f, (old, new)) in fixes.items():
            current = data[f].get(w) or None
            if current != old:
                stale.append((w, f, old, current))
    if stale:
        for (w, f, old, current) in stale:
            print(f"{w} {f}: expected {old!r}, found {current!r}")
        raise ValueError("corrections do not fit the source data")

    lexUtf8 = readLexUtf8()
    changes = []

    def setUtf8(w):
        lex = data["lex_etcbc"].get(w)
        new = lexUtf8.get(lex) if lex and lex != "=" else None
        old = data["lex_utf8_etcbc"].get(w)
        if new and new != old:
            data["lex_utf8_etcbc"][w] = new
            changes.append((w, "lex_utf8_etcbc", old, new))

    for (w, fixes) in CORRECTIONS.items():
        for (f, (old, new)) in fixes.items():
            data[f][w] = new
            changes.append((w, f, old, new))
        if "lex_etcbc" in fixes:
            setUtf8(w)

    for s in F.otype.s("scroll"):
        if F.scroll.v(s) in PARSED_SCROLLS:
            for w in L.d(s, otype="word"):
                if data["lex_etcbc"].get(w) and not data["lex_utf8_etcbc"].get(w):
                    setUtf8(w)

    doubtful = bhsaConventions(F, L, data, changes)

    os.makedirs(destDir, exist_ok=True)
    for name in os.listdir(sourceDir):
        if name.endswith(".tf") and os.path.isfile(f"{sourceDir}/{name}"):
            copy(f"{sourceDir}/{name}", f"{destDir}/{name}")

    TF = Fabric(locations=destDir, silent="deep")
    TF.save(
        nodeFeatures={f: data[f] for f in features},
        metaData={f: meta[f] for f in features},
        location=destDir,
        silent="deep",
    )

    print(f"Written {len(features)} features to {destDir}")
    print(f"{len(changes)} changes:")
    summary = collections.Counter()
    for (w, f, old, new) in changes:
        if f in {"vs_etcbc", "vt_etcbc"}:
            summary[(f, old, new)] += 1
        else:
            print(f"\t{w}\t{f}\t{old}\t{new}")
    for ((f, old, new), n) in sorted(summary.items()):
        print(f"\t{n:4}x\t{f}\t{old}\t{new}")
    print(f"{len(doubtful)} words whose morph_etcbc does not fit the new stem:")
    for (w, lex, morph, old, new) in doubtful:
        print(f"\t{w}\t{lex}\t{morph}\t{old} -> {new}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    produce()
