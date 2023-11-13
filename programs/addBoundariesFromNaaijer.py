import os
from shutil import rmtree

from tf.app import use
from tf.compose import modify


BASE = os.path.expanduser("~/github/etcbc/dss")
TF_BASE = f"{BASE}/tf"
BASE_NAAIJER = os.path.expanduser(f"{BASE}/_local/additions")

FILE_NAAIJER = """isa_clauses_phrases.csv"""

SOURCE = "0.8"
DEST = "0.9"

META = dict(
    acronym="dss-additions",
    convertedBy="Martijn Naaijer and Dirk Roorda",
    createdBy="Martin G. Abegg, Martijn Naaijer, ETCBC",
    createdDate="2020",
    description="Dead Sea Scrolls: additions based on BHSA and machine learning",
    license="Creative Commons Attribution-NonCommercial 4.0 International License",
    licenseUrl="http://creativecommons.org/licenses/by-nc/4.0/",
    source="Martijn Naaijer's data files, personal communication",
    valueType="str",
)

FEATURE_META = dict(
    nr=dict(
        valueType="int",
        description="number of clause or phrase",
    ),
)
for (k, v) in FEATURE_META.items():
    v.update(META)


def readBoundariesPlain():
    data = {}

    with open(f"{BASE_NAAIJER}/{FILE_NAAIJER}") as fh:
        next(fh)
        for line in fh:
            (w, scroll, book, verse, word, clauseNr, phraseNr) = line.rstrip(
                "\n"
            ).split(",")
            data[int(w)] = (word, book, clauseNr, phraseNr)

    return data


def getWordSlots():
    """Get the slots (= signs) for each word in the original data.
    """

    A = use("ETCBC/dss:clone", checkout="clone", version=SOURCE)
    api = A.api
    Eoslots = api.E.oslots
    Fotype = api.F.otype

    wordSlots = {}
    for w in Fotype.s("word"):
        wordSlots[w] = set(Eoslots.s(w))

    return wordSlots


def readBoundaries():
    """Read the boundary data.

    In notebook `boundariesFromNaaijer.ipynb` we check the data first.
    It turns out that the first column contains true word nodes.
    Some nodes are missing, but they are exactly those that correspond to the text `00 `,
    which corresponds to a sof pasuq at the end of a verse.

    We can safely keep them out of phrases and clauses.

    Note that the slot type in the DSS is `sign`, not `word`.
    When we add clauses and phrases, we must map them to signs.
    That is why we make use of a mapping of words to the signs\they contain.

    After reading the file, we compose a data structure that can be fed into the
    `modify` function of Text-Fabric.
    See https://annotation.github.io/text-fabric/compose/modify.html
    """

    wordSlots = getWordSlots()

    clauseNrs = {}
    phraseNrs = {}

    clauseNodeIndex = {}
    phraseNodeIndex = {}

    maxClauseNode = 0
    maxPhraseNode = 0

    clauseSlots = {}
    phraseSlots = {}

    with open(f"{BASE_NAAIJER}/{FILE_NAAIJER}") as fh:
        next(fh)
        for line in fh:
            (w, scroll, book, verse, word, clauseNr, phraseNr) = line.rstrip(
                "\n"
            ).split(",")

            w = int(w)
            slots = wordSlots[w]

            if (book, clauseNr) not in clauseNodeIndex:
                maxClauseNode += 1
                clauseNodeIndex[(book, clauseNr)] = maxClauseNode
                clauseNrs[maxClauseNode] = clauseNr
            clauseNode = clauseNodeIndex[(book, clauseNr)]
            clauseSlots.setdefault(clauseNode, set())
            clauseSlots[clauseNode] |= slots

            if (book, phraseNr) not in phraseNodeIndex:
                maxPhraseNode += 1
                phraseNodeIndex[(book, phraseNr)] = maxPhraseNode
                phraseNrs[maxPhraseNode] = phraseNr
            phraseNode = phraseNodeIndex[(book, phraseNr)]
            phraseSlots.setdefault(phraseNode, set())
            phraseSlots[phraseNode] |= slots

    return dict(
        phrase=dict(
            nodeFrom=1,
            nodeTo=maxPhraseNode,
            nodeSlots=phraseSlots,
            nodeFeatures=dict(nr=phraseNrs),
        ),
        clause=dict(
            nodeFrom=1,
            nodeTo=maxClauseNode,
            nodeSlots=clauseSlots,
            nodeFeatures=dict(nr=clauseNrs),
        ),
    )


def produce():
    data = readBoundaries()

    target = f"{TF_BASE}/{DEST}"
    if os.path.exists(target):
        rmtree(target)

    modify(
        f"{TF_BASE}/{SOURCE}",
        target,
        addTypes=data,
        featureMeta=FEATURE_META,
    )


if __name__ == "__main__":
    produce()
