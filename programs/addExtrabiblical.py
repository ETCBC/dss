"""Morphology of 1QS, 1QM and 1QHa from the ETCBC extrabiblical dataset.

The ETCBC extrabiblical dataset (ETCBC/extrabiblical, version 0.2) contains a
linguistic encoding of 1QS, 1QM and 1QHa, based on an older edition of the
texts. This program transfers its morphology to the DSS words.

Steps:

1.  `units()`: the extrabiblical words of a scroll are grouped into units
    that correspond to one DSS word node: a pronominal suffix (a separate word
    in extrabiblical) is attached to its host word, an article without
    consonants (elided after a preposition) to the preceding word.
2.  `align()`: the units are aligned with the DSS word nodes, on the basis of
    their consonants (C and F correspond to # in the scroll):
    *   `equal`: identical consonants, in a run of at least `MIN_RUN` words;
        only these words get the morphology of extrabiblical;
    *   `short`: identical consonants, but in a shorter run (in damaged text
        these are often accidental);
    *   `resplit`: a block of units and nodes with the same consonants,
        but divided differently into words; the word division of the DSS
        is kept, so these are not transferred;
    *   `replace`, `insert`, `delete`: different text.

    All words that are not `equal` are listed for review.

3.  `lexicon()`: the extrabiblical lexemes are mapped to lexemes in the
    conventions of the DSS (and the BHSA). The homonym numbers (`=`) of
    extrabiblical cannot be compared with those of the BHSA, so the mapping
    compares the consonants and the kind of lexeme (verb `[`, nominal `/`,
    other) and uses the current `lex_etcbc` of the aligned DSS words to choose
    between homonyms. Where that gives no answer, the words are not
    transferred until the homonym is decided by hand (`HOMONYMS`).
    Lexemes that are not known become new lexemes.
4.  `wordMorph()`: the morphology string `morph_etcbc` is built for each
    aligned DSS word from the paradigmatic morphemes (`pfm`, `vbs`, `vbe`,
    `nme`, `uvf`, the lexeme and the suffix) and the realised morphemes
    (`g_*`). Letters of the paradigm that are not written get `(`, written
    letters that are not in the paradigm get `&`. Annotations, as in 11Q19
    and 1Qisaa: `:d` piel, `:du` pual and passive qal, `:u` hofal,
    `:p` passive participle, `:a`/`:c` state of nominal forms without
    suffix, `:n` on the conjunction before a wayyiqtol.
5.  `produce()`: the features of the aligned words are set; the other words
    keep the values they had.

Checks: the consonants of the morphology agree with the signs of the scroll,
the lexeme derived from the morphology is the mapped lexeme, and the stem,
tense, person, number and gender derived from the morphology (with the rules
of `add1QpHab.py`) agree with those of extrabiblical.

The results are written to `import/extrabiblical`: the alignment per scroll,
the lexicon map and the review list.
"""

import collections
import csv
import difflib
import os
import re
import sys
from shutil import copy

from tf.fabric import Fabric

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add1QpHab import analyse, stem, tense, verbPgn  # noqa: E402
from morphemes import MORPHEME_FEATURES, agrees, realise, segment  # noqa: E402
from corrections import bhsaConventions  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_BASE = f"{BASE}/tf"
OUT_BASE = f"{BASE}/import/extrabiblical"
XB_LOCATION = os.path.expanduser("~/CACCHT/extrabiblical/tf/0.2")

# the scrolls are taken from PREVIOUS, the result is written into DEST,
# which already contains the corrections of `corrections.py`
PREVIOUS = "2.0.3"
DEST = "2.0.4"
SOURCE = PREVIOUS
IMPORT_BASE = f"{BASE}/import"
LEX_FILES = ("TempleSroll", "1Qisaa", "1QpHab")
BHSA_CANDIDATES = (
    "~/text-fabric-data/github/ETCBC/bhsa/tf/2021",
    "~/text-fabric-data/etcbc/bhsa/tf/2021",
)

SCROLLS = {"1QS": "B_1QS", "1QM": "B_1QM", "1QHa": "B_1QHa"}

# runs of fewer identical words, in damaged text, are not trusted
MIN_RUN = 3

