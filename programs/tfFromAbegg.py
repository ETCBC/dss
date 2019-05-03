import sys
import os
import collections
import re
import yaml
from shutil import rmtree
from functools import reduce

from tf.fabric import Fabric
from tf.writing.transcription import Transcription
from tf.convert.walker import CV

HELP = 'help'

ARGS = {
    HELP: 'print this help',
    'normwrite': 'write out normalized files',
    'morphdecl': 'only read morphology declaration, nothing else',
    'morphonly': 'only perform morphology checks, do not generate TF',
    'checkonly': 'only perform checks, do not generate TF',
    'check': 'performs checks, generate TF (by default, checks are not performed)',
    'load': 'load TF after generation (by default the TF is not loaded)',
    'loadonly': 'only load existing TF',
    'notf': 'do not generate TF',
    'force': 'let the TF converter continue after errors, so that you can see the final TF',
    'debug': 'run in debug mode',
}

helpText = '''

python3 tfFromAbegg.py options

Converts Abegg's data files to TF
Optionally performs checks.
Optionally loads the TF for the first time.

'''

for (arg, desc) in ARGS.items():
  helpText += f'{arg:<10} : {desc}\n'


# OPTIONS

argValue = {a: None for a in ARGS}
checkSource = None
debug = None

# LOCATIONS

ORG = 'etcbc'
REPO = 'dss'
VERSION_SRC = '1.0'
VERSION_TF = '1.0'

LOCAL_BASE = os.path.expanduser('~/local')
GH_BASE = os.path.expanduser('~/github')

SOURCE_DIR = f'{LOCAL_BASE}/{REPO}/sanitized'
NORM_DIR = f'{LOCAL_BASE}/{REPO}/normalized'
COMPARE_DIR = f'{LOCAL_BASE}/{REPO}/prepared/{VERSION_SRC}'

BASE = f'{GH_BASE}/{ORG}/{REPO}'
PROG_PATH = f'{BASE}/programs'
DECL_PATH = f'{BASE}/yaml'
TF_PATH = f'{BASE}/tf'
OUT_DIR = f'{TF_PATH}/{VERSION_TF}'

META_DIR = f'{BASE}/sources/meta'
SCROLL_TABLE = f'{META_DIR}/mans.txt'

SCROLL_DECL = f'{DECL_PATH}/scroll.yaml'
FIXES_DECL = f'{DECL_PATH}/fixes.yaml'
MORPH_DECL = f'{DECL_PATH}/morph.yaml'

LOG_DIR = f'{BASE}/log'
REPORT = f'{LOG_DIR}/conversion.txt'

TF_DIR = f'{BASE}/tf'


# SOURCE DECODING

TR = Transcription()

BIB = 'bib'
NONBIB = 'nonbib'

SOURCES = (BIB, NONBIB)

NOFIELD = '-'

BOOK = 'book'
CHAPTER = 'chapter'
VERSE = 'verse'
HALFVERSE = 'halfverse'
SCROLL = 'scroll'
FRAGMENT = 'fragment'
LINE = 'line'
CLUSTER = 'cluster'
WORD = 'word'
SIGN = 'sign'
LEX = 'lex'

TRANS = 'trans'

MORPH = 'morph'
BOUND = 'bound'
INTERLINEAR = 'interlinear'
SCRIPT = 'script'

LANG = 'language'

B = 'B'
NOLEX = '0'

# fields

iBIBINFO = 'bibinfo'
iSCROLLINFO = 'scrollinfo'
iSCROLLNAME = 'scrollname'
iSCROLLREF = 'scrollref'
iTRANS = 'trans'
iANALYSIS = 'analysis'
iNUM = 'num'

iCOLS = {
    True: (
        iBIBINFO,
        iSCROLLINFO,
        iTRANS,
        iANALYSIS,
        iNUM,
    ),
    False: (
        iSCROLLNAME,
        iSCROLLREF,
        iTRANS,
        iANALYSIS,
    ),
}

oSRCLN = 'srcln'
oSCROLL = 'scroll'
xSCROLL = 'scrollx'
oFRAGMENT = 'fragment'
oLINE = 'line'
oINTER = 'inter'
oSUB = 'sub'
oTRANS = 'trans'
xTRANS = 'transx'
oBOUND = 'bound'
oLANG = 'lang'
oSCRIPT = 'script'
oLEX = 'lex'
oMORPH = 'morph'
oBOOK = 'book'
oCHAPTER = 'chapter'
oVERSE = 'verse'

oCOLS = (
    oSRCLN,
    oSCROLL,
    oFRAGMENT,
    oLINE,
    oSUB,
    oINTER,
    oTRANS,
    oBOUND,
    oLEX,
    oLANG,
    oSCRIPT,
    oMORPH,
    oBOOK,
    oCHAPTER,
    oVERSE,
)


# script

PH_VAL = 'paleohebrew'
GC_VAL = 'greekcapital'
SCRIPT_VALS = (PH_VAL, GC_VAL)

# characters

NB = '\u00a0'  # non-breaking space

# various types (of characters, flags, brackets/clusters)

CONS = 'consonant'
VOWEL = 'vowel'
POINT = 'point'
SEP = 'sep'
PUNCT = 'punct'
NUMERAL = 'numeral'
MISSING = 'missing'
UNCERTAIN = 'uncertain'
ADD = 'add'
TERM = 'term'

GLYPH = 'empty'
EMPTY = 'empty'
FOREIGN = 'foreign'
OTHER = 'other'

CORRECTION = 'correction'
REMOVED = 'removed'
VACAT = 'vacat'
ALTERNATIVE = 'alternative'
RECONSTRUCTION = 'reconstruction'

ALEF = 'א'
YOD = 'י'
KAF_E = 'ך'
QOF = 'ק'

CONSONANTS = (
    (ALEF, 'a'),
    ('ב', 'b'),
    ('ג', 'g'),
    ('ד', 'd'),
    ('ה', 'h'),
    ('ו', 'w'),
    ('ז', 'z'),
    ('ח', 'j'),
    ('ט', 'f'),
    (YOD, 'y'),
    ('כ', 'k'),
    (KAF_E, 'K'),
    ('ל', 'l'),
    ('מ', 'm'),
    ('ם', 'M'),
    ('נ', 'n'),
    ('ן', 'N'),
    ('ס', 's'),
    ('פ', 'p'),
    ('ף', 'P'),
    ('ע', 'o'),
    ('צ', 'x'),
    ('ץ', 'X'),
    (QOF, 'q'),
    ('ר', 'r'),
    ('שׂ', 'c'),  # FB2B sin
    ('שׁ', 'v'),  # FB2A shin
    ('שׁ', 'C'),  # 05E9 dotless shin
    ('ת', 't'),
)
CONSONANTS_SET = {x[1] for x in CONSONANTS}

