"""Make data version 2.0.3: the morphological parsing of 1QpHab.

The parsing of 1QpHab was made by Saulo de Oliveira Cantanhêde. It is in
`import/1QpHab/dss_out`, in the same format as the parsings of 11Q19 and
1Qisaa: one graphical word per line, with its consonants and its ETCBC
morphological encoding. Prefixes are separated by `-`; each part belongs to
one word node of Text-Fabric. The file `import/1QpHab/mapping.txt` gives, for
each line of `dss_out`, the word node (or range of word nodes) it belongs to.

This program starts from 2.0.2 and, for the words of 1QpHab:

*   sets `morph_etcbc` to the parsing;
*   derives `lex_etcbc` from it;
*   derives `vs_etcbc` and `vt_etcbc` from the stem and tense markers;
*   derives `ps_etcbc`, `nu_etcbc` and `gn_etcbc` from the preformative,
    the verbal ending and the nominal ending (verbs and nominals) or from the
    BHSA (pronouns and other words);
*   takes `sp_etcbc` from the lexeme: BHSA, else the `dss_lex.csv` files,
    else the parsed scrolls of 2.0.2, else the shape of the lexeme;
*   derives `g_cons` and the morpheme features in the same way as
    `morphemes.py` did for 1Qisaa; `g_cons` of words with lexeme `=` is taken
    from the signs;
*   takes `lex_utf8_etcbc` from the BHSA, else from the `dss_lex.csv` files.

The values of these features for 1QpHab in 2.0.2 (partly predicted by machine
learning) are removed first, so words without a parsing get no values, as in
1Qisaa. The conventions follow 1Qisaa: imperatives and participles have no
person, infinitives have number `NA` and gender `unknown`, first person verbs
have gender `unknown`.

The parsing has no state markers (`:a`, `:c`), so infinitive absolutes cannot
be recognised; they get `infc`.

The notes made during the parsing are added to `note_etcbc`
from `import/1QpHab/note_etcbc.tf`.
"""

import collections
import csv
import os
import re
import sys
from shutil import copy

from tf.fabric import Fabric

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from morphemes import MORPHEME_FEATURES, agrees, realise, segment  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_BASE = f"{BASE}/tf"
IMPORT_BASE = f"{BASE}/import"
BHSA_CANDIDATES = (
    "~/text-fabric-data/github/ETCBC/bhsa/tf/2021",
    "~/text-fabric-data/etcbc/bhsa/tf/2021",
)

SOURCE = "2.0.2"
DEST = "2.0.3"

SCROLL = "1QpHab"
PARSED_SCROLLS = ("11Q19", "1Qisaa")
LEX_FILES = ("TempleSroll", "1Qisaa", "1QpHab")

NOTE_META = dict(
    convertedBy=(
        "Martijn Naaijer, Dirk Roorda, Thijs Amersfoort"
        " and Saulo de Oliveira Cantanhêde"
    ),
    description=(
        "Notes by Thijs Amersfoort (11Q19, 1Qisaa) and Saulo de Oliveira"
        " Cantanhêde (1QpHab) during the morphological parsing of the text."
    ),
    source=(
        "Automatic generated morphological parsing corrected by Thijs"
        " Amersfoort (11Q19, 1Qisaa) and Saulo de Oliveira Cantanhêde (1QpHab)"
    ),
)

FEATURES = (
    "morph_etcbc",
    "lex_etcbc",
    "sp_etcbc",
    "vs_etcbc",
    "vt_etcbc",
    "ps_etcbc",
    "nu_etcbc",
    "gn_etcbc",
    "g_cons",
    "lex_utf8_etcbc",
    *MORPHEME_FEATURES.values(),
)
NA_FEATURES = ("vs_etcbc", "vt_etcbc", "ps_etcbc", "nu_etcbc")

NOMINAL = {"subs", "adjv", "nmpr"}