XB_FEATURES = """
    book chapter verse g_cons lex lex_utf8 sp pdp ls st
    vs vt ps nu gn prs_ps prs_nu prs_gn
    pfm vbs vbe nme uvf g_pfm g_vbs g_lex g_vbe g_nme g_uvf
""".strip().split()


def loadXb():
    TF = Fabric(locations=XB_LOCATION, silent="deep")
    return TF.load(" ".join(XB_FEATURES), silent="deep")


def loadDss():
    TF = Fabric(locations=f"{TF_BASE}/{SOURCE}", silent="deep")
    return TF.load("scroll fragment line glyphe type rec", silent="deep")


def xbCons(F, w):
    return (F.g_cons.v(w) or "").replace("C", "#").replace("F", "#")


def units(apiX, book):
    """Group the extrabiblical words of a book into units of one DSS word."""
    F, L = apiX.F, apiX.L
    b = [b for b in F.otype.s("book") if F.book.v(b) == book][0]
    result = []
    unattached = []
    for w in L.d(b, otype="word"):
        isSuffix = F.ls.v(w) == "sffx"
        isElidedArticle = F.sp.v(w) == "art" and not F.g_cons.v(w)
        if (isSuffix or isElidedArticle) and result:
            result[-1].append(w)
        elif not F.g_cons.v(w):
            unattached.append(w)
            result.append([w])
        else:
            result.append([w])
    return (result, unattached)


def dssNodes(apiD, scroll):
    """The DSS words of a scroll with consonants, with their consonants."""
    F, L = apiD.F, apiD.L
    s = [s for s in F.otype.s("scroll") if F.scroll.v(s) == scroll][0]
    result = []
    for w in L.d(s, otype="word"):
        signs = [c for c in L.d(w, otype="sign") if F.type.v(c) == "cons"]
        if not signs:
            continue
        cons = "".join(F.glyphe.v(c) for c in signs).upper()
        rec = sum(1 for c in signs if F.rec.v(c))
        status = "none" if not rec else "full" if rec == len(signs) else "part"
        result.append((w, cons, status))
    return result


def align(apiX, apiD, scroll):
    FX = apiX.F
    (us, unattached) = units(apiX, SCROLLS[scroll])
    ds = dssNodes(apiD, scroll)
    a = ["".join(xbCons(FX, w) for w in u) for u in us]
    d = [cons for (w, cons, status) in ds]

    matcher = difflib.SequenceMatcher(None, a, d, autojunk=False)
    rows = []
    for (op, i1, i2, j1, j2) in matcher.get_opcodes():
        if op == "equal":
            status = "equal" if i2 - i1 >= MIN_RUN else "short"
            for (i, j) in zip(range(i1, i2), range(j1, j2)):
                rows.append((status, [us[i]], [ds[j]]))
        elif op == "replace" and "".join(a[i1:i2]) == "".join(d[j1:j2]):
            rows.append(("resplit", us[i1:i2], ds[j1:j2]))
        else:
            rows.append((op, us[i1:i2], ds[j1:j2]))
    return (rows, unattached, len(us), len(ds))


def ref(apiX, apiD, xbUnits, dsNodes):
    FX, LX = apiX.F, apiX.L
    FD, LD = apiD.F, apiD.L
    xRef = dRef = ""
    if xbUnits:
        v = LX.u(xbUnits[0][0], otype="verse")[0]
        xRef = f"{FX.chapter.v(v)}:{FX.verse.v(v)}"
    if dsNodes:
        ln = LD.u(dsNodes[0][0], otype="line")[0]
        dRef = f"{FD.fragment.v(ln)}:{FD.line.v(ln)}"
    return (xRef, dRef)