VOWELS = (
    ('\u05b0', 'V'),  # sheva
    ('\u05b0', '√'),  # sheva
    ('\u05b0', 'J'),  # sheva
    ('\u05b0', '◊'),  # sheva
    ('\u05b1', 'T'),  # hataf segol
    ('\u05b2', 'S'),  # hataf patah
    ('\u05b3', 'F'),  # hataf qamats
    ('\u05b3', 'ƒ'),  # hataf qamats
    ('\u05b3', 'Ï'),  # hataf qamats
    ('\u05b4', 'I'),  # hiriq
    ('\u05b4', 'ˆ'),  # hiriq
    ('\u05b4', 'î'),  # hiriq
    ('\u05b4', 'Ê'),  # hiriq
    ('\u05b5', 'E'),  # tsere
    ('\u05b5', 'é'),  # tsere
    ('\u05b5', '´'),  # tsere
    ('\u05b6', 'R'),  # segol
    ('\u05b6', '®'),  # segol
    ('\u05b6', '‰'),  # segol
    ('\u05b7', 'A'),  # patah
    ('\u05b7', 'Å'),  # patah
    ('\u05b7', 'å'),  # patah
    ('\u05b8', 'D'),  # qamats
    ('\u05b8', '∂'),  # qamats
    ('\u05b8', 'Î'),  # qamats
    ('\u05b9', 'O'),  # holam
    ('\u05b9', 'ø'),  # holam
    ('\u05bb', 'U'),  # qubbuts
    ('\u05bb', 'ü'),  # qubbuts
    ('\u05bb', '¨'),  # qubbuts
)
VOWELS_SET = {x[1] for x in VOWELS}

POINTS = (
    ('\u05bc', ';'),  # dagesh
    ('\u05bc', '…'),  # dagesh
    ('\u05bc', 'Ú'),  # dagesh
    ('\u05bc', '¥'),  # dagesh
    ('\u05bc', 'Ω'),  # dagesh
)

POINTS_SET = {x[1] for x in POINTS}

GERESH_POINT = '\u05f3'
GERESH_ACCENT = '\u059c'
MAQAF = '\u05be'

SEPS = (
    (NB, NB),  # non breaking space inside a word
    (MAQAF, '-'),  # maqaf
    (GERESH_POINT, '/'),  # morpheme separator
)
SEPS_SET = {x[1] for x in SEPS}

PUNCTS = (
    ('\u05c3', '.'),  # sof pasuq
    ('\u05c3' * 2, '±'),  # double sof pasuq as paleo divider
)
PUNCTS_SET = {x[1] for x in PUNCTS}

N1A = 'å'
N1F = '∫'

DOT_U = '\u05c4'
DOT_L = '\u05c5'
METEG = '\u05bd'

NUMERALS = (
    (f'{ALEF}{GERESH_ACCENT}', 'A'),
    (f'{ALEF}{DOT_U}', N1A),
    (f'{ALEF}{DOT_L}', 'B'),
    (f'{ALEF}{METEG}', N1F),
    (f'{YOD}{GERESH_ACCENT}', 'C'),
    (f'{KAF_E}{GERESH_ACCENT}', 'D'),
    (f'{QOF}{GERESH_ACCENT}', 'F'),
)

NUMERALS_SET = {x[1] for x in NUMERALS}
NUMERALS_UNI = {x[1]: x[0] for x in NUMERALS}
NUMERALS_REP = {x[1]: TR.from_hebrew(x[0]) for x in NUMERALS}

ARAMAIC = 'aramaic'
GREEK = 'greek'

ALPHA = '\u0391'
GAMMA = '\u0393'
DELTA = '\u0394'
EPSILON = '\u0395'
ETA = '\u0397'
THETA = '\u0398'
IOTA = '\u0399'
KAPPA = '\u039a'
NU = '\u039d'
RHO = '\u03a1'
SIGMA = '\u03a3'
TAU = '\u03a4'
CHI = '\u03a7'

FOREIGNS = (
    (ALPHA, 'A', None),
    (GAMMA, 'G', None),
    (DELTA, 'D', None),
    (EPSILON, 'E', None),
    (ETA, 'H', None),
    (THETA, 'TH', THETA),
    (IOTA, 'I', None),
    (KAPPA, 'K', None),
    (NU, 'N', None),
    (RHO, 'R', None),
    (SIGMA, 'S', None),
    (TAU, 'T', None),
    (CHI, 'CH', CHI),
)
FOREIGNS_ESC = {x[1]: x[2] for x in FOREIGNS if x[2]}
FOREIGNS_UNESC = {x[2]: x[1] for x in FOREIGNS if x[2]}
FOREIGNS_SET = {x[2] or x[1] for x in FOREIGNS}
FOREIGNS_UNI = {x[2] or x[1]: x[0] for x in FOREIGNS}
FOREIGNS_REP = FOREIGNS_UNI

FOREIGNS_REAL = (NUMERALS_SET - CONSONANTS_SET) | VOWELS_SET | FOREIGNS_SET

EM = 'ε'

TOKENS = (
    (MISSING, '--', '░', ' 0 ', EM),
    (UNCERTAIN, '?', None, ' ? ', ' ? '),
    (UNCERTAIN, '\\', None, ' # ', ' # '),
    (ADD, '+', None, ' + ', '+'),
    (TERM, '╱', None, '╱', '╱'),
)
TOKENS_FIX = (
    ('/', '╱'),
)
TOKENS_FIXED = {x[1] for x in TOKENS_FIX}
TOKENS_ESC = {x[1]: x[2] for x in TOKENS if x[2]}
TOKENS_UNESC = {x[2]: x[1] for x in TOKENS if x[2]}
TOKENS_SET = {x[2] or x[1] for x in TOKENS}
TOKENS_INV = {x[2] or x[1]: x[0] for x in TOKENS}
TOKENS_TYPE = {x[0] for x in TOKENS}

# nonbib 53527 lex: CHAG
# nonbib 53566 lex: HN
# nonbib 53584 lex: THE
#    only occurrences of GH

FLAGS = (
    (UNCERTAIN, 1, 'Ø', '?'),
    (UNCERTAIN, 2, '«', '#'),
    (UNCERTAIN, 3, '»', '#?'),
    (UNCERTAIN, 4, '|', '##'),
)

FLAGS_SET = {x[2] for x in FLAGS}
FLAGS_INV = {a: name for (name, v, a, k) in FLAGS}
FLAGS_VALUE = {name: v for (name, v, a, k) in FLAGS}

BRACKETS = (
    (CORRECTION, 3, True, '^', '^', '◀', '▶', '(^ ', ' ^)'),  # PL PR
    (CORRECTION, 2, False, '>>', '<<', '┛', '┗', '(<< ', ' >>)'),  # UL UR
    (CORRECTION, 1, False, '>', '<', '┘', '└', '(< ', ' >)'),  # ul ur
    (REMOVED, 2, False, '}}', '{{', '┫', '┣', '{{ ', ' }}'),  # VL VR
    (REMOVED, 1, False, '}', '{', '┤', '├', '{ ', ' }'),  # vl vr
    (VACAT, 1, False, '≥', '≤', '┐', '┌', '(- ', ' -)'),  # dl dr
    (ALTERNATIVE, 1, False, ')', '(', '◐', '◑', '( ', ' )'),  # 0L 0R
    (RECONSTRUCTION, 1, False, ']', '[', '┑', '┍', '[ ', ' ]'),  # dL dR
    (UNCERTAIN, 2, True, '»', '«', '┘', '└', '(# ', ' #)'),  # ul ur
)

