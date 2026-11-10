"""Make data version 2.0.5: morph_etcbc of 1Qisaa agrees with g_cons.

In version 2.0.2 (`morphemes.py`) `g_cons` of 1Qisaa was derived from
`morph_etcbc`, but where the result did not agree with the consonants of the
scroll, the value of version 1.9 was taken. The morpheme features
(`g_pfm_etcbc` ... `g_prs_etcbc`) were still derived from `morph_etcbc`, so for
66 words they do not add up to `g_cons`.

This program corrects `morph_etcbc` of those words, per node, and derives the
morpheme features again in the same way as `morphemes.py`. The corrections are
of two kinds:

*   letters that the parse marks as not realised (`(`), but that the scroll
    writes, e.g. the doubled yod of gentilics: `KFD(J(M/JM` becomes `KFDJ(M/JM`;
*   letters that the scroll writes in addition to the parse, marked with `&`,
    e.g. the doubled waw of `<WWN`: `<WN/WTJ+NW` becomes `<W&WN/WTJ+NW`.

For 13 words the parse itself was corrected by hand. Two of them (Isa 35:8
and 41:27) are harmonised with the interpretation of the BHSA. For one word
(Isa 17:7) the corrected parse also changes `nu_etcbc` and `gn_etcbc`, given
in `OTHER_FIXES`.

The program checks that the old value of `morph_etcbc` is still present and that
the new value realises exactly `g_cons`.
"""

import os
import sys
from shutil import copy

from tf.fabric import Fabric

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from morphemes import MORPHEME_FEATURES, realise, segment  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_BASE = f"{BASE}/tf"

SOURCE = "2.0.4"
DEST = "2.0.5"