def writeAlignment(apiX, apiD, scroll, rows):
    FX = apiX.F
    os.makedirs(OUT_BASE, exist_ok=True)
    with open(f"{OUT_BASE}/{scroll}_alignment.tsv", "w", encoding="utf8") as fh:
        fh.write("status\tdss_ref\tdss_nodes\tdss_cons\tdss_rec\txb_ref\txb_nodes\txb_cons\n")
        for (op, xbUnits, dsNodes) in rows:
            (xRef, dRef) = ref(apiX, apiD, xbUnits, dsNodes)
            dNodes = " ".join(str(w) for (w, cons, status) in dsNodes)
            dCons = " ".join(cons for (w, cons, status) in dsNodes)
            dRec = " ".join(status for (w, cons, status) in dsNodes)
            xNodes = " ".join("+".join(str(w) for w in u) for u in xbUnits)
            xCons = " ".join("+".join(FX.g_cons.v(w) or "0" for w in u) for u in xbUnits)
            fh.write(f"{op}\t{dRef}\t{dNodes}\t{dCons}\t{dRec}\t{xRef}\t{xNodes}\t{xCons}\n")


def reportAlignment():
    apiX = loadXb()
    apiD = loadDss()
    for scroll in SCROLLS:
        (rows, unattached, nUnits, nNodes) = align(apiX, apiD, scroll)
        writeAlignment(apiX, apiD, scroll, rows)

        units = collections.Counter()
        nodes = collections.Counter()
        recByOp = collections.Counter()
        for (op, xbUnits, dsNodes) in rows:
            units[op] += len(xbUnits)
            nodes[op] += len(dsNodes)
            for (w, cons, status) in dsNodes:
                recByOp[(op, status)] += 1
        print(f"== {scroll}: {nUnits} extrabiblical units, {nNodes} DSS words with consonants")
        print(f"\tunattached words without consonants: {len(unattached)}")
        for op in ("equal", "short", "resplit", "replace", "delete", "insert"):
            print(
                f"\t{op:8} units {units[op]:6} ({units[op] / nUnits:6.1%})"
                f"  DSS words {nodes[op]:6} ({nodes[op] / nNodes:6.1%})"
                f"  of which reconstructed full/part/none:"
                f" {recByOp[(op, 'full')]}/{recByOp[(op, 'part')]}/{recByOp[(op, 'none')]}"
            )


# ---------------------------------------------------------------------------
# 3. Lexicon
# ---------------------------------------------------------------------------

NOMINAL_SP = {"subs", "adjv", "nmpr"}

# homonyms that cannot be chosen automatically, decided by hand:
# (extrabiblical lexeme, kind) -> DSS lexeme; see import/extrabiblical/lex_map.tsv
HOMONYMS = {}

# pronominal suffixes of extrabiblical: lexeme -> paradigm in the DSS
SUFFIX = {
    "W=": "W",
    "HW": "HW",
    "H=": "H",
    "K": "K",
    "K==": "K=",
    "KM": "KM",
    "KN": "KN",
    "M": "M",
    "HM": "HM",
    "HN": "HN",
    "MW": "MW",
    "N": "N",
    "J": "J",
    "NJ": "NJ",
    "NW": "NW",
}


def isSub(a, b):
    """Whether the letters of a occur in b in the same order."""
    it = iter(b)
    return all(c in it for c in a)


def core(lex):
    return re.sub(r"[/\[=]", "", lex)


def kind(lex):
    return "[" if lex.endswith("[") else "/" if lex.endswith("/") else ""


def xbKind(F, w):
    if F.vbe.v(w) != "n/a":
        return "["
    if F.nme.v(w) != "n/a":
        return "/"
    return ""


def bhsaPath():
    for path in BHSA_CANDIDATES:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return path
    raise FileNotFoundError("BHSA 2021 not found")


def knownLexemes(apiD):
    """Lexemes of the BHSA, the DSS lexicon files and the parsed scrolls."""
    TFB = Fabric(locations=bhsaPath(), silent="deep")
    FB = TFB.load("lex language voc_lex_utf8", silent="deep").F
    freq = collections.Counter()
    utf8 = {}
    for w in FB.otype.s("word"):
        if FB.language.v(w) == "Hebrew":
            freq[FB.lex.v(w)] += 1
            utf8.setdefault(FB.lex.v(w), FB.voc_lex_utf8.v(w))
    for name in LEX_FILES:
        with open(f"{IMPORT_BASE}/{name}/dss_lex.csv", encoding="utf8") as fh:
            for row in csv.DictReader(fh):
                freq[row["lex"]] += 0
                if row["voc_lex_utf8"]:
                    utf8.setdefault(row["lex"], row["voc_lex_utf8"])
    return (freq, utf8)