BRACKETS_INV = {}
BRACKETS_INV.update({x[5] or x[3]: (x[0], x[1], True) for x in BRACKETS})
BRACKETS_INV.update({x[6] or x[4]: (x[0], x[1], False) for x in BRACKETS})

BRACKETS_ESC = tuple(x for x in BRACKETS if x[5] or x[6])
BRACKETS_ESCPURE = tuple(x for x in BRACKETS if (x[5] or x[6]) and not x[2])
BRACKETS_SPECIAL = tuple(x for x in BRACKETS if x[2])

DIGITS_SET = set('0123456789')

GLYPHS_ALPHA = CONSONANTS_SET | VOWELS_SET | POINTS_SET | SEPS_SET
GLYPHS_LEX = GLYPHS_ALPHA | DIGITS_SET
GLYPHS_SET = GLYPHS_ALPHA | NUMERALS_SET | FOREIGNS_SET
GLYPHS_AMBI = GLYPHS_ALPHA & NUMERALS_SET

CHARS = set()
for kind in (CONSONANTS, VOWELS, POINTS, SEPS, PUNCTS, NUMERALS):
  CHARS |= {x[1] for x in kind}

for (kind, index) in ((TOKENS, 1), (FLAGS, 2)):
  CHARS |= {x[index] for x in kind}

CHARS |= {x[3] for x in BRACKETS}
CHARS |= {x[4] for x in BRACKETS}

CHARS = reduce(
    set.union,
    (set(x) for x in CHARS),
    set(),
)
CHARS_LEX = CHARS | DIGITS_SET

CHARS_UNI = {}
CHARS_REP = {}
for chars in (CONSONANTS, VOWELS, POINTS, SEPS, PUNCTS):
  for x in chars:
    CHARS_UNI[x[1]] = x[0]
    CHARS_REP[x[1]] = TR.from_hebrew(x[0])
CHARS_UNI.update({x[2] or x[1]: x[4] for x in TOKENS})
CHARS_REP.update({x[2] or x[1]: x[3] for x in TOKENS})
CHARS_UNI.update({x[2]: x[3] for x in FLAGS})
CHARS_REP.update({x[2]: x[3] for x in FLAGS})
CHARS_UNI.update({x[5] or x[3]: x[7] for x in BRACKETS})
CHARS_REP.update({x[5] or x[3]: x[7] for x in BRACKETS})
CHARS_UNI.update({x[6] or x[4]: x[8] for x in BRACKETS})
CHARS_REP.update({x[6] or x[4]: x[8] for x in BRACKETS})

bEsc = {}
bEsc.update({x[3]: x[5] for x in BRACKETS_ESC})
bEsc.update({x[4]: x[6] for x in BRACKETS_ESC})

bUnesc = {}
bUnesc.update({x[5]: x[4] for x in BRACKETS_ESC})
bUnesc.update({x[6]: x[3] for x in BRACKETS_ESC})


bSpecialRe = {}
for x in BRACKETS_SPECIAL:
  name = x[0]
  b = re.escape(x[3])
  e = re.escape(x[4])
  bsRe = re.compile(
      f'{b}'
      f'([^{b}{e}]*)'
      f'{e}'
  )
  bSpecialRe[name] = bsRe


def bSpecialRepl(b, e):
  def bsRepl(match):
    return f'{b}{match.group(1)}{e}'
  return bsRepl


def besc(c):
  return bEsc.get(c, c)


def bunesc(c):
  return bUnesc.get(c, c)


def unesc(text):
  for (cEsc, c) in bUnesc.items():
    text = text.replace(cEsc, c)
  for (tx, t) in FOREIGNS_UNESC.items():
    text = text.replace(tx, t)
  for (tx, t) in TOKENS_UNESC.items():
    text = text.replace(tx, t)
  return text


lexDisRe = re.compile(r'^(.*?)(?:[_-])([0-9]+)$')
lexDisXRe = re.compile(r'[_-][0-9]+$')
foreignRe = re.compile(f'^[{"".join(FOREIGNS_SET)}]+$')
capitalNumRe = re.compile(f'^[A-Z{N1A}{N1F}]+$')
numeralRe = re.compile(f'^[{"".join(NUMERALS_SET)}]+$')
digitRe = re.compile(f'^[0-9]+$')
ambiRe = re.compile(f'^[{"".join(GLYPHS_AMBI)}]+$')
nonPunctRe = re.compile(f'[^{re.escape("".join(PUNCTS_SET))}]+')
nonGlyphRe = re.compile(f'[^{re.escape("".join(GLYPHS_SET))}]+')
nonGlyphLexRe = re.compile(f'[^{re.escape("".join(GLYPHS_LEX))}]+')


# CONFIG READING

def readYaml(fileName):
  with open(fileName) as y:
    y = yaml.load(y)
  return y


# MORPHOLOGY

MERR = 'merr'

NULL = '0'
UNKNOWN = 'unknown'

MORPH_ESC = (
    ('ii', 'ï'),
    ('Pp+Pa', 'På'),
)

# TF CONFIGURATION

slotType = SIGN

generic = dict(
    acronym='dss',
    createdBy='Martin G. Abegg, Jr., James E. Bowley, and Edward M. Cook',
    createdDate='2015',
    convertedBy='Jarod Jacobs, Martijn Naaijer and Dirk Roorda',
    source='Martin Abegg, personal communication',
    license='Creative Commons Attribution-NonCommercial 4.0 International License',
    licenseUrl='http://creativecommons.org/licenses/by-nc/4.0/',
    description='Dead Sea Scrolls: biblical and non-biblical scrolls',
)

otext = {
    'sectionFeatures': 'acro,label,label',
    'sectionTypes': 'scroll,fragment,line',
    'fmt:text-orig-full': f'{{glyph}}{{punc}}{{after}}',
    'fmt:text-trans-full': f'{{glyphe}}{{punce}}{{after}}',
    'fmt:text-source-full': f'{{glypho}}{{punco}}{{after}}',
    'fmt:text-orig-extra': f'{{full}}{{after}}',
    'fmt:text-trans-extra': f'{{fulle}}{{after}}',
    'fmt:text-source-extra': f'{{fullo}}{{after}}',
    'fmt:lex-orig-full': f'{{lex}}{{punc}}{{after}}',
    'fmt:lex-trans-full': f'{{lexe}}{{punce}}{{after}}',
    'fmt:lex-etcbc-full': f'{{lexo}}{{punco}}{{after}}',
}

intFeatures = set('''
    biblical
    interlinear
    number
    srcLn
'''.strip().split())