# person, number, gender of finite verbs, keyed by tense group, preformative
# and verbal ending (normalised)

PERF = {
    "": ("p3", "sg", "m"),
    "H": ("p3", "sg", "f"),
    "H=": ("p3", "sg", "f"),
    ">": ("p3", "sg", "f"),
    "T": ("p2", "sg", "m"),
    "TH": ("p2", "sg", "m"),
    "T=": ("p2", "sg", "f"),
    "TJ": ("p1", "sg", "unknown"),
    "W": ("p3", "pl", "unknown"),
    "TM": ("p2", "pl", "m"),
    "TMH": ("p2", "pl", "m"),
    "TN": ("p2", "pl", "f"),
    "TNH": ("p2", "pl", "f"),
    "NW": ("p1", "pl", "unknown"),
}
IMPF = {
    ("J", ""): ("p3", "sg", "m"),
    ("T", ""): ("p2", "sg", "m"),
    ("T=", ""): ("p3", "sg", "f"),
    (">", ""): ("p1", "sg", "unknown"),
    ("N", ""): ("p1", "pl", "unknown"),
    ("J", "W"): ("p3", "pl", "m"),
    ("J", "WN"): ("p3", "pl", "m"),
    ("T", "W"): ("p2", "pl", "m"),
    ("T", "WN"): ("p2", "pl", "m"),
    ("T", "J"): ("p2", "sg", "f"),
    ("T", "NH"): ("p2", "pl", "f"),
    ("T=", "NH"): ("p3", "pl", "f"),
    ("J", "NH"): ("p3", "pl", "f"),
}
IMPV = {
    "": ("sg", "m"),
    "H=": ("sg", "m"),
    "J": ("sg", "f"),
    "W": ("pl", "m"),
    "NH": ("pl", "f"),
}
# number of nominal endings (normalised); gender where the ending marks it
NOMINAL_ENDING = {
    "": ("sg", None),
    "H": ("sg", "f"),
    "T": ("sg", "f"),
    ">": ("sg", None),
    "J": ("pl", None),
    "JM": ("pl", None),
    "WT": ("pl", "f"),
    "WTJ": ("pl", "f"),
    "JN": ("pl", None),
    "J=": ("du", None),
    "JM=": ("du", None),
    "TJM": ("du", "f"),
    "JN=": ("du", None),
    "W=": ("du", None),
}
# gender of the nominal endings of participles and adjectives
ADJ_GENDER = {"": "m", "J": "m", "JM": "m", "H": "f", "T": "f", "WT": "f", "WTJ": "f"}


def norm(x):
    """Letters of a morpheme as in the paradigm.

    Letters marked with `&` (not in the paradigm) are left out,
    letters marked with `(` (not realised) are kept, annotations are left out.
    """
    x = re.sub(r":[a-z]+", "", x)
    x = re.sub(r"&[A-Z<>]", "", x)
    return x.replace("(", "")


def analyse(morph):
    """Split a morph string of one word node into its parts.

    A word node may contain an elided article, as in `B-(H`;
    then the first part is the word.
    """
    morph = morph.split("-", 1)[0]
    ann = set("".join(re.findall(r":([a-z]+)", morph)))
    rest = re.sub(r":[a-z]+", "", morph)
    pfm = vbs = None

    match = re.match(r"!([^!]*)!", rest)
    if match:
        pfm = norm(match.group(1))
        rest = rest[match.end():]
    match = re.match(r"\]([^\]]*)\]", rest)
    if match:
        vbs = norm(match.group(1))
        rest = rest[match.end():]

    rest = rest.split("+", 1)[0].split("~", 1)[0]
    match = re.match(r"([^\[/]*)(\[?)([^/]*)(/?)(.*)", rest)
    (lex, verbal, vbe, nominal, nme) = match.groups()
    # a reduplicated last radical, such as RWM&M, marks polel and the like
    reduplicated = bool(re.search(r"([A-Z<>])&\1$", lex))
    lexeme = norm(lex) + ("[" if verbal else "/" if nominal else "")

    return dict(
        ann=ann,
        pfm=pfm,
        vbs=vbs,
        lex=lexeme,
        reduplicated=reduplicated,
        verbal=bool(verbal),
        nominal=bool(nominal),
        vbe=norm(vbe),
        nme=norm(nme),
    )