def lexicon(apiX, apiD, aligned, freq):
    """Map (extrabiblical lexeme, kind) to a DSS lexeme.

    `aligned` is a list of (unit, DSS node) pairs.
    Returns a dict with values (lexeme, basis, evidence).
    """
    FX, FD = apiX.F, apiD.F
    byCore = collections.defaultdict(set)
    for lex in freq:
        byCore[core(lex)].add(lex)

    evidence = collections.defaultdict(collections.Counter)
    for (unit, node) in aligned:
        w = unit[0]
        evidence[(FX.lex.v(w), xbKind(FX, w))][FD.lex_etcbc.v(node) or ""] += 1

    mapping = {}
    # lexemes decided by hand: (extrabiblical lexeme, kind) -> DSS lexeme
    for ((lex, k), dLex) in HOMONYMS.items():
        if (lex, k) in evidence:
            mapping[(lex, k)] = (dLex, "decided by hand", evidence[(lex, k)])
    for ((lex, k), ev) in sorted(evidence.items()):
        if (lex, k) in mapping:
            continue
        if lex == "=":
            continue
        cands = sorted(c for c in byCore[core(lex)] if kind(c) == k)
        if not cands and k == "":
            cands = sorted(byCore[core(lex)])
        dssTop = [x for (x, n) in ev.most_common() if x in cands]
        variants = [
            x for (x, n) in ev.most_common()
            if x in freq and kind(x) == k and (isSub(core(x), core(lex)) or isSub(core(lex), core(x)))
        ]
        if not cands and variants:
            mapping[(lex, k)] = (variants[0], "spelling variant chosen by DSS", ev)
        elif len(cands) == 1:
            mapping[(lex, k)] = (cands[0], "unique", ev)
        elif dssTop:
            mapping[(lex, k)] = (dssTop[0], "homonym chosen by DSS", ev)
        elif cands:
            # no evidence to choose between homonyms: decided by hand later
            mapping[(lex, k)] = ("|".join(cands), "homonym undecided", ev)
        else:
            mapping[(lex, k)] = (core(lex) + k, "new", ev)
    return mapping


# ---------------------------------------------------------------------------
# 4. Morphology
# ---------------------------------------------------------------------------


def mark(paradigm, written):
    """Combine paradigmatic and written letters into the DSS notation.

    Letters of the paradigm that are not written are preceded by `(`,
    written letters that are not in the paradigm by `&`.
    Homonym markers `=` in the paradigm are kept at the end.
    """
    eq = re.sub(r"[^=]", "", paradigm)
    p = paradigm.replace("=", "")
    r = written
    n, m = len(p), len(r)
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            lcs[i][j] = (
                lcs[i + 1][j + 1] + 1 if p[i] == r[j] else max(lcs[i + 1][j], lcs[i][j + 1])
            )
    out = []
    (i, j) = (0, 0)
    while i < n or j < m:
        if i < n and j < m and p[i] == r[j] and lcs[i][j] == lcs[i + 1][j + 1] + 1:
            out.append(p[i])
            i += 1
            j += 1
        elif i < n and (j == m or lcs[i + 1][j] >= lcs[i][j + 1]):
            out.append(f"({p[i]}")
            i += 1
        else:
            out.append(f"&{r[j]}")
            j += 1
    return "".join(out) + eq


def written(value, markers):
    return re.sub(f"[{re.escape(markers)}]", "", value or "")


def present(value):
    return value not in {"n/a", "absent", None}


def annotations(F, w, isSuffixed):
    ann = ""
    vs = F.vs.v(w)
    if vs == "piel":
        ann += "d"
    elif vs in {"pual", "pasq"}:
        ann += "du"
    elif vs == "hof":
        ann += "u"
    vt = F.vt.v(w)
    if vt == "ptcp" and vs == "qal":
        ann += "p"
    st = F.st.v(w)
    if F.nme.v(w) != "n/a" and not isSuffixed and st in {"a", "c"}:
        # on an infinitive, :a means infinitive absolute in the DSS
        if vt == "infc" and st == "a":
            pass
        elif vt == "infa":
            ann += "a"
        else:
            ann += st
    return f":{ann}" if ann else ""