featureMeta = {
    'acro': {
        'description': 'acronym of a scroll or book',
    },
    'after': {
        'description': 'space behind the word, if any',
        'values': ' (space)',
    },
    ALTERNATIVE: {
        'description': 'alternative reading',
        'values': '1',
    },
    'biblical': {
        'description': 'whether we are in a biblical text or not',
        'values': '1 (means: biblical)',
        'applies': f'scroll fragment line cluster word',
    },
    CORRECTION: {
        'description': 'correction made by an ancient or modern editor',
        'values': '1 = modern, 2 = ancient, 3 = ancient supralinear',
    },
    'fullo': {
        'description': (
            'full transcription (original source Abegg) of a word'
            ' including flags and brackets'
        ),
    },
    'fulle': {
        'description': (
            'full transcription (ETCBC transliteration) of a word'
            ' including flags and brackets'
        ),
    },
    'full': {
        'description': (
            'full transcription (Unicode) of a word'
            ' including flags and brackets'
        ),
    },
    'glypho': {
        'description': 'representation (original source Abegg) of a word or sign',
    },
    'glyphe': {
        'description': 'representation (ETCBC transliteration) of a word or sign',
    },
    'glyph': {
        'description': 'representation (Unicode) of a word or sign',
    },
    'interlinear': {
        'description': (
            'interlinear material,'
            ' the value indicates the sequence number of the interlinear line'
        ),
    },
    'label': {
        'description': 'label of a fragment or chapter or line',
    },
    'language': {
        'description': 'language of a word or sign, only if it is not Hebrew',
        'values': f'{ARAMAIC} {GREEK}'
    },
    'lexo': {
        'description': 'representation (original source Abegg) of a lexeme',
    },
    'lexe': {
        'description': 'representation (ETCBC transliteration) of a lexeme',
    },
    'lex': {
        'description': 'representation (Unicode) of a lexeme',
    },
    MERR: {
        'description': 'errors in parsing the morphology tag',
    },
    'morpho': {
        'description': 'morphological tag (original source Abegg)',
    },
    'number': {
        'description': 'number of line or verse',
    },
    'occ': {
        'description': 'edge feature from a lexeme to its occurrences',
    },
    'punco': {
        'description': 'trailing punctuation (original source Abegg) of a word',
    },
    'punce': {
        'description': 'trailing punctuation (ETCBC transliteration) of a word',
    },
    'punc': {
        'description': 'trailing punctuation (Unicode) of a word',
    },
    REMOVED: {
        'description': 'removed by an ancient or modern editor',
        'values': '1 = modern, 2 = ancient',
    },
    RECONSTRUCTION: {
        'description': 'reconstructed by a modern editor',
        'values': '1',
    },
    'script': {
        'description': 'script in which the word is written if it is not Hebrew',
        'values': ' '.join(SCRIPT_VALS)
    },
    'srcLn': {
        'description': 'the line number of the word in the source data file',
    },
    'type': {
        'description': 'type of sign or cluster',
    },
    UNCERTAIN: {
        'description': 'uncertain material in various degrees: higher degree is less certain',
        'values': '1 2 3 4',
    },
    VACAT: {
        'description': 'empty, unwritten space',
        'values': '1',
    },
}

# DATA READING

LIMIT = 10

data = []

etcbcFromTrans = {}
charGroups = {}
morphParsed = {}

morphDecl = {}
posDict = {}
valueDict = {}
valuesFound = collections.defaultdict(set)

logh = None

diags = {}
biblical = None
ln = None


def report(msg, newline=True, only=False):
  nl = '\n' if newline else ''
  msg = f'{msg}{nl}'
  if not only:
    sys.stdout.write(msg)
    sys.stdout.flush()
  if logh:
    logh.write(msg)


def progress(msg, newline=True):
  nl = '' if newline is None else '\n' if newline else '\r'
  msg = f'{msg}{nl}'
  sys.stdout.write(msg)


def bib():
  return 'B' if biblical else 'N'


def resetDiag():
  global diags
  diags = {}


def diag(label, rep, status):
  diags[(label, biblical, ln, rep)] = status


def showDiag():
  n = collections.defaultDict(collections.Counter)

  good = True

  for ((kind, biblical, ln, rep), st) in sorted(diags.items()):
    n[kind][''] += 1
    st = None if st is None else bool(st)
    n[kind][st] += 1

    statusRep = '--' if st is None else 'OK' if st else 'XX'
    locRep = f'{bib()}:{ln:>6}'
    report(f'{kind}: {statusRep} {locRep} {rep}', only=True)
    if st is False:
      good = False
  for (kind, r) in n.items():
    if r[None]:
      report(f'{kind}: {r[None]} undetected')
    if r[False]:
      report(f'{kind}: {r[False]} errors')
    if r[True] == r['']:
      report(f'{kind}: all {r[""]} cases ok')
    report('', only=True)
  return good


def readSource():
  global biblical
  global ln

  XC = '\u001b'

  scrollDecl = readYaml(SCROLL_DECL)
  fixesDecl = readYaml(FIXES_DECL)

  lineFixes = fixesDecl['lineFixes']
  fieldFixes = fixesDecl['fieldFixes']

  fixL = 'FIX (LINE)'
  fixF = 'FIX (FIELD)'

  for (biblical, lns) in lineFixes.items():
    for (ln, (fr, to, expl)) in lns.items():
      taskRep = f'{fr:>6} => {to:<6} {expl}'
      diag(fixL, taskRep, None)

  for (biblical, lns) in fieldFixes.items():
    for (ln, fields) in lns.items():
      for (field, (fr, to, expl)) in fields.items():
        taskRep = f'{field:<8} {fr:>6} => {to:<6} {expl}'
        diag(fixF, taskRep, None)

  for src in SOURCES:
    biblical = src == BIB
    ln = 0

    splitChar = '\t' if biblical else ' '
    nCols = iCOLS[biblical]
    nCol = len(nCols)
    lineFix = lineFixes[biblical]
    fieldFix = fieldFixes[biblical]

    report(f'Reading proto {bib()} ...', newline=False)
    theseData = []
    prevWord = None
    prevLine = None
    subNum = None
    xLine = None
    interlinear = None
    script = None

    scrollso = set()
    scrollsx = set()

    # fl fy: paleo
    # f0 fy: greek

    with open(f'{SOURCE_DIR}/dss_{src}.txt') as fh:
      for line in fh:
        ln += 1
        if XC in line:
          xLine = line
          if '(a)' in xLine:
            interlinear = 1
          elif '(b)' in xLine:
            interlinear = 2
          elif xLine.startswith(f'{XC}r'):
            interlinear = None

          if '(fl)' in xLine:
            script = PH_VAL
          elif '(f0)' in xLine:
            script = GC_VAL
          elif '(fy)' in xLine:
            script = None

          continue
        line = line.rstrip('\n')

        if ln in lineFix:
          (fr, to, rep) = lineFix[ln]
          if fr in line:
            line = line.replace(fr, to)
            diag(fixL, rep, True)
          else:
            diags(fixL, rep, False)

        fields = line.split(splitChar)
        nFields = len(fields)
        if nFields > nCol:
          diag('FIELDS', 'too many: {nFields}', False)
          continue
        elif nFields < nCol:
          fields += [None] * (nCol - nFields)
        iData = {f: c for (f, c) in zip(nCols, fields)}

        if ln in fieldFix:
          for (field, (fr, to, rep)) in fieldFix[ln].items():
            iVal = iData[field]
            if iVal == fr:
              iData[field] = to
              diag(fixF, rep, True)
            else:
              diag(fixF, rep, False)

        oData = collections.defaultdict(lambda: '')
        oData[oSRCLN] = ln
        trans = iData[iTRANS]
        if biblical:
          (scroll, rest) = iData[iSCROLLINFO].split(' ')
          (fragment, line) = rest.split(':')
          oData[oFRAGMENT] = fragment
          oData[oLINE] = line
          (book, rest) = iData[iBIBINFO].split(' ', 1)
          (chapter, verse) = rest.split(':', 1)
          oData[oBOOK] = book
          oData[oCHAPTER] = chapter
          oData[oVERSE] = verse
          word = iData[iNUM]
          if '.' in word:
            oData[oBOUND] = '&'
        else:
          if line.startswith('>'):
            line = line[1:]
            scroll = iData[iSCROLLNAME]
            (fragment, line) = iData[iSCROLLREF].split(':', 1)
            if line != prevLine:
              interlinear = None
            prevLine = line
            continue
          if trans.startswith(']') and trans.endswith('['):
            text = trans[1:-1]
            if text.isdigit():
              subNum = text[::-1]
              continue

          (fragment, rest) = iData[iSCROLLREF].split(':', 1)
          (line, word) = rest.split(',', 1)
          if line != prevLine:
            interlinear = None
          oData[oFRAGMENT] = fragment
          oData[oLINE] = line
          if line == '0':
            if subNum:
              oData[oSUB] = subNum
          (word, sub) = word.split('.', 1)
          if word == prevWord:
            theseData[-1][oBOUND] = '&'
          prevWord = word

        scrollx = scrollDecl.get(scroll, x)
        scrollso.add(scroll)
        scrollsx.add(scrollx)
        oData[oSCROLL] = scroll
        oData[xSCROLL] = scrollDecl.get(scroll, x)

        if interlinear:
          oData[oINTER] = interlinear
        if script:
          oData[oSCRIPT] = script

        analysis = iData[iANALYSIS] or ''
        (lang, lex, morph) = (None, None, None)
        if '%' in analysis:
          lang = ARAMAIC
          (lex, morph) = analysis.split('%', 1)
        elif '@' in analysis:
          (lex, morph) = analysis.split('@', 1)
        oData[oTRANS] = trans
        oData[oLANG] = lang
        oData[oLEX] = lex
        oData[oMORPH] = morph

        prevLine = line

        theseData.append(oData)
    report(f'{len(theseData):<6} lines out of {ln:<6} source lines')
    data.extend(theseData)
  report('', only=True)
  report(f'DATANORM: {len(data)} lines')
  report(f'SCROLLS: {len(scrollso):>4} names (original)')
  report(f'SCROLLS: {len(scrollsx):>4} names (after renaming some')