# node: (old morph_etcbc, new morph_etcbc)
MORPH_FIXES = {
    # letters marked as not realised that the scroll writes
    1898244: ("PLCT(J/JM", "PLCTJ/JM"),  # PLCTJJM
    1899303: ("PLCT(J/JM", "PLCTJ/JM"),  # PLCTJJM
    1899744: ("KFD(J(M/JM", "KFDJ(M/JM"),  # KFDJJM
    1902688: ("KFD(J(M/JM", "KFDJ(M/JM"),  # KFDJJM
    1910706: ("KFD(J(M/JM", "KFDJ(M/JM"),  # KFDJJM
    1912157: ("KFD(J(M/JM", "KFDJ(M/JM"),  # KFDJJM
    1912208: ("KFD(J(M/JM", "KFDJ(M/JM"),  # KFDJJM
    1912664: ("KFD(J(M/JM", "KFDJ(M/JM"),  # KFDJJM
    1912762: ("KFD(J(M/JM", "KFDJ(M/JM"),  # KFDJJM
    1902530: ("KT(J(J(M/JM", "KTJ(J(M/JM"),  # KTJJM
    1902677: ("KT(J(J(M/JM", "KTJ(J(M/JM"),  # KTJJM
    1901405: ("<W<(J(M/JM", "<W<J(M/JM"),  # <W<JJM
    1915866: ("X&WPC(J/JM", "X&WPCJ/JM"),  # XWPCJJM
    1901005: ("B&WZ(Z[/J+NW", "B&WZZ[/J+NW"),  # BWZZJNW
    1914419: ("G&WZ(Z[/J+H", "G&WZZ[/J+H"),  # GWZZJH
    1916218: ("!N!GC(C[:d", "!N!GCC[:d"),  # NGCC
    1900282: ("!M!](H](NK(H[/+(K&H", "!M!](H](NK(H[/+K&H"),  # MKKH
    1913575: ("!>!](H]PR(H[+W", "!>!](H]PRH[+W"),  # >PRHW
    1903074: ("]HT]R&W<(<=[H", "]HT]R&W<<=[H"),  # HTRW<<H
    1910740: ("<&WZ(WZ=/", "<&WZWZ=/"),  # <WZWZ
    # letters that the scroll writes in addition to the parse
    1895275: ("R>CWN/H", "R>&JCWN/H"),  # R>JCWNH
    1897745: ("GD(J(H/WTJ+W", "GD(J(H&W/WTJ+W"),  # GDWWTJW
    1898257: ("Z(>&WT", "Z(>&W&WT"),  # ZWWT
    1902070: ("XZ(JWN/", "XZ(JW&WN/"),  # XZWWN
    1905921: ("YJ(WN/", "YJ(W&JN/"),  # YJJN
    1907887: ("SPR(WJM=/", "SPR(WJ&JM=/"),  # SPRJJM
    1913064: ("S(J&WNJM/", "S(J&WNJ&JM/"),  # SWNJJM
    1915209: ("]N]LW(H[/JM", "]N]LW(H&J[/JM"),  # NLWJJM
    1905212: ("<&HWN/", "<&HW&WN/"),  # <HWWN
    1908396: ("XDN/", "X&WDN/"),  # XWDN
    1909295: ("THW/", "THW&W/"),  # THWW
    1909483: ("QY(H/WT:c", "QY(H&W/WT:c"),  # QYWWT
    1909666: ("QY(H/WT:c", "QY(H&W/WT:c"),  # QYWWT
    1909613: ("QY(H&>/WT:c", "QY(H&>&W/WT:c"),  # QY>WWT
    1908149: ("!!](H]C>(H[/WT", "!!](H]C>(H&W[/WT"),  # C>WWT
    1913338: ("<WN/WTJ+KM&H", "<W&WN/WTJ+KM&H"),  # <WWNWTJKMH
    1917970: ("<WN/WTJ+KM&H", "<W&WN/WTJ+KM&H"),  # <WWNWTJKMH
    1914375: ("<WN/WTJ+NW", "<W&WN/WTJ+NW"),  # <WWNWTJNW
    1916268: ("<WN/WTJ+NW", "<W&WN/WTJ+NW"),  # <WWNWTJNW
    1917768: ("<WN/WTJ+NW", "<W&WN/WTJ+NW"),  # <WWNWTJNW
    1914505: ("<WN/WT+M", "<W&WN/WT+M"),  # <WWNWTM
    1917546: ("Y&W>N/+W", "Y&W>&WN/+W"),  # YW>WNW
    1908363: ("!J!CWB[", "!J!CW&WB["),  # JCWWB
    1901528: ("HJH[", "HJ&JH["),  # HJJH
    1918791: ("R>(H[W", "R>(H&W[W"),  # R>WW
    1902120: ("!T!](H](>WY[W", "!T!](H](>WY[W&W"),  # TWYWW
    1916352: ("SMK[(H&T+HW", "SMK[(H&T+HW&W"),  # SMKTHWW
    1916583: ("!T=!<WP[NH", "!T=!<WP&P[NH"),  # T<WPPNH
    1917469: ("GML[+M", "GM&>L[+M"),  # GM>LM
    1904333: ("MSK&SH=/", "MSK&S&KH=/"),  # MSKSKH
    1911490: ("HR/JM", "HR&R/JM"),  # HRRJM
    1908234: ("!!NV(<[W", "!!NV&W<["),  # NVW<
    1909165: (">L&WH(J(M/(J&H+KM", ">L&WH(J(M/(J&H+KM&H"),  # >LWHHKMH
    # parses corrected by hand (reviewed by the editor)
    1894993: ("]N](JTR[H", "]N](JTR[T"),  # Isa 1:8 NTRT: feminine participle in -T
    1896414: ("]H](JC(B[TM", "JC(B[TM"),  # Isa 5:8 JCTM: qal perf, B not written
    1897139: ("!!NW<[/:c", "!!N(W<[/:c"),  # Isa 7:2 N<: infc without W
    1899699: ("!J!](N]CSS[W", "!J!](N]CS(S[W"),  # Isa 13:16 JCSW: one S for CSS
    1900854: ("<&WF(H[/J+(W", "<&WF(H[/+WHJ"),  # Isa 17:7 <WFWHJ: suffix -WHJ
    1900927: ("!T!F(WG&F&G[&FJLd", "!T!F(WG&F&G[&FJ:d"),  # Isa 17:11 TFGFGFJ
    1901047: ("QW==/", "QW&Q&W==/"),  # Isa 18:2 QWQW: one word in the scroll
    1901165: ("QW==/", "QW&Q&W==/"),  # Isa 18:7 QWQW: idem
    1901344: ("C&WT&WT/J+H", "C&WT(WT/J+H"),  # Isa 19:10 CWTTJH
    1908182: ("JD<[TJ&J&>", "JD<[TJ&>"),  # Isa 37:28 JD<TJ>
    1911453: ("!(T=&J!](H(T]JSD[", "!J!]T]JSD["),  # Isa 44:28 JTJSD
    # harmonised with the BHSA
    # Isa 35:8 J<WBWRNH: BHSA qal impf 3ms + energic N + suffix 3ms (prs HW);
    # the suffix is written with H, coded H= as the BHSA codes a 3ms suffix written with H
    1906991: ("!J!<&WBR[~N+(HW", "!J!<&WB&WR[~N+H="),
    # Isa 41:27 HNWMH: BHSA HNH + suffix 3mp (HN.@M); the scroll writes the suffix
    # with W and paragogic H, as in KM&H
    1909992: ("HN(H", "HN(H+&WM&H"),
}