def stem(a):
    vbs = a["vbs"]
    ann = a["ann"]
    if vbs is None:
        if "u" in ann:
            return "polal" if a["reduplicated"] else "pual"
        if "d" in ann:
            return "polel" if a["reduplicated"] else "piel"
        if "o" in ann:
            return "poel"
        return "qal"
    if "CT" in vbs:
        return "hsht"
    if "T" in vbs:
        return "hitopel" if a["reduplicated"] else "hit"
    if "N" in vbs:
        return "nif"
    if "u" in ann:
        return "hof"
    if "H" in vbs or ">" in vbs or vbs == "":
        return "hif"
    return "unknown"


def tense(a, afterWaw):
    ann = a["ann"]
    if a["pfm"] is not None:
        if a["pfm"] == "M":
            return "ptca"
        if a["nominal"]:
            return "infa" if "a" in ann else "infc"
        if a["pfm"] in {"", "H"}:
            return "impv"
        return "wayq" if afterWaw else "impf"
    if a["nominal"]:
        return "ptcp" if "p" in ann else "ptca"
    return "perf"


def verbPgn(a, vt):
    unknown = ("unknown", "unknown", "unknown")
    if vt == "perf":
        return PERF.get(a["vbe"], unknown)
    if vt in {"impf", "wayq"}:
        # the cohortative ending does not change person, number and gender
        vbe = "" if a["vbe"] == "H=" else a["vbe"]
        return IMPF.get((a["pfm"], vbe), unknown)
    if vt == "impv":
        (nu, gn) = IMPV.get(a["vbe"], ("unknown", "unknown"))
        return ("NA", nu, gn)
    if vt in {"infc", "infa"}:
        return ("NA", "NA", "unknown")
    (nu, _) = NOMINAL_ENDING.get(a["nme"], ("unknown", None))
    return ("NA", nu, ADJ_GENDER.get(a["nme"], "unknown"))


def bhsaPath():
    for path in BHSA_CANDIDATES:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return path
    raise FileNotFoundError("BHSA 2021 not found")


def readLexicon():
    """Information per lexeme from the BHSA, the lexicon files and 2.0.2."""
    TFB = Fabric(locations=bhsaPath(), silent="deep")
    apiB = TFB.load("lex language sp gn nu ps voc_lex_utf8", silent="deep")
    FB = apiB.F

    sp = collections.defaultdict(collections.Counter)
    gn = collections.defaultdict(collections.Counter)
    pgn = collections.defaultdict(collections.Counter)
    utf8 = {}
    for w in FB.otype.s("word"):
        if FB.language.v(w) != "Hebrew":
            continue
        lex = FB.lex.v(w)
        sp[lex][FB.sp.v(w)] += 1
        if FB.gn.v(w) not in {"NA", "unknown"}:
            gn[lex][FB.gn.v(w)] += 1
        pgn[lex][(FB.ps.v(w), FB.nu.v(w), FB.gn.v(w))] += 1
        utf8.setdefault(lex, FB.voc_lex_utf8.v(w))

    lexSp = {lex: c.most_common(1)[0][0] for (lex, c) in sp.items()}
    lexGn = {lex: c.most_common(1)[0][0] for (lex, c) in gn.items()}
    lexPgn = {lex: c.most_common(1)[0][0] for (lex, c) in pgn.items()}

    fileSp = {}
    for name in LEX_FILES:
        with open(f"{IMPORT_BASE}/{name}/dss_lex.csv", encoding="utf8") as fh:
            for row in csv.DictReader(fh):
                if row["voc_lex_utf8"]:
                    utf8.setdefault(row["lex"], row["voc_lex_utf8"])
                if row["sp"]:
                    fileSp.setdefault(row["lex"], row["sp"])

    return (lexSp, lexGn, lexPgn, utf8, fileSp)