def writeProto():
  if not os.path.exists(NORM_DIR):
    os.makedirs(NORM_DIR, exist_ok=True)
  with open(f'{NORM_DIR}/dss.tsv', 'w') as fh:
    for fields in data:
      line = '\t'.join(str(fields[col]) for col in oCOLS)
      fh.write(f'{line}\n')


def tokenizeData():
  global biblical
  global ln

  prevS = None

  for fields in data:
    text = fields[oTRANS]

    for (t, tx) in FOREIGNS_ESC.items():
      text = text.replace(t, tx)
    for (t, tx) in TOKENS_FIX:
      if text == t:
        text = tx
    for (t, tx) in TOKENS_ESC.items():
      text = text.replace(t, tx)
    for x in BRACKETS_SPECIAL:
      bRe = bSpecialRe[x[0]]
      text = bRe.sub(bSpecialRepl(x[5], x[6]), text)
      b = x[3]
      e = x[4]
      bEsc = x[5]
      eEsc = x[6]
      if b == e and b in text:
        r = eEsc if prevS == bEsc else bEsc
        prevS = r
        text = text.replace(b, r)
    for x in BRACKETS_ESCPURE:
      text = text.replace(x[3], x[5]).replace(x[4], x[6])

    fields[xTRANS] = text


def checkChars():
  global biblical
  global ln

  charsFound = collections.Counter()
  charsMapped = set()
  charsLetter = {}
  lastOfLine = collections.Counter()
  nLines = 0

  def showChars():
    report(f'CHARACTERS: MAPPED: {"".join(sorted(charsMapped))}', only=True)
    lexes = set(charsLetter[LEX]) if LEX in charsLetter else set()
    transes = set(charsLetter[TRANS]) if TRANS in charsLetter else set()
    charsLetterShow = {}
    for (name, freqs) in charsLetter.items():
      for (c, freq) in freqs.items():
        label = (
            'both'
            if c in lexes and c in transes else
            'only'
        )
        charsLetterShow.setdefault(name, []).append((label, c, freq))
    report(f'CHARACTERS: {sum(len(x) for x in charsLetterShow.values())} used')
    for (name, items) in sorted(charsLetterShow.items()):
      report(f'\tin {name} field:', only=True)
      for (label, c, freq) in sorted(items):
        report(f'\t\t{label:<5} {c} {freq:>6} x', only=True)
    report('', only=True)

  prevTrans = None
  prevLine = None
  prevFragment = None
  prevScroll = None

  for fields in data:
    biblical = oBOOK in fields
    ln = fields[oSRCLN]

    word = fields[xTRANS]
    lex = fields[oLEX]
    script = fields[oSCRIPT]
    thisLine = fields[oLINE]
    thisFragment = fields[oFRAGMENT]
    thisScroll = fields[xSCROLL]

    if (prevScroll, prevFragment, prevLine) != (thisScroll, thisFragment, thisLine):
      nLines += 1
      if prevTrans is not None:
        lastOfLine[prevTrans] += 1
    else:
      if prevTrans == '/':
        diag('CHAR', 'inner /', True)

    if script:
      diag('SCRIPT', script, script in SCRIPT_VALS)

    lexBare = lexDisXRe.sub('', lex)
    lexPure = nonGlyphLexRe.sub('', lexBare)
    isNumLex = lexPure and lexPure != '0' and digitRe.match(lexPure)
    if isNumLex:
      lex = lex[::-1]
      lexPure = lexPure[::-1]

    wordPure = nonGlyphRe.sub('', word)
    isNumTrans = wordPure and numeralRe.match(wordPure)
    isAmbi = wordPure and ambiRe.match(wordPure)

    isNumCand = capitalNumRe.match(wordPure)

    if isNumCand and not isNumTrans and (isNumLex or not lexPure):
      diag('NUMERAL', f'candidate "{wordPure}"', None)

    if isNumTrans and isNumLex:
      diag('NUMERAL', f'found "{wordPure}"', True)

    if not isAmbi:
      label = (
          'trans:yes lex:no'
          if isNumTrans and not isNumLex else
          'trans:no lex:yes'
          if not isNumTrans and isNumLex else
          None
      )
      if label is not None:
        diag('NUMERAL', f'{label} trans="{wordPure}" lex="{lexPure}"', False)

    isForeign = wordPure and lex == NOLEX and foreignRe.match(wordPure)
    if isForeign:
      diag('FOREIGN', wordPure, True)

    digital = DIGITS_SET

    for (name, legal, text) in (
        (TRANS, CHARS | FOREIGNS_SET, word),
        (LEX, CHARS_LEX, lexBare),
    ):
      for c in text:
        charsFound[c] += 1
        if (
            c in legal
            or
            (c in digital and name == LEX and isNumLex)
        ):
          charsMapped.add(c)
        else:
          diag('CHAR', f'unmapped "{c}" = {ord(c)}', False)
        charsLetter.setdefault(name, collections.Counter())[c] += 1

    prevLine = thisLine
    prevFragment = thisFragment
    prevScroll = thisScroll
    prevTrans = word

  unused = (CHARS | CHARS_LEX) - charsMapped - TOKENS_FIXED
  if unused:
    unusedStr = ''.join(sorted(unused))
    report(f'CHARACTERS: WARNING: UNUSED: {unusedStr} ({len(unused)} chars)')

  report(
      f'\tNumber of ways to end a line: {len(lastOfLine)} ways to end a line',
      only=True
  )
  for (word, amount) in sorted(lastOfLine.items(), key=lambda x: (-x[1], x[0]))[0:20]:
    report(f'\t\t{word:<10} {amount:>6} x', only=True)
  report('', only=True)

  showChars()


