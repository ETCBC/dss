"""Make data version 2.0.2: morphemes for 11Q19 and 1Qisaa.

Version 2.0.1 added the morphological parsing of 1Qisaa, but some features
were not derived correctly for that scroll:

*   `g_cons` was missing for 1Qisaa;
*   `g_lex_etcbc` contained the vocalised Hebrew lexeme instead of the
    realised lexeme in ETCBC transliteration;
*   `lex_utf8_etcbc` was empty;
*   `g_pfm_etcbc` still contained the `=` marker and `g_prs_etcbc` was missing
    when the `=` marker preceded the suffix.

This program starts from 2.0.1 and derives all morpheme features of 1Qisaa
again from `morph_etcbc`, using the same conventions that were used for 11Q19.
The data of 11Q19 is kept, except for 5 words where `morph_etcbc` lacked the
pronominal suffix that is present in `g_cons` and `g_prs_etcbc`.

`g_cons` of 1Qisaa is derived from `morph_etcbc`, but only where it agrees with
the consonants of the scroll (`#` may be `C` or `F`). Where it does not, the
value of version 1.9 is taken if that one agrees with the scroll. These words
are listed, because their `morph_etcbc` must be corrected by hand.
Words without legible consonants get no `g_cons` and no morpheme features.

`lex_utf8_etcbc` is taken from the BHSA (`voc_lex_utf8`), and for lexemes
not in the BHSA from the `dss_lex.csv` files in `import`.
"""

import csv
import os
import re
from shutil import copy

from tf.fabric import Fabric


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_BASE = f"{BASE}/tf"
IMPORT_BASE = f"{BASE}/import"
BHSA = os.path.expanduser("~/text-fabric-data/etcbc/bhsa/tf/2021")

SOURCE = "2.0.1"
DEST = "2.0.2"
G_CONS_FALLBACK = "1.9"

SCROLLS = ("11Q19", "1Qisaa")
REDO_SCROLL = "1Qisaa"
LEX_FILES = ("TempleSroll", "1Qisaa")

MORPHEME_FEATURES = dict(
    pfm="g_pfm_etcbc",
    vbs="g_vbs_etcbc",
    lex="g_lex_etcbc",
    vbe="g_vbe_etcbc",
    nme="g_nme_etcbc",
    uvf="uvf_etcbc",
    prs="g_prs_etcbc",
)

# words in 11Q19 where morph_etcbc lacks the suffix that is in g_cons and g_prs_etcbc
MORPH_FIXES = {
    1867431: "B+HMH",
    1869566: "L+HMH",
    1869738: "L+HMH",
    1869790: "L+HMH",
    1869798: "L+HMH",
}

FEATURES = (
    "g_cons",
    "morph_etcbc",
    "lex_etcbc",
    "lex_utf8_etcbc",
    *MORPHEME_FEATURES.values(),
)

META_FIXES = dict(
    g_lex_etcbc=dict(
        description=(
            "The consonantal representation of the realised lexeme"
            " of a word occurrence in BHSA transliteration"
        )
    ),
)


def realise(morph):
    """The consonants of (a part of) a morph string, without markers.

    Removed are: annotations such as `:a` and `:c`,
    lexeme letters that are not realised (preceded by `(`),
    and all morpheme markers.
    """

    morph = re.sub(r":[a-z]+", "", morph)
    morph = re.sub(r"\([A-Z<>]", "", morph)
    return re.sub(r"[^A-Z<>]", "", morph)


def segment(morph):
    """Split a morph string into its realised morphemes.

    The morphemes are returned as a dict keyed by the names in
    `MORPHEME_FEATURES`; morphemes that are not present have value `""`.
    """

    parts = {k: "" for k in MORPHEME_FEATURES}
    rest = re.sub(r":[a-z]+", "", morph)

    match = re.match(r"!([^!]*)!", rest)
    if match:
        parts["pfm"] = match.group(1)
        rest = rest[match.end():]

    match = re.match(r"\]([^\]]*)\]", rest)
    if match:
        parts["vbs"] = match.group(1)
        rest = rest[match.end():]

    if "+" in rest:
        (rest, parts["prs"]) = rest.split("+", 1)
    if "~" in rest:
        (rest, parts["uvf"]) = rest.split("~", 1)

    match = re.match(r"([^\[/]*)\[([^/]*)", rest)
    if match:
        parts["lex"] = match.group(1)
        parts["vbe"] = match.group(2)
        rest = rest[match.end():]
        if rest.startswith("/"):
            parts["nme"] = rest[1:]
    elif "/" in rest:
        (parts["lex"], parts["nme"]) = rest.split("/", 1)
    else:
        parts["lex"] = rest

    return {k: realise(v) for (k, v) in parts.items()}