def readParse():
    """The parse per word node of 1QpHab."""
    with open(f"{IMPORT_BASE}/{SCROLL}/dss_out", encoding="utf8") as fh:
        rows = [line.rstrip("\r\n").split("\t") for line in fh]
    with open(f"{IMPORT_BASE}/{SCROLL}/mapping.txt", encoding="utf8") as fh:
        mapping = [line.rstrip("\r\n").split("\t") for line in fh]

    if len(rows) != len(mapping):
        raise ValueError(f"{len(rows)} parsed words but {len(mapping)} mapped words")

    parse = {}
    for (row, (nodes, text)) in zip(rows, mapping):
        (i, ref, cons, morph) = row[0:4]
        if text.replace("-", "") != cons:
            raise ValueError(f"line {i} {ref}: {cons} does not match mapping {text}")
        bounds = [int(n) for n in nodes.split("-")]
        nodes = range(bounds[0], bounds[-1] + 1)
        parts = morph.split("-")
        if len(parts) != len(nodes):
            raise ValueError(f"line {i} {ref}: {morph} does not fit nodes {nodes}")
        for (n, part) in zip(nodes, parts):
            parse[n] = part
    return parse


def readNotes():
    """The notes in a TF feature file, with TF's rules for implicit nodes."""
    notes = {}
    prev = 0
    with open(f"{IMPORT_BASE}/{SCROLL}/note_etcbc.tf", encoding="utf8") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if line.startswith("@") or not line:
                continue
            if "\t" in line:
                (n, value) = line.split("\t", 1)
                n = int(n)
            else:
                (n, value) = (prev + 1, line)
            notes[n] = value
            prev = n
    return notes