def checkBracketPair(b, e):
  global biblical
  global ln

  (bOrig, eOrig) = (bunesc(b), bunesc(e))
  report(f'BRACKETS {bOrig} {eOrig} ...', only=True)

  last = None
  nOccs = collections.Counter()

  def closeBracket():
    if last is not None and last != e:
      diag('BRACKET', f'{bOrig}{eOrig} not closed after last {last}')

  biblical = None

  for fields in data:
    prevBiblical = biblical
    biblical = oBOOK in fields
    if prevBiblical is not None and prevBiblical != biblical:
      last = None
      closeBracket()

    ln = fields[oSRCLN]

    word = fields[xTRANS]
    for c in word:
      isB = c == b
      isE = c == e
      if isB and last == b:
        diag('BRACKET', f'extra {bOrig}')
      if isE and (last == e or last is None):
        diag('BRACKET', f'extra {eOrig}')
      if isB or isE:
        nOccs[biblical] += 1
        last = c

  closeBracket()
  report('', only=True)


def checkBrackets():
  for (name, value, kind, b, e, bEsc, eEsc, *x) in BRACKETS:
    if bEsc is None:
      bEsc = b
    if eEsc is None:
      eEsc = e
    checkBracketPair(bEsc, eEsc)


def readMorph():
  global morphDecl
  global posDict
  global featureList
  global valueDict

  morphDecl = readYaml(MORPH_DECL)

  posFt = morphDecl['posFt']
  classFt = morphDecl['classFt']

  posDict = {v[0]: k for (k, v) in morphDecl['values'][posFt].items()}
  featureList = {
      pos: [list(feat.keys())[0] for feat in feats]
      for (pos, feats) in morphDecl['tags'].items()
  }
  valuesInfo = morphDecl['values']

  valueDict = {}
  for (pos, feats) in morphDecl['tags'].items():
    posValues = {}
    for (ftData) in feats:
      featValues = {}
      for (ft, values) in ftData.items():
        for v in values:
          m = valuesInfo[ft][v][0] if ft != classFt else valuesInfo[ft][pos][v][0]
          featValues[m] = v
      posValues[ft] = featValues
    valueDict[pos] = posValues


def parseMorph():
  global biblical
  global ln

  posFt = morphDecl['posFt']
  mEsc = morphDecl['escapes']
  mRepl = morphDecl['aramaicReplace']

  def mesc(tag):
    for x in mEsc:
      tag = tag.replace(*x)
    return tag

  def readPart(tag, nPart, parsed):
    m = tag[0]
    tag = tag[1:]

    pos = UNKNOWN if m == NULL else posDict.get(m, None)

    if not pos:
      parsed.setdefault(MERR, '')
      parsed[MERR] += m
      return tag

    parsed[posFt] = pos
    valuesFound[posFt].add(pos)

    if not tag:
      return tag

    feats = featureList[pos]
    for ft in feats:
      if not tag:
        break
      m = tag[0]
      values = valueDict[pos][ft]
      mft = f'{ft}{nPart + 1}' if nPart else ft

      value = UNKNOWN if m == NULL else values.get(m, None)
      if value is not None:
        parsed[mft] = value
        valuesFound[mft].add(value)
        tag = tag[1:]

    return tag

  def parseTag(tago):
    tag = mesc(tago)
    parsed = {}
    nPart = 0

    while tag:
      m = tag[0]
      if nPart == 0 or tag.startswith('X'):
        tag = readPart(tag, nPart, parsed)
        nPart += 1
      else:
        parsed.setdefault(MERR, '')
        parsed[MERR] += m
        tag = tag[1:]
    return parsed

  tagFound = collections.Counter()
  tagError = collections.Counter()
  tagGood = collections.Counter()

  def showMorph():
    totalTag = sum(tagFound.values())
    totalGood = sum(tagGood.values())
    totalError = sum(tagError.values())
    report(f'MORPH: {len(tagFound)} distinct tags in {totalTag} occurrences')
    if tagError:
      report(f'MORPH: ERROR: {len(tagError)} distinct tags in {totalError} occurrences')
      for (tago, amount) in sorted(tagError.items()):
        parsed = morphParsed[tago]
        tag = mesc(tago)
        tagRep = tago if tago == tag else f'{tago} => {tag}'
        report(f'\t{tagRep:<18} {amount:>5} x {parsed}', only=True)
      report('', only=True)

    report(f'MORPH: GOOD: {len(tagGood)} distinct tags in {totalGood} occurrences')
    for (tago, amount) in sorted(tagGood.items()):
      parsed = morphParsed[tago]
      tag = mesc(tago)
      tagRep = tago if tago == tag else f'{tago} => {tag}'
      report(f'\t{tagRep:<18} {amount:>5} x {parsed}', only=True)
    report('', only=True)

  for fields in data:
    biblical = oBOOK in fields
    ln = fields[oSRCLN]

    lang = fields[oLANG]
    morpho = fields[MORPH]
    if lang == ARAMAIC:
      morpho = morpho.replace(*mRepl)  # vs code H means something different in Aramaic

    tagFound[morpho] += 1
    if morpho in morphParsed:
      parsed = morphParsed[morpho]
    else:
      parsed = parseTag(morpho)
      morphParsed[morpho] = parsed

  if debug:
    biblical = None
    ln = 0
    tag = None
    while tag is None or tag:
      tago = input('tag [ENTER to stop]> ')
      tag = mesc(tago)
      tagRep = tago if tago == tag else f'{tago} => {tag}'
      print(f'{tagRep} => {parseTag(tag)}')
    return

  for (tag, amount) in tagFound.items():
    parsed = morphParsed[tag]
    if MERR in parsed:
      tagError[tag] += amount
    else:
      tagGood[tag] += amount

  showMorph()


def prepare():
  global logh
  logh = open(REPORT, 'w')


def finalize():
  global logh
  logh.close()
  logh = None


def verseNum(text):
  if text.isdigit():
    return (text, None)
  return (text[0:-1], text[-1])


# DIRECTOR

