"""Draft of the morphological parsing of 1QSa (steps 3 and 4 of the plan).

The draft is meant to be corrected by hand (by Saulo de Oliveira Cantanhêde),
after which it is converted into the data like 1QpHab.

Input:

*   DSS (version `SOURCE`): the words of 1QSa, their `lex_etcbc` and the tags
    of Abegg (`morpho`, `vs`, `vt`, `st`, `gn`, `nu`, `ps`);
*   the parsings of the scrolls that have one (`PARSED_SCROLLS`);
*   the BHSA: analyses and pointed forms of the same lexemes;
*   a transcription of a vocalised edition of 1QSa, one line per scroll line
    (`col:line<TAB>text`). Because of copyright this file is not part of the
    repository; its location is given as an argument.

For every DSS word of 1QSa with consonants (consecutive word nodes without
space between them form one written word, as in `import/1QpHab/mapping.txt`):

1.  candidate analyses (`morph_etcbc` strings) are collected:
    *   `lookup`: the analyses of the same consonants in the parsed scrolls;
    *   `bhsa`: the BHSA occurrences of the same lexeme, whose paradigmatic
        morphemes are combined with the consonants of the scroll; this is only
        allowed if the differences are vowel letters or weak letters;
2.  candidates whose consonants do not agree with the scroll are rejected;
3.  the candidates are scored: agreement with the vowels of the edition
    (compared with the pointed BHSA forms of the candidate), with the lexeme
    (`lex_etcbc`) and with the tags of Abegg, and the frequency in the parsed
    scrolls;
4.  the state of nominal forms without suffix is added (`:a`, `:c`), from the
    tags of Abegg, else from the BHSA reading that was chosen.

Fully reconstructed words for which the edition has different consonants are
not parsed.

Output, in the directory given as argument (outside the repository, because
the review list contains the vocalised text):

*   `dss_out` and `mapping.txt`: the draft, in the format of `import/1QpHab`;
*   `review.tsv`: per word the chosen analysis, the basis, the confidence and
    the other candidates, for correction by hand.

Usage: python programs/draft1QSa.py <vocalised.tsv> <output directory>
"""

import collections
import difflib
import os
import re
import sys

from tf.fabric import Fabric

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add1QpHab import analyse, stem, tense, verbPgn  # noqa: E402
from morphemes import realise  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_BASE = f"{BASE}/tf"
SOURCE = "2.0.4"
SCROLL = "1QSa"
PARSED_SCROLLS = ("11Q19", "1Qisaa", "1QpHab", "1QS", "1QM", "1QHa")
BHSA_CANDIDATES = (
    "~/text-fabric-data/github/ETCBC/bhsa/tf/2021",
    "~/text-fabric-data/etcbc/bhsa/tf/2021",
)

# letters that may be written or not without changing the analysis
VOWEL_LETTERS = set("WJH>")
WEAK_LETTERS = set("WJH>NT")

ABEGG_VS = dict(qal="qal", piel="piel", pual="pual", hifil="hif", hofal="hof",
                nifal="nif", hitpael="hit")
ABEGG_NU = dict(s="sg", p="pl", d="du")

HEB = dict(zip("אבגדהוזחטיכךלמםנןסעפףצץקרשת", ">BGDHWZXVJKKLMMNNS<PPYYQRCT"))
POINTS = set(chr(c) for c in range(0x05B0, 0x05BD)) | {"ׁ", "ׂ", "ׇ"}


# ---------------------------------------------------------------------------
# pointed text
# ---------------------------------------------------------------------------


def pointedLetters(word):
    """Consonants of a pointed Hebrew word with their points.

    Returns a list of (consonant, points). Vowel letters that only carry
    a vowel of the preceding letter (holem male, shureq, hireq or sere with
    yod) give their vowel to the preceding letter.
    """
    letters = []
    for ch in word:
        if ch in HEB:
            letters.append([HEB[ch], set()])
        elif ch in POINTS and letters:
            letters[-1][1].add(ch)
    result = []
    for (c, pts) in letters:
        if c == "W" and pts in ({"ֹ"}, {"ּ"}) and result:
            # holem male or shureq
            result[-1][1].add("o" if "ֹ" in pts else "u")
            continue
        if c == "J" and not pts and result and result[-1][1] & {"ִ", "ֵ", "ֶ"}:
            continue
        if c in {"W", "J", ">", "H"} and not pts and result:
            continue
        pts = {"o" if p == "ֹ" else "u" if p == "ֻ" else p for p in pts}
        result.append((c, pts))
    return [(c, frozenset(pts)) for (c, pts) in result]