def wordMorph(F, w, lex, suffixes):
    """The morphology string of one extrabiblical word with its suffix."""
    parts = []
    if present(F.pfm.v(w)):
        parts.append(f"!{mark(F.pfm.v(w), written(F.g_pfm.v(w), '!'))}!")
    if present(F.vbs.v(w)):
        parts.append(f"]{mark(F.vbs.v(w), written(F.g_vbs.v(w), ']'))}]")
    eq = re.sub(r"[^=]", "", lex)
    parts.append(mark(core(lex), written(F.g_lex.v(w), "-")) + eq)
    k = kind(lex)
    if present(F.vbe.v(w)):
        parts.append(f"[{mark(F.vbe.v(w), written(F.g_vbe.v(w), '[-'))}")
    elif k == "[":
        parts.append("[")
    if present(F.nme.v(w)):
        parts.append(f"/{mark(F.nme.v(w), written(F.g_nme.v(w), '/-'))}")
    elif k == "/":
        parts.append("/")
    if present(F.uvf.v(w)):
        parts.append(f"~{mark(F.uvf.v(w), written(F.g_uvf.v(w), '~-'))}")
    parts.append(annotations(F, w, bool(suffixes)))
    for s in suffixes:
        parts.append(f"+{mark(SUFFIX[F.lex.v(s)], F.g_cons.v(s) or '')}")
    return "".join(parts)


def unitMorph(F, unit, mapping):
    """The morphology string of a unit (one DSS word), or a reason why not."""
    w = unit[0]
    lex = F.lex.v(w)
    if lex == "=":
        return (None, "unknown lexeme in extrabiblical")
    if (lex, xbKind(F, w)) not in mapping:
        return (None, "no lexeme")
    (dLex, basis, ev) = mapping[(lex, xbKind(F, w))]
    if basis == "homonym undecided":
        return (None, f"homonym undecided: {dLex}")
    suffixes = [x for x in unit[1:] if F.ls.v(x) == "sffx"]
    articles = [x for x in unit[1:] if F.sp.v(x) == "art"]
    unknown = [x for x in suffixes if F.lex.v(x) not in SUFFIX]
    if unknown:
        return (None, f"unknown suffix {F.lex.v(unknown[0])}")
    morph = wordMorph(F, w, dLex, suffixes)
    if articles:
        morph += "-(H"
    return ((morph, dLex), None)


# ---------------------------------------------------------------------------
# 5. Features
# ---------------------------------------------------------------------------

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


def xbValues(F, w):
    """sp, vs, vt, ps, nu, gn of extrabiblical in the conventions of the DSS."""
    sp = F.sp.v(w)
    (vs, vt, ps, nu, gn) = (F.vs.v(w), F.vt.v(w), F.ps.v(w), F.nu.v(w), F.gn.v(w))
    if sp == "verb":
        if vt in {"infc", "infa"}:
            (ps, nu, gn) = ("NA", "NA", "unknown")
        elif vt in {"impv", "ptca", "ptcp"}:
            ps = "NA"
    return (sp, vs, vt, ps, nu, gn)


# differences between the rules of add1QpHab.py and the analysis of
# extrabiblical that are not errors: the morphology does not distinguish
# passive qal (pasq) from pual
EQUIVALENT = {
    ("vs", "pasq", "pual"),
}


def roundTrip(morph, afterWaw):
    """sp-independent values derived from the morphology, as for 1QpHab."""
    a = analyse(morph)
    if not a["verbal"]:
        return None
    vt = tense(a, afterWaw)
    return (stem(a), vt, *verbPgn(a, vt))


