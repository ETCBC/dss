import os
from shutil import rmtree

from tf.compose import modify


BASE_NAAIJER = os.path.expanduser("~/local/dss/additions")
FILES_NAAIJER = """
    biblical_scrolls_clause_phrase_boundaries.csv
    lexemes_non_bib_books.csv
    lexemes_pos_gn_all_bib_books_with_hebrew.csv
    nu_ps_all_scrolls.csv
    vs_vt_all_scrolls.csv
""".strip().split()

FILE_COLUMNS = {
    0: [5, 6, 7, 8],
    1: [4],
    2: [5, 7, 9, 11],
    3: [3, 5],
    4: [3, 5],
}

BASE = os.path.expanduser("~/github/etcbc/dss/tf")
SOURCE = "0.7"
DEST = "0.8"

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
    g_cons=dict(
        valueType="str", description="consonantal word in ETCBC representation",
    ),
    gn_etcbc=dict(
        valueType="str", description="grammatical gender in ETCBC vocabulary",
    ),
    lex_etcbc=dict(
        valueType="str", description="consonantal lexeme in ETCBC representation",
    ),
    nu_etcbc=dict(
        valueType="str", description="grammatical number in ETCBC vocabulary",
    ),
    sp_etcbc=dict(valueType="str", description="part-of-speech in ETCBC vocabulary",),
    ps_etcbc=dict(
        valueType="str", description="grammatical person in ETCBC vocabulary",
    ),
    vs_etcbc=dict(valueType="str", description="verbal stem in ETCBC vocabulary",),
    vt_etcbc=dict(valueType="str", description="verbal tense in ETCBC vocabulary",),
)
for (k, v) in FEATURE_META.items():
    v.update(META)


def readFile(fileNum, data):
    """Reads a file from Martijn and extracts data.

    The file is given by de index in `FILES_NAAIJER`.

    The columns as specified in `FILE_COLUMNS` are extracted.
    The keys in `FILE_COLUMNS` are the file numbers.
    The values are the columns to extract.

    The result is delivered as a dict whose keys are the column names
    of the columns extracted, and whose values are dicts of TF nodes as keys
    and column values as values.
    """

    with open(f"{BASE_NAAIJER}/{FILES_NAAIJER[fileNum]}") as fh:
        columns = FILE_COLUMNS[fileNum]
        header = next(fh).rstrip("\n").split(",")
        for i in columns:
            data.setdefault(header[i], {})

        for line in fh:
            values = line.rstrip("\n").split(",")
            for i in columns:
                data[header[i]][int(values[0])] = values[i]


def readFiles():
    data = {}
    for fileNum in range(1, len(FILES_NAAIJER)):
        print(f"reading {FILES_NAAIJER[fileNum]}")
        readFile(fileNum, data)

    for (feat, featData) in data.items():
        print(f"feature {feat} assigning values to {len(featData)} nodes")

    return data


"""
def readBoundaries():
    with open(f"{BASE_NAAIJER}/{FILES_NAAIJER[2]}") as fh:
        next(fh)
        nodes = [int(line.split(",")[0]) for line in fh]
    fileNum = 0
    data = {}
    with open(f"{BASE_NAAIJER}/{FILES_NAAIJER[fileNum]}") as fh:
        columns = FILE_COLUMNS[fileNum]
        header = next(fh).rstrip("\n").split(",")
        for i in columns:
            data.setdefault(header[i], {})

        for (node, line) in zip(nodes, fh):
            values = line.rstrip("\n").split(",")
            for i in columns:
                data[header[i]][node] = values[i]

    for (feat, featData) in data.items():
        print(f"property {feat} assigning values to {len(featData)} nodes")

    A = use('dss:clone', checkout="clone", version='0.7')
    api = A.api
    E = api.E
    Eoslots = E.oslots.s

    lastClause = 0
    curClause = []
    clauseSlots = {}
    lastPhrase = 0
    curPhrase = []
    phraseSlots = {}

    clauseStartFeat = data['start_of_clause']
    clauseEndFeat = data['end_of_clause']
    phraseStartFeat = data['start_of_phrase']
    phraseEndFeat = data['end_of_phrase']

    B = 'b'
    E = 'e'

    for w in nodes:
        slots = Eoslots(w)
        (b, e) = (slots[0], slots[-1])
        clauseStart = clauseStartFeat[w] == B
        clauseEnd = clauseEndFeat[w] == E
        phraseStart = phraseStartFeat[w] == B
        phraseEnd = phraseEndFeat[w] == E
"""


def produce():
    featureData = readFiles()
    # boundaries = readBoundaries()

    target = f"{BASE}/{DEST}"
    if os.path.exists(target):
        answer = input(f"{target} exists. Delete it? [yn] ")
        if answer == "y":
            rmtree(target)

    modify(
        f"{BASE}/{SOURCE}",
        target,
        addFeatures=dict(nodeFeatures=featureData),
        featureMeta=FEATURE_META,
    )


produce()