def produce():
    sourceDir = f"{TF_BASE}/{SOURCE}"
    destDir = f"{TF_BASE}/{DEST}"

    TF = Fabric(locations=sourceDir, silent="deep")
    api = TF.load(
        f"scroll type glyphe note_etcbc {' '.join(FEATURES)}", silent="deep"
    )
    F, L = api.F, api.L

    data = {f: dict(TF.features[f].data) for f in (*FEATURES, "note_etcbc")}
    meta = {f: dict(TF.features[f].metaData) for f in (*FEATURES, "note_etcbc")}
    meta["note_etcbc"].update(NOTE_META)

    (lexSp, lexGn, lexPgn, lexUtf8, fileSp) = readLexicon()

    parsedSp = collections.defaultdict(collections.Counter)
    for s in F.otype.s("scroll"):
        if F.scroll.v(s) in PARSED_SCROLLS:
            for w in L.d(s, otype="word"):
                if F.sp_etcbc.v(w):
                    parsedSp[F.lex_etcbc.v(w)][F.sp_etcbc.v(w)] += 1

    def spOf(a):
        lex = a["lex"]
        if lex in lexSp:
            return lexSp[lex]
        if lex in fileSp:
            return fileSp[lex]
        if lex in parsedSp:
            return parsedSp[lex].most_common(1)[0][0]
        if a["verbal"]:
            return "verb"
        if a["nominal"]:
            return "subs"
        return ""

    parse = readParse()
    scroll = [s for s in F.otype.s("scroll") if F.scroll.v(s) == SCROLL][0]
    words = L.d(scroll, otype="word")

    unknownPgn = []
    noUtf8 = []
    disagreeing = []
    unparsedWithSigns = []
    stats = collections.Counter()

    for w in words:
        for f in FEATURES:
            data[f].pop(w, None)
        for f in NA_FEATURES:
            data[f][w] = "NA"
        data["sp_etcbc"][w] = ""

    for (i, w) in enumerate(words):
        signs = "".join(
            F.glyphe.v(c).upper() for c in L.d(w, otype="sign") if F.type.v(c) == "cons"
        )
        morph = parse.get(w, "")
        if not morph:
            if signs:
                unparsedWithSigns.append((w, signs))
            continue

        stats["parsed"] += 1
        data["morph_etcbc"][w] = morph

        if morph == "=":
            data["lex_etcbc"][w] = "="
            data["g_cons"][w] = signs
            stats["unknown lexeme"] += 1
            continue

        a = analyse(morph)
        lex = a["lex"]
        data["lex_etcbc"][w] = lex
        sp = spOf(a)
        if a["verbal"]:
            sp = "verb"
        data["sp_etcbc"][w] = sp

        if sp == "verb":
            afterWaw = i > 0 and parse.get(words[i - 1], "").endswith(":n")
            vt = tense(a, afterWaw)
            data["vs_etcbc"][w] = stem(a)
            data["vt_etcbc"][w] = vt
            pgn = verbPgn(a, vt)
        elif sp in NOMINAL:
            (nu, gn) = NOMINAL_ENDING.get(a["nme"], ("unknown", None))
            if sp == "adjv":
                gn = ADJ_GENDER.get(a["nme"], gn)
            elif sp == "nmpr" and a["nme"] == "":
                nu = "NA"
            gn = lexGn.get(lex, gn) if sp != "adjv" else gn
            pgn = ("NA", nu, gn or "unknown")
        else:
            pgn = lexPgn.get(lex, ("NA", "NA", "NA"))

        if "unknown" in pgn[0:2]:
            unknownPgn.append((w, morph, sp, pgn))
        (data["ps_etcbc"][w], data["nu_etcbc"][w], data["gn_etcbc"][w]) = pgn

        if lex in lexUtf8:
            data["lex_utf8_etcbc"][w] = lexUtf8[lex]
        else:
            noUtf8.append((w, lex))

        gCons = realise(morph)
        if not agrees(gCons, signs):
            disagreeing.append((w, morph, gCons, signs))
        data["g_cons"][w] = gCons
        for (k, v) in segment(morph).items():
            if v:
                data[MORPHEME_FEATURES[k]][w] = v

    for (n, note) in readNotes().items():
        data["note_etcbc"][n] = note

    os.makedirs(destDir, exist_ok=True)
    for name in os.listdir(sourceDir):
        if name.endswith(".tf") and os.path.isfile(f"{sourceDir}/{name}"):
            copy(f"{sourceDir}/{name}", f"{destDir}/{name}")

    saved = (*FEATURES, "note_etcbc")
    TF = Fabric(locations=destDir, silent="deep")
    TF.save(
        nodeFeatures={f: data[f] for f in saved},
        metaData={f: meta[f] for f in saved},
        location=destDir,
        silent="deep",
    )

    print(f"Written {len(saved)} features to {destDir}")
    print(f"{len(words)} words in {SCROLL}, {stats['parsed']} parsed,"
          f" {stats['unknown lexeme']} with unknown lexeme")
    print(f"{len(unparsedWithSigns)} words with consonants but without parse:")
    for x in unparsedWithSigns:
        print("\t" + "\t".join(str(y) for y in x))
    print(f"{len(noUtf8)} words without lex_utf8_etcbc:")
    for x in noUtf8:
        print("\t" + "\t".join(str(y) for y in x))
    print(f"{len(disagreeing)} words where g_cons does not agree with the scroll:")
    for x in disagreeing:
        print("\t" + "\t".join(str(y) for y in x))
    print(f"{len(unknownPgn)} words with unknown person or number:")
    for x in unknownPgn:
        print("\t" + "\t".join(str(y) for y in x))


if __name__ == "__main__":
    produce()