def produce():
    sys.stdout.reconfigure(encoding="utf-8")
    apiX = loadXb()
    FX = apiX.F

    prevDir = f"{TF_BASE}/{PREVIOUS}"
    destDir = f"{TF_BASE}/{DEST}"
    TFP = Fabric(locations=prevDir, silent="deep")
    apiD = TFP.load(
        f"scroll fragment line glyphe type rec {' '.join(FEATURES)}", silent="deep"
    )
    FD, LD = apiD.F, apiD.L
    prevData = {f: TFP.features[f].data for f in FEATURES}

    TFD = Fabric(locations=destDir, silent="deep")
    TFD.load(" ".join(FEATURES), silent="deep")
    data = {f: dict(TFD.features[f].data) for f in FEATURES}
    meta = {f: dict(TFD.features[f].metaData) for f in FEATURES}

    (freq, utf8) = knownLexemes(apiD)

    alignments = {}
    aligned = []
    for scroll in SCROLLS:
        (rows, unattached, nUnits, nNodes) = align(apiX, apiD, scroll)
        writeAlignment(apiX, apiD, scroll, rows)
        alignments[scroll] = rows
        for (status, xbUnits, dsNodes) in rows:
            if status == "equal":
                aligned.append((xbUnits[0], dsNodes[0][0]))

    mapping = lexicon(apiX, apiD, aligned, freq)
    writeLexicon(apiX, mapping, aligned)
    for (lex, row) in writeNewLexemes(apiX, mapping, aligned).items():
        utf8.setdefault(lex, row["voc_lex_utf8"])

    review = []
    stats = collections.Counter()
    tripDiffs = collections.Counter()

    for scroll in SCROLLS:
        s = [s for s in FD.otype.s("scroll") if FD.scroll.v(s) == scroll][0]
        scrollWords = LD.d(s, otype="word")

        # make the program repeatable: start from the values of PREVIOUS
        for w in scrollWords:
            for f in FEATURES:
                if w in prevData[f]:
                    data[f][w] = prevData[f][w]
                else:
                    data[f].pop(w, None)

        results = {}
        for (status, xbUnits, dsNodes) in alignments[scroll]:
            if status != "equal":
                for (node, cons, rec) in dsNodes:
                    review.append((scroll, node, cons, status, ""))
                continue
            (unit, (node, cons, rec)) = (xbUnits[0], dsNodes[0])
            (result, reason) = unitMorph(FX, unit, mapping)
            if result is None:
                review.append((scroll, node, cons, "not transferred", reason))
                continue
            results[node] = (unit, result)

        nodeIndex = {w: i for (i, w) in enumerate(scrollWords)}
        # the conjunction before a wayyiqtol gets :n
        for (node, (unit, (morph, lex))) in list(results.items()):
            if FX.vt.v(unit[0]) == "wayq":
                prev = scrollWords[nodeIndex[node] - 1]
                if prev in results and results[prev][1][0] == "W":
                    (pu, (pm, pl)) = results[prev]
                    results[prev] = (pu, ("W:n", pl))

        for (node, (unit, (morph, lex))) in results.items():
            w = unit[0]
            signs = "".join(
                FD.glyphe.v(c).upper() for c in LD.d(node, otype="sign") if FD.type.v(c) == "cons"
            )
            gCons = realise(morph)
            if not agrees(gCons, signs):
                review.append((scroll, node, signs, "consonants differ", morph))
                continue
            derived = analyse(morph)["lex"]
            if derived != lex:
                review.append((scroll, node, signs, "lexeme differs", f"{morph} {derived} {lex}"))
                continue

            (sp, vs, vt, ps, nu, gn) = xbValues(FX, w)
            prev = scrollWords[nodeIndex[node] - 1] if nodeIndex[node] else None
            afterWaw = prev in results and results[prev][1][0].endswith(":n")
            trip = roundTrip(morph, afterWaw)
            if trip is not None and sp == "verb":
                for (f, x, y) in zip(("vs", "vt", "ps", "nu", "gn"), (vs, vt, ps, nu, gn), trip):
                    if x != y and (f, x, y) not in EQUIVALENT:
                        tripDiffs[(f, x, y)] += 1
                        review.append((scroll, node, signs, f"round trip {f}", f"{morph} xb={x} morph={y}"))

            stats[scroll] += 1
            data["morph_etcbc"][node] = morph
            data["lex_etcbc"][node] = lex
            data["sp_etcbc"][node] = sp
            data["vs_etcbc"][node] = vs
            data["vt_etcbc"][node] = vt
            data["ps_etcbc"][node] = ps
            data["nu_etcbc"][node] = nu
            data["gn_etcbc"][node] = gn
            data["g_cons"][node] = gCons
            for f in MORPHEME_FEATURES.values():
                data[f].pop(node, None)
            for (k, v) in segment(morph).items():
                if v:
                    data[MORPHEME_FEATURES[k]][node] = v
            if lex in utf8:
                data["lex_utf8_etcbc"][node] = utf8[lex]
            else:
                data["lex_utf8_etcbc"].pop(node, None)
                review.append((scroll, node, signs, "no lex_utf8", lex))

        # words that keep their values: add a missing lex_utf8_etcbc
        for w in scrollWords:
            lex = data["lex_etcbc"].get(w)
            if lex and lex != "=" and not data["lex_utf8_etcbc"].get(w) and lex in utf8:
                data["lex_utf8_etcbc"][w] = utf8[lex]
                stats["lex_utf8 added"] += 1

    # the restored values of the words that keep their values:
    # stems and participles as in the BHSA, as done by corrections.py
    conventionChanges = []
    bhsaConventions(FD, LD, data, conventionChanges)
    print(f"{len(conventionChanges)} restored values brought into line with the BHSA")

    writeReview(review)

    for name in os.listdir(prevDir):
        target = f"{destDir}/{name}"
        if name.endswith(".tf") and not os.path.exists(target):
            copy(f"{prevDir}/{name}", target)
    TFS = Fabric(locations=destDir, silent="deep")
    TFS.save(
        nodeFeatures={f: data[f] for f in FEATURES},
        metaData={f: meta[f] for f in FEATURES},
        location=destDir,
        silent="deep",
    )

    print(f"Written {len(FEATURES)} features to {destDir}")
    for scroll in SCROLLS:
        print(f"{scroll}: {stats[scroll]} words with morphology from extrabiblical")
    print(f"lex_utf8_etcbc added to {stats['lex_utf8 added']} words that keep their values")
    print("lexicon map:", dict(collections.Counter(b for (x, b, e) in mapping.values())))
    print("review list:", dict(collections.Counter(r[3] for r in review)))
    print("round trip differences (feature, extrabiblical, from morphology):")
    for (k, n) in tripDiffs.most_common(30):
        print(f"\t{n}\t{k}")