def director(cv):
  global biblical
  global ln

  mRepl = morphDecl['aramaicReplace']

  report('Compiling feature data from tokens')

  prevBook = None
  prevChapter = None
  prevVerse = None
  prevHalfVerse = None

  prevScroll = None
  prevFragment = None
  prevLine = None

  curBook = None
  curChapter = None
  curVerse = None
  curHalfVerse = None

  curScroll = None
  curFragment = None
  curLine = None

  curBrackets = {}

  curWord = None
  curSlot = None

  lexIndex = {}

  errors = {}

  def asUni(text, asNum=False, asForeign=False):
    result = ''
    try:
      result = (
          ''.join(FOREIGNS_UNI[c] if c in FOREIGNS_UNI else CHARS_UNI[c] for c in text)
          if asForeign else
          ''.join(NUMERALS_UNI[c] if c in NUMERALS_UNI else CHARS_UNI[c] for c in text)
          if asNum else
          ''.join(CHARS_UNI[c] for c in text)
      )
    except KeyError:
      diag('unknown character uni', text, False)
    return result

  def asRep(text, asNum=False, asForeign=False):
    result = ''
    try:
      result = (
          ''.join(FOREIGNS_REP[c] if c in FOREIGNS_REP else CHARS_UNI[c] for c in text)
          if asForeign else
          ''.join(NUMERALS_REP[c] if c in NUMERALS_REP else CHARS_REP[c] for c in text)
          if asNum else
          ''.join(CHARS_REP[c] for c in text)
      )
    except KeyError:
      diag('unknown character rep', False)
    return result

  def morphMeta():
    if not cv.occurs(MERR):
      cv.meta(MERR)
    for (ft, desc) in morphDecl['features'].items():
      for p in range(1, 5):
        mft = f'{ft}{p}' if p > 1 else ft
        if cv.occurs(mft):
          d = f' (for part {p})' if p > 1 else ''
          valueRep = ', '.join(sorted(valuesFound[mft]))
          meta = {
              'description': f'{desc}{d} (morphology tag)',
              'valueType': 'int' if ft in intFeatures else 'str',
              'values': valueRep,
          }
          cv.meta(mft, **meta)

  def addSlot():
    nonlocal curSlot
    curSlot = cv.slot()
    isNum = typ == NUMERAL
    glyph = asUni(c, asNum=isNum, asForeign=isForeign)
    glyphe = asRep(c, asNum=isNum, asForeign=isForeign)
    cv.feature(curSlot, glyph=glyph, glyphe=glyphe, glypho=unesc(c), type=typ)
    if lang:
      cv.feature(curSlot, language=lang)
    for (name, value) in curBrackets:
      cv.feature(curSlot, **{name: value})

  nScroll = 0
  nBook = 0
  thisLex = None

  chunk = 1000
  k = 0
  j = 0

  def closeVolume():
    cv.terminate(curLine)
    cv.terminate(curFragment)
    cv.terminate(curScroll)
    if biblical:
      cv.terminate(curHalfVerse)
      cv.terminate(curVerse)
      cv.terminate(curChapter)
      cv.terminate(curBook)

  biblical = None

  for fields in data:
    prevBiblical = biblical
    biblical = oBOOK in fields
    if prevBiblical is not None and prevBiblical != biblical:
      closeVolume()
      pass

    ln = fields[oSRCLN]

    curSlot = None

    if j == chunk:
      j = 0
      progress(f'{bib()}:{k:>6} lines', newline=False)
    j += 1
    k += 1
    thisScroll = fields[xSCROLL]
    thisFragment = fields[oFRAGMENT]
    thisLine = fields[oLINE]
    changeScroll = thisScroll != prevScroll
    changeFragment = thisFragment != prevFragment
    changeLine = thisLine != prevLine
    if changeLine or changeFragment or changeScroll:
      cv.terminate(curLine)
    if changeFragment or changeScroll:
      cv.terminate(curFragment)
    if changeScroll:
      cv.terminate(curScroll)
      nScroll += 1
      curScroll = cv.node(SCROLL)
      cv.feature(curScroll, acro=thisScroll)
      if biblical:
        cv.feature(curScroll, biblical=1)
    if changeFragment or changeScroll:
      curFragment = cv.node(FRAGMENT)
      cv.feature(curFragment, label=thisFragment)
      if biblical:
        cv.feature(curFragment, biblical=1)
    if changeLine or changeFragment or changeScroll:
      curLine = cv.node(LINE)
      cv.feature(curLine, label=thisLine)
      if biblical:
        cv.feature(curLine, biblical=1)

    if biblical:
      thisBook = fields[oBOOK]
      thisChapter = fields[oCHAPTER]
      thisVerse = fields[oVERSE]
      (thisVerse, thisHalfVerse) = verseNum(thisVerse)
      changeBook = thisBook != prevBook
      changeChapter = thisChapter != prevChapter
      changeVerse = thisVerse != prevVerse
      changeHalfVerse = thisHalfVerse != prevHalfVerse
      if changeHalfVerse or changeVerse or changeChapter or changeBook:
        cv.terminate(curHalfVerse)
      if changeVerse or changeChapter or changeBook:
        cv.terminate(curVerse)
      if changeChapter or changeBook:
        cv.terminate(curChapter)
      if changeBook:
        cv.terminate(curBook)
      if changeBook:
        curBook = cv.node(BOOK)
        cv.feature(curBook, acro=thisBook)
        nBook += 1
      if changeChapter or changeBook:
        curChapter = cv.node(CHAPTER)
        cv.feature(curChapter, label=thisChapter)
      if changeVerse or changeChapter or changeBook:
        curVerse = cv.node(VERSE)
        cv.feature(curVerse, number=thisVerse)
      if changeHalfVerse or changeVerse or changeChapter or changeBook:
        if thisHalfVerse:
          curHalfVerse = cv.node(HALFVERSE)
          cv.feature(curHalfVerse, number=thisVerse, label=thisHalfVerse)

    after = ' ' if fields[oBOUND] == B else None
    fullo = fields[oTRANS]
    lexo = fields[oLEX]
    lang = fields[oLANG]
    morpho = fields[oMORPH]
    script = fields[oSCRIPT]
    interlinear = None if biblical else fields[oINTER]
    glypho = nonGlyphRe.sub('', fullo)
    punco = nonPunctRe.sub('', fullo)
    if punco and glypho:
      diag('punctuation and glyphs on same line', fullo, False)

    if lexo == 'B':
      diag('Unknown lexeme', lexo, False)
      lexo = ''
    isNumLex = False

    if lexo:
      (lexoB, lexN) = (lexo, '')
      lexoDis = lexDisRe.findall(lexo)
      if lexoDis:
        (lexoB, lexN) = lexoDis[0]
        lexN = f'_{lexN}' if lexN else ''
        lexo = f'{lexoB}{lexN}'
      else:
        (lexoB, lexN) = (lexo, '')
      lexPure = nonGlyphLexRe.sub('', lexoB)
      isNoLex = lexPure == '0'
      isNumLex = lexPure and not isNoLex and digitRe.match(lexPure)

      if isNoLex:
        lex = EM
        lexe = EM
      elif isNumLex:
        lexoB = lexoB[::-1]
        lex = lexoB
        lexe = lexoB
      else:
        lex = asUni(lexoB)
        lexe = asRep(lexoB)
      lex += lexN
      lexe += lexN
      thisLex = lexIndex.get(lex, None)
      if thisLex:
        cv.resume(thisLex)
      else:
        thisLex = cv.node(LEX)
        lexIndex[lex] = thisLex
      cv.feature(thisLex, lexo=lexo, lexe=lexe, lex=lex)

    if punco or glypho or lexo:
      curWord = cv.node(WORD)
      cv.feature(curWord, srcLn=ln + 1)
      if biblical:
        cv.feature(curWord, biblical=1)
      if script:
        cv.feature(curWord, script=script)
      if interlinear:
        cv.feature(curWord, interlinear=interlinear)
      if fullo:
        cv.feature(curWord, fullo=unesc(fullo))
      if after:
        cv.feature(curWord, after=after)
      if glypho:
        cv.feature(curWord, glypho=glypho)
      if punco:
        cv.feature(
            curWord,
            punco=punco,
            punc=asUni(punco),
            punce=asRep(punco),
        )
      if not glypho:
        typ = EMPTY
        c = ''
        addSlot()
    if glypho and lexo:
      cv.feature(curWord, lexo=lexo, lexe=lexe, lex=lex)
      cv.edge(thisLex, curWord, occ=None)

    isNumTrans = glypho and numeralRe.match(glypho)
    isNum = isNumTrans and isNumLex
    isForeign = glypho and lexo == NOLEX and foreignRe.match(glypho)

    typ = (
        PUNCT if punco else
        NUMERAL if isNum else
        GLYPH if glypho or lexo else
        EMPTY if not fullo else
        OTHER
    )

    cv.feature(
        curWord,
        type=typ,
        full=asUni(fullo, asNum=isNum, asForeign=isForeign),
        fulle=asRep(fullo, asNum=isNum, asForeign=isForeign),
    )
    if glypho:
      cv.feature(
          curWord,
          glyph=asUni(glypho, asNum=isNum, asForeign=isForeign),
          glyphe=asRep(glypho, asNum=isNum, asForeign=isForeign),
      )
    if isForeign:
      lang = GREEK
    if lang:
      cv.feature(curWord, language=lang)

    if morpho:
      morph = morpho.replace(*mRepl) if lang == ARAMAIC else morpho
      # vs code H means something different in Aramaic
      cv.feature(curWord, morpho=morpho, **morphParsed[morph])

    typ = None
    for c in fullo:
      if isForeign:
        typ = FOREIGN
        addSlot()
      elif isNum and c in NUMERALS_SET:
        typ = NUMERAL
        addSlot()
      elif c in TOKENS_SET:
        typ = TOKENS_INV[c]
        addSlot()
      elif c in CONSONANTS_SET:
        typ = CONS
        addSlot()
      elif c in VOWELS_SET:
        typ = VOWEL
        addSlot()
      elif c in SEPS_SET:
        typ = SEP
        addSlot()
      elif c in PUNCTS_SET:
        typ = PUNCT
        addSlot()
      elif c in FLAGS_INV:
        name = FLAGS_INV[c]
        value = FLAGS_VALUE[name]
        cv.feature(curSlot, **{name: value})
      elif c in BRACKETS_INV:
        (name, value, isOpen) = BRACKETS_INV[c]
        key = (name, value)
        valRep = '' if value == 1 else value
        if isOpen:
          cn = cv.node(CLUSTER)
          curBrackets[key] = cn
          cv.feature(cn, type=f'{name}{valRep}')
          if biblical:
            cv.feature(cn, biblical=1)
        else:
          cn = curBrackets[key]
          if not cv.linked(cn):
            em = cv.slot()
            cv.feature(em, type=EMPTY)
          cv.terminate(cn)
          del curBrackets[key]
    cv.terminate(curWord)
    cv.terminate(thisLex)

    prevScroll = thisScroll
    prevFragment = thisFragment
    prevLine = thisLine
    if biblical:
      prevBook = thisBook
      prevChapter = thisChapter
      prevVerse = thisVerse
      prevHalfVerse = thisHalfVerse

  closeVolume()

  progress(f'{bib():<6}:{k:>6} lines')

  morphMeta()
  showDiag()
  return not errors