# node: {feature: (old value, new value)}; follows from a corrected parse
OTHER_FIXES = {
    # Isa 17:7 <WFWHJ: singular participle with suffix, as in the BHSA
    1900854: dict(nu_etcbc=("pl", "sg"), gn_etcbc=(None, "m")),
}


def produce():
    sourceDir = f"{TF_BASE}/{SOURCE}"
    destDir = f"{TF_BASE}/{DEST}"

    features = ("morph_etcbc", "g_cons", "lex_etcbc", "nu_etcbc", "gn_etcbc",
                *MORPHEME_FEATURES.values())
    TF = Fabric(locations=sourceDir, silent="deep")
    TF.load(" ".join(features), silent="deep")

    data = {f: dict(TF.features[f].data) for f in features}
    meta = {f: dict(TF.features[f].metaData) for f in features}

    errors = []
    for (w, (old, new)) in MORPH_FIXES.items():
        current = data["morph_etcbc"].get(w)
        if current != old:
            errors.append(f"{w}: expected {old!r}, found {current!r}")
        gCons = data["g_cons"].get(w)
        if realise(new) != gCons:
            errors.append(f"{w}: {new!r} realises {realise(new)!r}, not {gCons!r}")
    if errors:
        print("\n".join(errors))
        raise ValueError("corrections do not fit the source data")

    changes = []
    for (w, (old, new)) in MORPH_FIXES.items():
        data["morph_etcbc"][w] = new
        lex = data["lex_etcbc"].get(w, "")
        for (k, v) in segment(new).items():
            f = MORPHEME_FEATURES[k]
            before = data[f].pop(w, None)
            if v and not (k == "lex" and lex == "="):
                data[f][w] = v
            after = data[f].get(w)
            if before != after:
                changes.append((w, f, before, after))

    for (w, fixes) in OTHER_FIXES.items():
        for (f, (old, new)) in fixes.items():
            data[f][w] = new
            changes.append((w, f, old, new))

    os.makedirs(destDir, exist_ok=True)
    for name in os.listdir(sourceDir):
        if name.endswith(".tf") and os.path.isfile(f"{sourceDir}/{name}"):
            copy(f"{sourceDir}/{name}", f"{destDir}/{name}")

    saved = ("morph_etcbc", "nu_etcbc", "gn_etcbc", *MORPHEME_FEATURES.values())
    TF = Fabric(locations=destDir, silent="deep")
    TF.save(
        nodeFeatures={f: data[f] for f in saved},
        metaData={f: meta[f] for f in saved},
        location=destDir,
        silent="deep",
    )

    print(f"Written {len(saved)} features to {destDir}")
    print(f"{len(MORPH_FIXES)} words with a corrected morph_etcbc")
    print(f"{len(changes)} changes in other features:")
    for (w, f, before, after) in changes:
        print(f"\t{w}\t{f}\t{before}\t{after}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    produce()