def writeLexicon(apiX, mapping, aligned):
    FX = apiX.F
    utf8 = {}
    for (unit, node) in aligned:
        w = unit[0]
        utf8.setdefault((FX.lex.v(w), xbKind(FX, w)), FX.lex_utf8.v(w))
    os.makedirs(OUT_BASE, exist_ok=True)
    with open(f"{OUT_BASE}/lex_map.tsv", "w", encoding="utf8") as fh:
        fh.write("xb_lex\tkind\tdss_lex\tbasis\tlex_etcbc_of_aligned_words_in_2.0.3\n")
        for ((lex, k), (dLex, basis, ev)) in sorted(mapping.items()):
            evs = " ".join(f"{x or '-'}:{n}" for (x, n) in ev.most_common())
            fh.write(f"{lex}\t{k or '-'}\t{dLex}\t{basis}\t{evs}\n")


def writeNewLexemes(apiX, mapping, aligned):
    """New lexemes, with the unvocalised lexeme of extrabiblical."""
    FX = apiX.F
    info = {}
    for (unit, node) in aligned:
        w = unit[0]
        key = (FX.lex.v(w), xbKind(FX, w))
        if key in mapping and mapping[key][1] == "new":
            info.setdefault(mapping[key][0], (FX.sp.v(w), FX.lex_utf8.v(w)))
    rows = {}
    for (lex, (sp, utf8)) in sorted(info.items()):
        rows[lex] = dict(
            gloss="", language="Hebrew", lex=lex, lexCons=core(lex), root="",
            sp=sp, voc_lex="", voc_lex_utf8=utf8,
        )
    with open(f"{OUT_BASE}/dss_lex.csv", "w", encoding="utf8", newline="") as fh:
        fields = ["gloss", "language", "lex", "lexCons", "root", "sp", "voc_lex", "voc_lex_utf8"]
        writer = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        writer.writerows(rows.values())
    return rows


def writeReview(review):
    with open(f"{OUT_BASE}/review.tsv", "w", encoding="utf8") as fh:
        fh.write("scroll\tnode\tconsonants\treason\tdetails\n")
        for row in review:
            fh.write("\t".join(str(x) for x in row) + "\n")


if __name__ == "__main__":
    produce()