def agrees(cons, signs):
    """Whether a consonantal word agrees with the consonant signs of the scroll.

    The scroll has `#` for both shin and sin, so it may stand for `C` or `F`.
    """

    return len(cons) == len(signs) and all(
        c == s or (s == "#" and c in "CF") for (c, s) in zip(cons, signs)
    )


def readGconsFallback():
    TFF = Fabric(locations=f"{TF_BASE}/{G_CONS_FALLBACK}", silent="deep")
    TFF.load("g_cons", silent="deep")
    return TFF.features["g_cons"].data


def readLexUtf8():
    """Mapping from ETCBC lexemes to Hebrew lexemes in UNICODE.

    The BHSA is leading, the `dss_lex.csv` files are used for
    lexemes that are not in the BHSA.
    """

    TFB = Fabric(locations=BHSA, silent="deep")
    apiB = TFB.load("lex voc_lex_utf8 language", silent="deep")
    FB = apiB.F

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

    TF = Fabric(locations=sourceDir, silent="deep")
    api = TF.load(f"scroll type glyphe {' '.join(FEATURES)}", silent="deep")
    F, L = api.F, api.L

    data = {f: dict(TF.features[f].data) for f in FEATURES}
    meta = {f: dict(TF.features[f].metaData) for f in FEATURES}

    for (f, fixes) in META_FIXES.items():
        meta[f].update(fixes)

    for (w, morph) in MORPH_FIXES.items():
        data["morph_etcbc"][w] = morph

    lexUtf8 = readLexUtf8()
    gConsFallback = readGconsFallback()
    noUtf8 = []
    fromFallback = []
    illegible = []
    disagreeing = []

    for s in F.otype.s("scroll"):
        if F.scroll.v(s) != REDO_SCROLL:
            continue

        for w in L.d(s, otype="word"):
            for f in (*MORPHEME_FEATURES.values(), "g_cons", "lex_utf8_etcbc"):
                data[f].pop(w, None)

            lex = data["lex_etcbc"].get(w, "")

            if lex and lex != "=":
                if lex in lexUtf8:
                    data["lex_utf8_etcbc"][w] = lexUtf8[lex]
                else:
                    noUtf8.append((w, lex))

            morph = data["morph_etcbc"].get(w, "")
            if not morph:
                continue

            signs = "".join(
                F.glyphe.v(c).upper()
                for c in L.d(w, otype="sign")
                if F.type.v(c) == "cons"
            )
            if not signs:
                illegible.append((w, morph))
                continue

            gCons = realise(morph)
            if not agrees(gCons, signs):
                fallback = gConsFallback.get(w, "")
                if fallback and agrees(fallback, signs):
                    fromFallback.append((w, morph, gCons, fallback))
                    gCons = fallback
                else:
                    disagreeing.append((w, morph, gCons, signs))
            data["g_cons"][w] = gCons

            for (k, v) in segment(morph).items():
                if k == "lex" and lex == "=":
                    continue
                if v:
                    data[MORPHEME_FEATURES[k]][w] = v

    os.makedirs(destDir, exist_ok=True)
    for name in os.listdir(sourceDir):
        if name.endswith(".tf") and os.path.isfile(f"{sourceDir}/{name}"):
            copy(f"{sourceDir}/{name}", f"{destDir}/{name}")

    TF = Fabric(locations=destDir, silent="deep")
    TF.save(
        nodeFeatures={f: data[f] for f in FEATURES},
        metaData={f: meta[f] for f in FEATURES},
        location=destDir,
        silent="deep",
    )

    print(f"Written {len(FEATURES)} features to {destDir}")
    print(f"{len(noUtf8)} words without lex_utf8_etcbc:")
    for (w, lex) in noUtf8:
        print(f"\t{w}\t{lex}")
    print(f"{len(illegible)} words with a parse but without legible consonants:")
    for (w, morph) in illegible:
        print(f"\t{w}\t{morph}")
    print(
        f"{len(fromFallback)} words with g_cons from {G_CONS_FALLBACK},"
        " because the parse does not agree with the scroll:"
    )
    print("\tnode\tmorph_etcbc\tfrom parse\tg_cons")
    for (w, morph, gCons, fallback) in fromFallback:
        print(f"\t{w}\t{morph}\t{gCons}\t{fallback}")
    print(f"{len(disagreeing)} words where g_cons does not agree with the scroll:")
    for (w, morph, gCons, signs) in disagreeing:
        print(f"\t{w}\t{morph}\t{gCons}\t{signs}")


if __name__ == "__main__":
    produce()