# SET UP CONVERSION

def getConverter():
  if os.path.exists(OUT_DIR):
    rmtree(OUT_DIR)
  if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
  TF = Fabric(locations=[OUT_DIR])
  return CV(TF)


def convert():
  prepare()
  readSource()
  if argValue['normwrite']:
    writeProto()

  readMorph()
  if argValue['morphdecl']:
    showDiag()
    return True

  parseMorph()
  if argValue['morphonly']:
    showDiag()
    return True

  if checkSource:
    checkChars()
  tokenizeData()
  if checkSource:
    checkBrackets()

  if argValue['checkonly']:
    showDiag()
    return True

  showDiag()
  resetDiag()

  cv = getConverter()

  result = cv.walk(
      director,
      slotType,
      otext=otext,
      generic=generic,
      intFeatures=intFeatures,
      featureMeta=featureMeta,
      generateTf=not argValue['notf'],
      force=argValue['force'],
  )
  finalize()
  return result


# TF LOADING (to test the generated TF)

def loadTf():
  TF = Fabric(locations=[OUT_DIR])
  allFeatures = TF.explore(silent=True, show=True)
  loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
  api = TF.load(loadableFeatures, silent=False)
  if api:
    F = api.F
    report(f'max node = {api.F.otype.maxNode}')
    for (word, freq) in F.glyph.freqList(nodeTypes={WORD})[0:20]:
      report(f'{freq:>6} x {word}')
    report(f'first {ARAMAIC} word:')
    aramaicWords = [w for w in F.otype.s(WORD) if F.language.v(w) == ARAMAIC]
    for w in aramaicWords[0:10]:
      report(f'{ARAMAIC:} {w:>7} = {F.fullo.v(w)} = {F.full.v(w)}')
  return 0 if api else 1


# MAIN

def main():
  global checkSource
  global debug

  report(f'This is tfFromAbegg converting {REPO} transcriptions to TF:')
  report(f'\tsource version = {VERSION_SRC}')
  report(f'\ttarget version = {VERSION_TF}')

  for arg in ARGS:
    argValue[arg] = len(sys.argv) > 1 and arg in sys.argv[1:]

  unknownArgs = set()

  for arg in sys.argv[1:]:
    if arg not in ARGS:
      unknownArgs.add(arg)

  if unknownArgs:
    print(helpText)
    for arg in sorted(unknownArgs):
      print(f'ERROR: unknown arg {arg}')
    return 1

  if argValue['help']:
    print(helpText)
    return 0

  checkSource = argValue['check'] or argValue['checkonly']
  debug = argValue['debug']

  if argValue['loadonly']:
    return loadTf()

  if debug:
    import readline  # noqa
    readMorph()
    parseMorph()
    return 0

  good = convert()

  if not good:
    return 1

  if (
      not argValue['checkonly'] and
      argValue['load'] and
      not argValue['notf']
  ):
    return loadTf()

    return 0


sys.exit(main())