def vowelScore(edition, bhsa):
    """How well two pointed forms agree: matching minus differing points."""
    a = pointedLetters(edition)
    b = pointedLetters(bhsa)
    ca = [c.replace("C", "#") for (c, p) in a]
    cb = [c.replace("C", "#") for (c, p) in b]
    score = 0
    matcher = difflib.SequenceMatcher(None, ca, cb, autojunk=False)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            pa = a[block.a + k][1] - {"ׁ", "ׂ"}
            pb = b[block.b + k][1] - {"ׁ", "ׂ"}
            score += len(pa & pb) - len(pa ^ pb)
    return score


def translit(word):
    out = []
    for (i, ch) in enumerate(word):
        if ch in HEB:
            c = HEB[ch]
            if ch == "ש":
                nxt = word[i + 1:i + 4]
                c = "C" if "ׁ" in nxt else "F" if "ׂ" in nxt else "#"
            out.append(c)
    return "".join(out)


def readVocalised(path):
    lines = {}
    with open(path, encoding="utf8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            (ref, text) = line.rstrip("\n").split("\t")
            text = re.sub(r"\{.*?\}", "", text)
            words = [re.sub(r"[\[\]]", "", w) for w in text.split()]
            lines[ref] = [w for w in words if translit(w)]
    return lines


# ---------------------------------------------------------------------------
# morphology strings
# ---------------------------------------------------------------------------


def present(v):
    return v not in {"n/a", "absent", None}


def core(lex):
    return re.sub(r"[/\[=]", "", lex)


def kind(lex):
    return "[" if lex.endswith("[") else "/" if lex.endswith("/") else ""


BHSA_CONSONANTS = set("BGDHWZXVJKLMNSPYQRFCT<>")

# morphemes of a BHSA word: (feature, realised feature, opening, closing marker)
MORPHEMES = (
    ("pfm", "g_pfm", "!", "!"),
    ("vbs", "g_vbs", "]", "]"),
    ("lex", "g_lex", "", ""),
    ("vbe", "g_vbe", "[", ""),
    ("nme", "g_nme", "/", ""),
    ("uvf", "g_uvf", "~", ""),
    ("prs", "g_prs", "+", ""),
)
# where the scroll may write a vowel letter that the BHSA does not write
MAY_ADD = dict(lex=VOWEL_LETTERS, vbe={"H"}, prs={"H"})
# where the scroll may leave out a letter that the BHSA writes
MAY_DROP = dict(lex=VOWEL_LETTERS, prs={"H"})


def bhsaTokens(FB, w):
    """The morphemes of a BHSA word as tokens, in the spelling of the BHSA.

    Returns a list of (morpheme, opening, closing, eq, tokens), where tokens are
    (kind, letter): `m` paradigmatic and written, `p` paradigmatic but not
    written, `w` written but not paradigmatic.
    """
    lex = FB.lex.v(w)
    result = []
    for (feat, gFeat, open_, close) in MORPHEMES:
        if feat == "lex":
            par = core(lex)
            eq = re.sub(r"[^=]", "", lex)
        else:
            value = getattr(FB, feat).v(w)
            if not present(value):
                if feat == "vbe" and kind(lex) == "[":
                    result.append(("vbe", "[", "", "", []))
                elif feat == "nme" and kind(lex) == "/":
                    result.append(("nme", "/", "", "", []))
                continue
            par = value.replace("=", "")
            eq = re.sub(r"[^=]", "", value)
        written = "".join(c for c in (getattr(FB, gFeat).v(w) or "") if c in BHSA_CONSONANTS)
        result.append((feat, open_, close, eq, alignTokens(par, written)))
    return result


def alignTokens(par, written):
    n, m = len(par), len(written)
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            lcs[i][j] = lcs[i + 1][j + 1] + 1 if par[i] == written[j] else max(lcs[i + 1][j], lcs[i][j + 1])
    tokens = []
    (i, j) = (0, 0)
    while i < n or j < m:
        if i < n and j < m and par[i] == written[j] and lcs[i][j] == lcs[i + 1][j + 1] + 1:
            tokens.append(["m", par[i]])
            i += 1
            j += 1
        elif i < n and (j == m or lcs[i + 1][j] >= lcs[i][j + 1]):
            tokens.append(["p", par[i]])
            i += 1
        else:
            tokens.append(["w", written[j]])
            j += 1
    return tokens


def toScroll(morphemes, written):
    """Adapt the tokens of a BHSA word to the consonants of the scroll.

    Only vowel letters may be added or left out, and only where `MAY_ADD` and
    `MAY_DROP` allow it. Returns the adapted morphemes and the number of
    adaptations, or None if the word cannot be written like this.
    """
    real = [(mi, ti) for (mi, (feat, o, c, eq, toks)) in enumerate(morphemes)
            for (ti, (k, ch)) in enumerate(toks) if k in {"m", "w"}]
    if not real:
        return None
    letters = [morphemes[mi][4][ti][1] for (mi, ti) in real]
    same = lambda a, b: a == b or (b == "#" and a in "CF")
    n, m = len(letters), len(written)
    INF = 10 ** 6
    cost = [[INF] * (m + 1) for _ in range(n + 1)]
    cost[n][m] = 0
    for i in range(n, -1, -1):
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            best = INF
            if i < n and j < m and same(letters[i], written[j]):
                best = cost[i + 1][j + 1]
            if i < n:
                feat = morphemes[real[i][0]][0]
                if letters[i] in MAY_DROP.get(feat, set()):
                    best = min(best, cost[i + 1][j] + 1)
            if j < m:
                mi = real[i - 1][0] if i else (real[0][0] if real else 0)
                feat = morphemes[mi][0] if morphemes else "lex"
                if written[j] in MAY_ADD.get(feat, set()):
                    best = min(best, cost[i][j + 1] + 1)
            cost[i][j] = best
    if cost[0][0] >= INF:
        return None
    new = [(feat, o, c, eq, [list(t) for t in toks]) for (feat, o, c, eq, toks) in morphemes]
    inserts = collections.defaultdict(list)
    (i, j) = (0, 0)
    while i < n or j < m:
        if i < n and j < m and same(letters[i], written[j]) and cost[i][j] == cost[i + 1][j + 1]:
            (mi, ti) = real[i]
            new[mi][4][ti][1] = letters[i] if letters[i] != "#" else written[j]
            i += 1
            j += 1
        elif i < n and letters[i] in MAY_DROP.get(morphemes[real[i][0]][0], set()) and cost[i][j] == cost[i + 1][j] + 1:
            (mi, ti) = real[i]
            k = new[mi][4][ti][0]
            new[mi][4][ti][0] = "p" if k == "m" else "x"
            i += 1
        else:
            (mi, ti) = real[i - 1] if i else (real[0][0], -1)
            inserts[(mi, ti)].append(written[j])
            j += 1
    result = []
    for (mi, (feat, o, c, eq, toks)) in enumerate(new):
        out = []
        for ch in inserts.get((mi, -1), []):
            out.append(["w", ch])
        for (ti, t) in enumerate(toks):
            if t[0] != "x":
                out.append(t)
            for ch in inserts.get((mi, ti), []):
                out.append(["w", ch])
        # an added letter next to the same paradigmatic letter: it is written
        k = 0
        while k < len(out) - 1:
            (a, b) = (out[k], out[k + 1])
            if {a[0], b[0]} == {"p", "w"} and a[1] == b[1]:
                out[k:k + 2] = [["m", a[1]]]
            k += 1
        result.append((feat, o, c, eq, out))
    return (result, cost[0][0])


def serialise(morphemes, ann):
    out = []
    for (feat, o, c, eq, toks) in morphemes:
        body = "".join(ch if k == "m" else f"({ch}" if k == "p" else f"&{ch}" for (k, ch) in toks)
        if feat == "prs" and ann:
            out.append(f":{ann}")
            ann = ""
        out.append(f"{o}{body}{eq}{c}")
    if ann:
        out.append(f":{ann}")
    return "".join(out)


def annotations(vs, vt):
    ann = ""
    if vs == "piel":
        ann += "d"
    elif vs in {"pual", "pasq"}:
        ann += "du"
    elif vs == "hof":
        ann += "u"
    if vt == "ptcp" and vs == "qal":
        ann += "p"
    return ann


def bhsaMorph(FB, w, written, cache):
    """The morph string of a BHSA word, written with the consonants of the scroll."""
    if w not in cache:
        cache[w] = bhsaTokens(FB, w)
    adapted = toScroll(cache[w], written)
    if adapted is None:
        return None
    (morphemes, n) = adapted
    return (serialise(morphemes, annotations(FB.vs.v(w), FB.vt.v(w))), n)


def stripState(morph):
    """Remove the state markers a and c from the annotations."""
    def fix(m):
        rest = m.group(1).replace("a", "").replace("c", "")
        return f":{rest}" if rest else ""
    return re.sub(r":([a-z]+)", fix, morph)


def addState(morph, st):
    if st not in {"a", "c"} or "+" in morph:
        return morph
    a = analyse(morph)
    if not a["nominal"]:
        return morph
    if a["verbal"] and a["pfm"] is not None and a["pfm"] != "M":
        # infinitive: a would mean infinitive absolute
        return morph
    match = re.search(r":([a-z]+)$", morph)
    if match:
        return morph[:match.start()] + f":{match.group(1)}{st}"
    return f"{morph}:{st}"


def describe(morph):
    """Analysis derived from a morph string: (lex, vs, vt, ps, nu, gn)."""
    parts = morph.split("-")
    a = analyse(parts[0])
    if not a["verbal"]:
        return (a["lex"], None, None, None, None, None)
    vt = tense(a, False)
    return (a["lex"], stem(a), vt, *verbPgn(a, vt))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def bhsaPath():
    for path in BHSA_CANDIDATES:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return path
    raise FileNotFoundError("BHSA 2021 not found")


def produce(vocPath, outDir):
    sys.stdout.reconfigure(encoding="utf-8")
    TF = Fabric(locations=f"{TF_BASE}/{SOURCE}", silent="deep")
    api = TF.load(
        "scroll fragment line glyphe type rec after morph_etcbc lex_etcbc"
        " morpho sp vs vt st gn nu ps", silent="deep",
    )
    F, L = api.F, api.L
    scrolls = {F.scroll.v(s): s for s in F.otype.s("scroll")}

    def cons(w):
        return "".join(
            F.glyphe.v(c) for c in L.d(w, otype="sign") if F.type.v(c) == "cons"
        ).upper()

    def recStatus(w):
        signs = [c for c in L.d(w, otype="sign") if F.type.v(c) == "cons"]
        r = sum(1 for c in signs if F.rec.v(c))
        return "none" if not r else "full" if r == len(signs) else "part"

    # lookup: consonants of a word node -> morph strings in the parsed scrolls
    lookup = collections.defaultdict(collections.Counter)
    for name in PARSED_SCROLLS:
        for w in L.d(scrolls[name], otype="word"):
            m = F.morph_etcbc.v(w)
            if m and m != "=":
                lookup[cons(w)][stripState(m)] += 1

    # the written words of 1QSa: consecutive nodes without space between them
    units = []
    for ln in L.d(scrolls[SCROLL], otype="line"):
        ref = f"{F.fragment.v(ln)}:{F.line.v(ln)}"
        cur = []
        for w in L.d(ln, otype="word"):
            cur.append(w)
            if F.after.v(w) is not None:
                if any(cons(x) for x in cur):
                    units.append((ref, [x for x in cur if cons(x)]))
                cur = []
        if any(cons(x) for x in cur):
            units.append((ref, [x for x in cur if cons(x)]))

    # vowels from the edition, per node
    voc = readVocalised(vocPath)
    pointed = {}
    byLine = collections.defaultdict(list)
    for (ref, nodes) in units:
        byLine[ref].append(nodes)
    for (ref, lineUnits) in byLine.items():
        ed = voc.get(ref, [])
        a = [translit(x).replace("C", "#").replace("F", "#") for x in ed]
        d = ["".join(cons(w) for w in nodes) for nodes in lineUnits]
        matcher = difflib.SequenceMatcher(None, a, d, autojunk=False)
        for (op, i1, i2, j1, j2) in matcher.get_opcodes():
            if op != "equal":
                continue
            for (i, j) in zip(range(i1, i2), range(j1, j2)):
                split = splitPointed(ed[i], [cons(w) for w in lineUnits[j]])
                for (w, part) in zip(lineUnits[j], split):
                    pointed[w] = part

    # BHSA occurrences of the lexemes concerned
    lexemes = {F.lex_etcbc.v(w) for (ref, nodes) in units for w in nodes if F.lex_etcbc.v(w)}
    TFB = Fabric(locations=bhsaPath(), silent="deep")
    FB = TFB.load(
        "lex language vs vt ps nu gn st pfm vbs vbe nme prs uvf g_word_utf8"
        " g_pfm g_vbs g_lex g_vbe g_nme g_uvf g_prs", silent="deep"
    ).F
    bhsa = collections.defaultdict(list)
    for w in FB.otype.s("word"):
        if FB.language.v(w) == "Hebrew" and FB.lex.v(w) in lexemes:
            bhsa[FB.lex.v(w)].append(w)
    cache = {}

    def bhsaCandidates(lex, written):
        result = collections.defaultdict(list)
        for b in bhsa.get(lex, []):
            built = bhsaMorph(FB, b, written, cache)
            if built and agreesWritten(built[0], written):
                result[built[0]].append((b, built[1]))
        return result

    rows = []
    review = []
    stats = collections.Counter()
    for (idx, (ref, nodes)) in enumerate(units):
        rec = [recStatus(w) for w in nodes]
        hasEdition = all(w in pointed for w in nodes)
        if all(r == "full" for r in rec) and not hasEdition:
            stats["reconstructed, not in edition: not parsed"] += 1
            continue
        morphs = []
        for (k, w) in enumerate(nodes):
            nextNode = nodes[k + 1] if k + 1 < len(nodes) else None
            (best, info) = chooseNode(F, L, w, cons(w), pointed.get(w), lookup, bhsaCandidates, FB, nextNode)
            morphs.append(best)
            stats[info["confidence"]] += 1
            review.append((ref, w, cons(w), pointed.get(w, ""), best, info))
        rows.append((ref, nodes, "".join(cons(w) for w in nodes), morphs))

    writeOutput(outDir, rows, review)
    print(f"{len(rows)} written words in the draft")
    for (k, n) in stats.most_common():
        print(f"\t{n:5}\t{k}")


def splitPointed(word, nodeCons):
    """Split a pointed written word over its word nodes, by their consonants."""
    if len(nodeCons) == 1:
        return [word]
    parts = []
    cur = ""
    counts = [len(c) for c in nodeCons]
    k = 0
    n = 0
    for ch in word:
        if ch in HEB:
            if n == counts[k] and k < len(counts) - 1:
                parts.append(cur)
                cur = ""
                k += 1
                n = 0
            n += 1
        cur += ch
    parts.append(cur)
    return parts


def agreesWritten(morph, written):
    g = realise(morph.replace("-", ""))
    return len(g) == len(written) and all(
        a == b or (b == "#" and a in "CF") for (a, b) in zip(g, written)
    )


def abeggSuffix(F, L, w):
    """Whether Abegg marks a pronominal suffix: an apostrophe before it."""
    return any(F.glyphe.v(c) == "'" for c in L.d(w, otype="sign")) or F.sp.v(w) == "suff"


def abeggTags(F, w):
    return dict(
        vs=ABEGG_VS.get(F.vs.v(w)), vt=F.vt.v(w) if F.vt.v(w) != "unknown" else None,
        st=F.st.v(w), nu=ABEGG_NU.get(F.nu.v(w)), gn=F.gn.v(w) if F.gn.v(w) in {"m", "f"} else None,
    )


def chooseNode(F, L, w, written, voc, lookup, bhsaCandidates, FB, nextNode):
    lex = F.lex_etcbc.v(w)
    tags = abeggTags(F, w)
    suffix = abeggSuffix(F, L, w)
    cands = {}
    prefix = prefixMorph(F, w, written, voc, nextNode)
    if prefix:
        return prefix
    for (m, n) in lookup.get(written, {}).items():
        if m.endswith(":n"):
            m = m[:-2]
        if agreesWritten(m, written):
            cands.setdefault(m, dict(sources=set(), freq=0, bhsa=[]))
            cands[m]["sources"].add("lookup")
            cands[m]["freq"] += n
    if lex:
        for (m, occs) in bhsaCandidates(lex, written).items():
            cands.setdefault(m, dict(sources=set(), freq=0, bhsa=[]))
            cands[m]["sources"].add("bhsa")
            cands[m]["bhsa"].extend(b for (b, n) in occs)
            cands[m]["adapted"] = min(n for (b, n) in occs)
    if not cands:
        return ("", dict(confidence="no candidate", basis="", others=[], tags=tags, lex=lex))

    scored = []
    for (m, c) in cands.items():
        (dLex, vs, vt, ps, nu, gn) = describe(m)
        score = 0.0
        notes = []
        if lex and dLex == lex:
            score += 4
        elif lex:
            score -= 4
            notes.append(f"lexeme {dLex} not {lex}")
        if ("+" in m) != suffix:
            score -= 4
            notes.append("Abegg " + ("suffix" if suffix else "no suffix"))
        if tags["vs"] and vs and tags["vs"] != vs:
            score -= 2
            notes.append(f"Abegg {tags['vs']}")
        # Abegg does not distinguish the participles of passive stems
        if tags["vt"] and vt and tags["vt"] != vt and {tags["vt"], vt} != {"ptca", "ptcp"}:
            score -= 2
            notes.append(f"Abegg {tags['vt']}")
        vScore = None
        bestOcc = None
        if voc and c["bhsa"]:
            (vScore, bestOcc) = max((vowelScore(voc, FB.g_word_utf8.v(b)), b) for b in c["bhsa"][:400])
            score += vScore
        score += min(c["freq"], 20) / 10
        score += min(len(c["bhsa"]), 20) / 20
        score -= 0.3 * c.get("adapted", 0)
        scored.append((score, m, vScore, bestOcc, notes, c))
    scored.sort(key=lambda x: -x[0])
    (score, m, vScore, bestOcc, notes, c) = scored[0]

    st = tags["st"] or (FB.st.v(bestOcc) if bestOcc else None)
    chosen = addState(m, st)
    margin = score - scored[1][0] if len(scored) > 1 else None
    if len(scored) == 1 and not notes:
        confidence = "single candidate"
    elif margin is not None and margin >= 2 and not notes:
        confidence = "clear choice"
    else:
        confidence = "uncertain"
    basis = "+".join(sorted(c["sources"]))
    if vScore is not None:
        basis += f", vowels {vScore}"
    others = [f"{x[1]} ({x[0]:.1f})" for x in scored[1:6]]
    return (chosen, dict(confidence=confidence, basis=basis, others=others, tags=tags,
                         lex=lex, notes=notes, bhsa=FB.g_word_utf8.v(bestOcc) if bestOcc else ""))


PREFIXES = {"B": "B", "K": "K", "L": "L"}


def prefixMorph(F, w, written, voc, nextNode):
    """Prepositions B, K, L written as one letter: with or without elided article.

    A patah under the preposition marks the elided article (`B-(H`).
    A qamets is ambiguous (article, or before a stressed syllable).
    """
    if written not in PREFIXES or F.lex_etcbc.v(w) != written:
        return None
    tags = abeggTags(F, w)
    base = dict(tags=tags, lex=written, others=[], notes=[], bhsa="")
    if not voc:
        return (written, dict(base, confidence="uncertain", basis="preposition, no vowels",
                              others=[f"{written}-(H"]))
    if "ַ" in voc:
        return (f"{written}-(H", dict(base, confidence="clear choice", basis="preposition, patah: article"))
    if "ָ" in voc and nextNode and (F.lex_etcbc.v(nextNode) or "").endswith("["):
        return (written, dict(base, confidence="clear choice", basis="preposition, qamets before verb"))
    if "ָ" in voc:
        return (written, dict(base, confidence="uncertain", basis="preposition, qamets",
                              others=[f"{written}-(H"]))
    return (written, dict(base, confidence="clear choice", basis="preposition, no article"))


def writeOutput(outDir, rows, review):
    os.makedirs(outDir, exist_ok=True)
    with open(f"{outDir}/dss_out", "w", encoding="utf8") as fh:
        for (i, (ref, nodes, text, morphs)) in enumerate(rows):
            (col, line) = ref.split(":")
            fh.write(f"{i}\t{SCROLL} {col} {line}\t{text}\t{'-'.join(morphs)}\t\n")
    with open(f"{outDir}/mapping.txt", "w", encoding="utf8") as fh:
        for (ref, nodes, text, morphs) in rows:
            n = str(nodes[0]) if len(nodes) == 1 else f"{nodes[0]}-{nodes[-1]}"
            fh.write(f"{n}\t{text}\n")
    with open(f"{outDir}/review.tsv", "w", encoding="utf8") as fh:
        fh.write("ref\tnode\tconsonants\tedition\tdraft_morph\tconfidence\tbasis\tlex_etcbc"
                 "\tabegg\tnotes\tbhsa_form\tother_candidates\n")
        for (ref, w, written, voc, best, info) in review:
            tags = " ".join(f"{k}={v}" for (k, v) in info["tags"].items() if v)
            fh.write("\t".join([
                ref, str(w), written, voc, best, info["confidence"], info.get("basis", ""),
                info.get("lex") or "", tags, "; ".join(info.get("notes", [])),
                info.get("bhsa", ""), " | ".join(info.get("others", [])),
            ]) + "\n")


if __name__ == "__main__":
    produce(sys.argv[1], sys.argv[2])
