import sys
import os
import collections
import re
import time
from datetime import date, datetime
from shutil import rmtree
from functools import reduce

import yaml

from tf.fabric import Fabric
from tf.writing.transcription import Transcription
from tf.convert.walker import CV

HELP = 'help'

ARGS = {
    HELP: 'print this help',
    'nochars': 'suppress character checks (by default, checks are performed)',
    'normwrite': 'write out normalized files',
    'sourceonly': 'only read source and apply fixes',
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
debug = None

# LOCATIONS

ORG = 'etcbc'
REPO = 'dss'
VERSION_SRC = '1.0'
VERSION_TF = '0.5'

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

RUNDATE = date.today().isoformat()

MAIN_R = 'main_r'
LINESO_R = 'lineso_r'
LINESS_R = 'liness_r'
ALIGN_R = 'align_r'
MORPH_R = 'morph_r'

REPORT_FILES = {
    MAIN_R: 'conversion',
    LINESO_R: 'linesOrig',
    LINESS_R: 'linesSort',
    ALIGN_R: 'align',
    MORPH_R: 'morpho',
}
REPORT_HANDLES = {
    MAIN_R: None,
    LINESO_R: None,
    LINESS_R: None,
    ALIGN_R: None,
    MORPH_R: None,
}


TF_DIR = f'{BASE}/tf'


# SOURCE DECODING

TR = Transcription()

BIB = 'bib'
NONBIB = 'nonbib'

SOURCES = (NONBIB, BIB)  # import: nonbib before bib

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
INTERLINEAR = 'intl'
SCRIPT = 'script'
SRCLN = 'srcLn'
BIBLICAL = 'biblical'

LANG = 'lang'

B = '&'
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
oKEY = 'key'
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
oHVERSE = 'halfverse'

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
    oHVERSE,
)


# script

PH_VAL = 'paleohebrew'
GC_VAL = 'greekcapital'
SCRIPT_VALS = (PH_VAL, GC_VAL)

# characters

NB = '\u00a0'  # non-breaking space

# various types (of characters, flags, brackets/clusters)

CONS = 'cons'
VOWEL = 'vwl'
POINT = 'point'
SEP = 'sep'
PUNCT = 'punct'
NUMERAL = 'numr'
MISSING = 'missing'
UNCERTAIN = 'unc'
ADD = 'add'
TERM = 'term'

GLYPH = 'glyph'
EMPTY = 'empty'
FOREIGN = 'foreign'
OTHER = 'other'

CORRECTION = 'cor'
REMOVED = 'rem'
VACAT = 'vac'
ALTERNATIVE = 'alt'
RECONSTRUCTION = 'rec'

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
    (NB, NB),  # meaningful space inside or before or after a word
    (NB, ' '),  # meaningful space inside or before or after a word
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

L_ARAMAIC = 'a'
ARAMAIC = 'aramaic'
L_GREEK = 'g'
GREEK = 'greek'

LANGS = {
    L_GREEK: GREEK,
    L_ARAMAIC: ARAMAIC,
}

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
FOREIGNS_SETO = {x[1] for x in FOREIGNS}
FOREIGNS_UNI = {x[2] or x[1]: x[0] for x in FOREIGNS}
FOREIGNS_REP = FOREIGNS_UNI

FOREIGNS_REAL = (NUMERALS_SET - CONSONANTS_SET) | VOWELS_SET | FOREIGNS_SET

EM = 'ε'

TOKENS = (
    (VACAT, '□', None, NB, NB),
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
FLAGS_INV = {x[2]: x[0] for x in FLAGS}
FLAGS_VALUE = {x[2]: x[1] for x in FLAGS}
FLAGS_NAME = {x[0] for x in FLAGS}

BRACKETS = (
    (CORRECTION, 3, True, '^', '^', '◀', '▶', '(^ ', ' ^)'),  # PL PR
    (CORRECTION, 2, False, '>>', '<<', '┛', '┗', '(<< ', ' >>)'),  # UL UR
    (CORRECTION, 1, False, '>', '<', '┘', '└', '(< ', ' >)'),  # ul ur
    (REMOVED, 2, False, '}}', '{{', '┫', '┣', '{{ ', ' }}'),  # VL VR
    (REMOVED, 1, False, '}', '{', '┤', '├', '{ ', ' }'),  # vl vr
    (VACAT, 1, False, '≥', '≤', '┐', '┌', '(- ', ' -)'),  # dl dr
    (ALTERNATIVE, 1, False, ')', '(', '◐', '◑', '( ', ' )'),  # 0L 0R
    (RECONSTRUCTION, 1, False, ']', '[', '┑', '┍', '[ ', ' ]'),  # dL dR
    (UNCERTAIN, 2, True, '»', '«', '┙', '┕', '(# ', ' #)'),  # uL uR
)

BRACKETS_INV = {}
BRACKETS_INV.update({x[5] or x[3]: (x[0], x[1], True) for x in BRACKETS})
BRACKETS_INV.update({x[6] or x[4]: (x[0], x[1], False) for x in BRACKETS})

BRACKETS_ESC = tuple(x for x in BRACKETS if x[5] or x[6])
BRACKETS_ESCPURE = tuple(x for x in BRACKETS if (x[5] or x[6]) and not x[2])
BRACKETS_SPECIAL = tuple(x for x in BRACKETS if x[2])
BRACKETS_NAME = {x[0] for x in BRACKETS}

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


lexDisRe = re.compile(r'^(.*?)(?:[_])([0-9]+)$')
lexDisXRe = re.compile(r'[_-][0-9]+$')
foreignRe = re.compile(f'^[{"".join(FOREIGNS_SET)}]+$')
foreignoRe = re.compile(f'^[{"".join(FOREIGNS_SETO)}]+$')
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
    source="Martin Abegg's data files, personal communication",
    license='Creative Commons Attribution-NonCommercial 4.0 International License',
    licenseUrl='http://creativecommons.org/licenses/by-nc/4.0/',
    description='Dead Sea Scrolls: biblical and non-biblical scrolls',
)

otext = {
    'sectionFeatures': 'scroll,fragment,line',
    'sectionTypes': 'scroll,fragment,line',
    'fmt:text-orig-full': '{glyph}{punc}{after}',
    'fmt:text-trans-full': '{glyphe}{punce}{after}',
    'fmt:text-source-full': '{glypho}{punco}{after}',
    'fmt:text-orig-extra': 'word#{full}{after}',
    'fmt:text-trans-extra': 'word#{fulle}{after}',
    'fmt:text-source-extra': 'word#{fullo}{after}',
    'fmt:lex-orig-full': 'word#{lang:h}-{glex}{punc}{after}',
    'fmt:lex-trans-full': 'word#{lang:h}-{glexe}{punce}{after}',
    'fmt:lex-source-full': 'word#{lang:h}-{glexo}{punco}{after}',
    'fmt:morph-source-full': 'word#{morpho}{punco}{after}',
    'fmt:lex-default': 'word#{lang:h}-{lex}-{lexe}-{lexo} ',
}

intFeatures = {
    BIBLICAL,
    SRCLN,
    INTERLINEAR,
} | FLAGS_NAME | BRACKETS_NAME

featureMeta = {
    'after': {
        'description': 'space behind the word, if any',
        'values': ' (space)',
    },
    ALTERNATIVE: {
        'description': 'alternative reading',
        'values': '1',
    },
    BIBLICAL: {
        'description': 'whether we are in biblical material or not',
        'values': '1=biblical, 2=biblical but also with nonbiblical material',
        'applies': f'scroll fragment line cluster word',
        'remark': (
            'for lines it means that the material is taken from the bib source'
            ' while there is also material for this line in the nonbib source.'
            ' But the nonbib material is either identical or virtually absent,'
            ' in which case the bib material is a reconstruction and marked as such.'
        ),
    },
    BOOK: {
        'description': 'acronym of the book in which the word occurs',
    },
    CHAPTER: {
        'description': 'label of the chapter in which the word occurs',
    },
    CORRECTION: {
        'description': 'correction made by an ancient or modern editor',
        'values': '1 = modern, 2 = ancient, 3 = ancient supralinear',
    },
    FRAGMENT: {
        'description': 'label of a fragment of a scroll',
    },
    'fullo': {
        'description': (
            'full transcription (original source) of a word'
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
        'description': 'representation (original source) of a word or sign',
    },
    'glyphe': {
        'description': 'representation (ETCBC transliteration) of a word or sign',
    },
    'glyph': {
        'description': 'representation (Unicode) of a word or sign',
    },
    HALFVERSE: {
        'description': 'label of the half-verse in which the word occurs',
    },
    INTERLINEAR: {
        'description': (
            'interlinear material,'
            ' the value indicates the sequence number of the interlinear line'
        ),
    },
    LANG: {
        'description': 'language of a word or sign, only if it is not Hebrew',
        'values': ', '.join(f'{code}={lang}' for (code, lang) in LANGS.items())
    },
    'lexo': {
        'description': 'representation (original source) of a lexeme',
    },
    'lexe': {
        'description': 'representation (ETCBC transliteration) of a lexeme',
    },
    'lex': {
        'description': 'representation (Unicode) of a lexeme',
    },
    'glexo': {
        'description': (
            'representation (original source) of a lexeme'
            ' leaving out non-letters'
        ),
    },
    'glexe': {
        'description': (
            'representation (ETCBC transliteration) of a lexeme'
            ' leaving out non-letters'
        ),
    },
    'glex': {
        'description': (
            'representation (Unicode) of a lexeme'
            ' leaving out non-letters'
        ),
    },
    LINE: {
        'description': 'label of a line of a fragment of a scroll',
    },
    MERR: {
        'description': 'errors in parsing the morphology tag',
    },
    'morpho': {
        'description': 'morphological tag (by Abegg)',
    },
    'occ': {
        'description': 'edge feature from a lexeme to its occurrences',
    },
    'punco': {
        'description': 'trailing punctuation (original source) of a word',
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
    SCRIPT: {
        'description': 'script in which the word or sign is written if it is not Hebrew',
        'values': ' '.join(SCRIPT_VALS)
    },
    SCROLL: {
        'description': 'acronym of a scroll',
    },
    SRCLN: {
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
    VERSE: {
        'description': 'label of the verse in which the word occurs',
    },
}

# DATA READING

LIMIT = 10

data = []

scrollsBoth = set()
fragmentsBoth = set()
linesBoth = set()

etcbcFromTrans = {}
charGroups = {}
morphParsed = {}

morphDecl = {}
posDict = {}
valueDict = {}
valuesFound = collections.defaultdict(set)

logh = None

diags = collections.defaultdict(lambda: collections.defaultdict(dict))
biblical = None
ln = None


def bib():
  return 'B' if biblical == 1 else 'b' if biblical == 2 else 'N'


def resetDiag():
  diags.clear()


def diag(kind, rep, status):
  # diags[(kind, biblical, ln, rep)] = status
  diags[kind][rep][(biblical, ln)] = status


stMap = collections.OrderedDict((
    ('', 'ALL'),
    (1, 'OK'),
    (0, '--'),
    (-1, 'XX'),
))


def showDiag():
  global biblical
  global ln

  cw = 4
  mw = 49
  ow = 8

  cl = '─' * cw
  ml = '─' * mw
  ol = '─' * ow

  ur = f'┌{cl}┬{cl}┬{cl}┬{cl}┬{ml}┬{ol}┐\n'
  ir = f'├{cl}┼{cl}┼{cl}┼{cl}┼{ml}┼{ol}┤\n'
  dr = f'└{cl}┴{cl}┴{cl}┴{cl}┴{ml}┴{ol}┘\n'

  lineFormat = f'│{{:>{cw}}}' * 4 + f'│{{:<{mw}}}│{{:<{ow}}}│\n'

  def line(*x):
    return lineFormat.format(*x)

  def head(*x):
    return ur + line(*x) + ir

  def tail():
    return dr

  good = True

  for (kind, reps) in sorted(diags.items()):
    nK = {
        s: sum(sum(1 for oc in occs if occs[oc] == s) for occs in reps.values())
        for s in ('c', *stMap)
    }
    nK[''] = sum(len(occs) for occs in reps.values())
    okK = nK[-1] == 0 and nK[0] == 0
    if not okK:
      good = False

    report(
        head(nK[''], nK[1] + nK['c'], nK[0], nK[-1], kind, '', ''),
        newline=False,
        only=okK,
    )

    for (rep, occs) in sorted(reps.items()):
      cats = set(occs.values())
      nOccs = len(occs)
      if nOccs == 1 or len(cats) == 1 and list(cats)[0] == 'c':
        ((biblical, ln), st) = list(occs.items())[0]
        stat = [stMap[s] if s == st else '' for s in stMap]
        if st == 'c':
          stat[0] = nOccs
          stat[1] = stMap[1]
        report(
            line(*stat, rep, f'{bib()}:{ln:>6}'),
            newline=False,
            only=st == 1 or st == 'c',
        )
        continue

      nR = {
          s: sum(1 for oc in occs if occs[oc] == s)
          for s in ('c', *stMap)
      }
      nR[''] = nOccs
      okR = nR[-1] == 0 and nR[0] == 0
      if len(cats) > 1:
        report(
            line(nR[''], nR[1] + nR['c'], nR[0], nR[-1], rep, ''),
            newline=False,
            only=okR,
        )
      cDone = False
      for ((biblical, ln), st) in sorted(
          occs.items(),
          key=lambda x: (-2 if x[1] == 'c' else -x[1], x[0]),
      ):
        stat = [stMap[s] if s == st else '' for s in stMap.keys()]
        if st == 'c':
          stat[0] = nR['c']
          stat[1] = stMap[1]
          if cDone:
            continue
        report(
            line(*stat, rep, f'{bib()}:{ln:>6}'),
            newline=False,
            only=st == 1 or st == 'c',
        )
        if st == 'c':
          cDone = True
    report(tail(), newline=False, only=okK)

  return good


def readSource():
  global biblical
  global ln

  global linesBoth

  XC = '\u001b'

  scrollDecl = readYaml(SCROLL_DECL)
  fixesDecl = readYaml(FIXES_DECL)

  lineFixes = fixesDecl['lineFixes']
  fieldFixes = fixesDecl['fieldFixes']

  fixL = 'FIX (LINE)'
  fixF = 'FIX (FIELD)'

  lines = collections.defaultdict(set)

  for (biblical, lns) in lineFixes.items():
    for (ln, (fr, to, expl)) in lns.items():
      taskRep = f'{fr:>6} => {to:<6} {expl}'
      diag(fixL, taskRep.replace('\t', '\\t'), 0)

  for (biblical, lns) in fieldFixes.items():
    for (ln, fields) in lns.items():
      for (field, (fr, to, expl)) in fields.items():
        taskRep = f'{field:<8} {fr:>6} => {to:<6} {expl}'
        diag(fixF, taskRep, 0)

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
            interlinear = ''

          if '(fl)' in xLine:
            script = PH_VAL
          elif '(f0)' in xLine:
            script = GC_VAL
          elif '(fy)' in xLine:
            script = ''

          continue
        line = line.rstrip('\n')

        if ln in lineFix:
          (fr, to, expl) = lineFix[ln]
          rep = f'{fr:>6} => {to:<6} {expl}'
          if fr in line:
            line = line.replace(fr, to)
            diag(fixL, rep.replace('\t', '\\t'), 1)
          else:
            diag(fixL, rep.replace('\t', '\\t'), -1)

        if not biblical:
          if line.startswith('>'):
            line = line[1:]
            fields = line.split(splitChar)
            scroll = fields[0]
            (fragment, line) = fields[1].split(':', 1)
            if line != prevLine:
              interlinear = ''
            prevLine = line
            continue

        fields = line.split(splitChar)
        nFields = len(fields)
        if nFields > nCol:
          diag('FIELDS', f'too many: {nFields}', -1)
          continue
        elif nFields < nCol:
          fields += [''] * (nCol - nFields)
        iData = collections.defaultdict(
            lambda: '',
            ((f, c) for (f, c) in zip(nCols, fields)),
        )

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
          (verse, halfVerse) = verseNum(verse)
          oData[oVERSE] = verse
          oData[oHVERSE] = halfVerse
          word = iData[iNUM]
          if '.' in word:
            oData[oBOUND] = B
        else:
          if trans.startswith(']') and trans.endswith('['):
            text = trans[1:-1]
            if text.isdigit():
              subNum = text[::-1]
              continue

          (fragment, rest) = iData[iSCROLLREF].split(':', 1)
          (line, word) = rest.split(',', 1)
          if line != prevLine:
            interlinear = ''
          oData[oFRAGMENT] = fragment
          oData[oLINE] = line
          if line == '0':
            if subNum:
              oData[oSUB] = subNum
          (word, sub) = word.split('.', 1)
          if word == prevWord:
            theseData[-1][oBOUND] = B
          prevWord = word

        scrollx = f'{scrollDecl.get(scroll, scroll)}'
        oData[oSCROLL] = scroll
        oData[xSCROLL] = scrollx

        lines[biblical].add((scrollx, fragment, line))

        if interlinear:
          oData[oINTER] = interlinear
        if script:
          oData[oSCRIPT] = script

        analysis = iData[iANALYSIS] or ''
        (lang, lex, morph) = ('', '', '')
        if '%' in analysis:
          lang = L_ARAMAIC
          (lex, morph) = analysis.split('%', 1)
        elif '@' in analysis:
          (lex, morph) = analysis.split('@', 1)
        else:
          lex = analysis
        oData[oTRANS] = trans
        oData[oLANG] = lang
        oData[oLEX] = lex
        oData[oMORPH] = morph

        if ln in fieldFix:
          for (field, (fr, to, expl)) in fieldFix[ln].items():
            rep = f'{field:<8} {fr:>6} => {to:<6} {expl}'
            iVal = oData[field]
            if iVal == fr:
              oData[field] = to
              diag(fixF, rep, 1)
            else:
              diag(fixF, rep, -1)

        prevLine = line

        theseData.append(oData)
    report(f'{len(theseData):<6} rows out of {ln:<6} sourcelines')
    data.extend(theseData)
  report(f'DATANORM: {len(data)} rows')

  linesBoth = lines[True] & lines[False]
  report(f'LINES: {len(linesBoth)} with bib and nonbib material')


def tweakBiblical():
  tweakBiblicalLines()
  tweakBiblicalRest()
  alignBiblical()


def tweakBiblicalLines():
  global data
  global biblical
  global ln

  linesSeen = {}
  nLine = 0

  scrollx = None
  fragment = None
  line = None

  newData = []
  lineoh = REPORT_HANDLES[LINESO_R]

  for fields in data:
    biblical = oBOOK in fields
    ln = fields[oSRCLN]

    prevScrollx = scrollx
    prevFragment = fragment
    prevLine = line

    scrollx = fields[xSCROLL]
    fragment = fields[oFRAGMENT]
    line = fields[oLINE]

    key = (scrollx, fragment, line)
    lineoh.write(f'{"▪".join(key)}\n')

    if key in linesSeen:
      n = linesSeen[key]
    else:
      nLine += 1
      n = nLine
      linesSeen[key] = n

    fields[oKEY] = (n, scrollx, fragment, line, biblical)

    if key in linesBoth:
      if scrollx != prevScrollx or fragment != prevFragment or line != prevLine:
        diag('LINE (biblical and nonbiblical)', f'{scrollx:<15} {fragment:>10}:{line:>5}', 1)

    if key not in linesBoth or biblical:
      newData.append(fields)

  data = sorted(newData, key=lambda fields: fields[oKEY])


def tweakBiblicalRest():
  global biblical
  global ln

  global fragmentsBoth
  global scrollsBoth

  scrollsx = collections.defaultdict(set)
  scrollso = collections.defaultdict(set)
  fragments = collections.defaultdict(set)

  linesh = REPORT_HANDLES[LINESS_R]
  for fields in data:
    biblical = oBOOK in fields
    ln = fields[oSRCLN]

    scroll = fields[oSCROLL]
    scrollx = fields[xSCROLL]
    fragment = fields[oFRAGMENT]
    line = fields[oLINE]
    key = (scrollx, fragment, line)
    keyRep = f'{"▪".join(key)}\n'
    if key in linesBoth and not biblical:
      diag('LINES (AFTER TWEAK', f'{keyRep} not removed', -1)
    linesh.write(keyRep)

    scrollso[biblical].add(scroll)
    scrollsx[biblical].add(scrollx)
    fragments[biblical].add((scrollx, fragment))

  nScrollso = sum(len(x) for x in scrollso.values())
  nScrollsx = sum(len(x) for x in scrollsx.values())
  scrollsRep = (
      f'{nScrollsx} '
      +
      'names' if nScrollsx == nScrollso else f'({nScrollso} originally) names'
  )
  report(f'SCROLLS: {scrollsRep}')

  scrollsBoth = scrollsx[True] & scrollsx[False]
  report(f'SCROLLS: {len(scrollsBoth)} with bib and nonbib material')

  fragmentsBoth = fragments[True] & fragments[False]
  report(f'FRAGMENTS: {len(fragmentsBoth)} with bib and nonbib material')


def alignBiblical():
  global biblical
  global ln

  align = collections.defaultdict(lambda: collections.defaultdict(set))

  scroll = None
  fragment = None
  line = None
  book = None
  chapter = None
  verse = None

  for fields in data:
    biblical = oBOOK in fields
    if not biblical:
      continue

    ln = fields[oSRCLN]

    prevScroll = scroll
    prevFragment = fragment
    prevLine = line
    prevBook = book
    prevChapter = chapter
    prevVerse = verse

    scroll = fields[xSCROLL]
    fragment = fields[oFRAGMENT]
    line = fields[oLINE]
    book = fields[oBOOK]
    chapter = fields[oCHAPTER]
    verse = fields[oVERSE]

    changeScroll = scroll != prevScroll
    changeFragment = fragment != prevFragment
    changeLine = line != prevLine
    changeBook = book != prevBook
    changeChapter = chapter != prevChapter
    changeVerse = verse != prevVerse

    if changeScroll or changeBook:
      align['SB'][scroll].add(book)
      align['BS'][book].add(scroll)
      align['FC'][(scroll, fragment)].add((book, chapter))
      align['CF'][(book, chapter)].add((scroll, fragment))
      align['LV'][(scroll, fragment, line)].add((book, chapter, verse))
      align['VL'][(book, chapter, verse)].add((scroll, fragment, line))
    elif changeFragment or changeChapter:
      align['FC'][(scroll, fragment)].add((book, chapter))
      align['CF'][(book, chapter)].add((scroll, fragment))
      align['LV'][(scroll, fragment, line)].add((book, chapter, verse))
      align['VL'][(book, chapter, verse)].add((scroll, fragment, line))
    elif changeLine or changeVerse:
      align['LV'][(scroll, fragment, line)].add((book, chapter, verse))
      align['VL'][(book, chapter, verse)].add((scroll, fragment, line))

  alignh = REPORT_HANDLES[ALIGN_R]
  for (kind, corr) in align.items():
    alignh.write(f'ALIGNMENT: {kind}: {len(corr)} items\n')
    for (s, cs) in corr.items():
      alignh.write(f'\t{str(s)} => {", ".join(str(c) for c in cs)}\n')


def writeProto():
  if not os.path.exists(NORM_DIR):
    os.makedirs(NORM_DIR, exist_ok=True)
  with open(f'{NORM_DIR}/dss.tsv', 'w') as fh:
    for fields in data:
      line = '\t'.join(str(fields[col]) for col in oCOLS)
      fh.write(f'{line}\n')


def tokenizeData():
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
        kind = (
            'both'
            if c in lexes and c in transes else
            'only'
        )
        charsLetterShow.setdefault(name, []).append((kind, c, freq))
    report(f'CHARACTERS: {sum(len(x) for x in charsLetterShow.values())} used')
    for (name, items) in sorted(charsLetterShow.items()):
      report(f'\tin {name} field:', only=True)
      for (kind, c, freq) in sorted(items):
        report(f'\t\t{kind:<5} {c} {freq:>6} x', only=True)

  prevTrans = None
  prevLine = None
  prevFragment = None
  prevScroll = None

  for fields in data:
    biblical = oBOOK in fields
    ln = fields[oSRCLN]

    word = fields[oTRANS]
    lex = fields[oLEX]
    script = fields[oSCRIPT]
    thisLine = fields[oLINE]
    thisFragment = fields[oFRAGMENT]
    thisScroll = fields[xSCROLL]

    if (prevScroll, prevFragment, prevLine) != (thisScroll, thisFragment, thisLine):
      nLines += 1
      if prevTrans is not None:
        lastOfLine[prevTrans] += 1

    if script:
      diag('SCRIPT', script, 'c' if script == PH_VAL else 1 if script in SCRIPT_VALS else -1)

    lexBare = lexDisXRe.sub('', lex)
    glexo = nonGlyphLexRe.sub('', lexBare)
    isNumLex = glexo and glexo != '0' and digitRe.match(glexo)
    if isNumLex:
      lex = lex[::-1]
      glexo = glexo[::-1]

    wordPure = nonGlyphRe.sub('', word)
    isNumTrans = wordPure and numeralRe.match(wordPure)
    isAmbi = wordPure and ambiRe.match(wordPure)

    isNumCand = capitalNumRe.match(wordPure)

    if isNumCand and not isNumTrans and (isNumLex or not glexo):
      diag('NUMERAL', f'candidate "{wordPure}"', 'c')

    if isNumTrans and isNumLex:
      diag('NUMERAL', f'found "{wordPure}"', 'c')

    if not isAmbi:
      kind = (
          'trans:yes lex:no'
          if isNumTrans and not isNumLex else
          'trans:no lex:yes'
          if not isNumTrans and isNumLex else
          None
      )
      if kind is not None:
        diag('NUMERAL inconsistent LEX', f'{kind} trans="{wordPure}" lex="{glexo}"', -1)

    isForeign = wordPure and lex == NOLEX and foreignoRe.match(wordPure)
    if isForeign:
      diag('FOREIGN', wordPure, 1)

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
          diag('CHAR', f'unmapped "{c}" = {ord(c)}', -1)
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
      diag('BRACKET', f'{bOrig}{eOrig} not closed after last {last}', -1)

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
        diag('BRACKET', f'extra {bOrig}', -1)
      if isE and (last == e or last is None):
        diag('BRACKET', f'extra {eOrig}', -1)
      if isB or isE:
        nOccs[biblical] += 1
        last = c

  closeBracket()


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

  def showMorpho():
    morphh = REPORT_HANDLES[MORPH_R]
    for (morph, analysis) in sorted(morphParsed.items()):
      analysisRep = f'ERROR: {analysis[MERR]} ' if MERR in analysis else ''
      analysisRep += ' '.join(f'{k}={v}' for (k, v) in analysis.items() if k != MERR)
      morphh.write(f'{morph:<20} => {analysisRep}\n')

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

  for fields in data:
    biblical = oBOOK in fields
    ln = fields[oSRCLN]

    lang = fields[oLANG]
    morpho = fields[oMORPH]
    if lang == L_ARAMAIC:
      morpho = morpho.replace(*mRepl)  # vs code H means something different in Aramaic

    if morpho in morphParsed:
      parsed = morphParsed[morpho]
    else:
      parsed = parseTag(morpho)
      morphParsed[morpho] = parsed
    if MERR in parsed:
      diag('MORPH', f'at char: {parsed[MERR]}', -1)

  showMorpho()


def verseNum(text):
  if text.isdigit():
    return (text, None)
  return (text[0:-1], text[-1])


# DIRECTOR

def director(cv):
  global biblical
  global ln

  mRepl = morphDecl['aramaicReplace']

  report('Compiling feature data ...')

  prevScroll = None
  prevFragment = None
  prevLine = None

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
      diag('CHAR', f'unknown character uni "{text}"', -1)
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
      diag('CHAR', f'unknown character rep "{text}"', -1)
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
      cv.feature(curSlot, lang=lang)
    if script:
      cv.feature(curSlot, script=script)
    if interlinear:
      cv.feature(curSlot, intl=interlinear)
    for (name, value) in curBrackets:
      cv.feature(curSlot, **{name: value})

  nScroll = 0
  thisLex = None

  chunk = 1000
  j = 0

  biblical = None
  biblicalLine = None

  thisLine = None

  for fields in data:
    biblical = oBOOK in fields
    ln = fields[oSRCLN]

    curSlot = None
    prevLine = thisLine

    if j == chunk:
      j = 0
      progress(f' {bib()}:{ln:>6} rows', newline=False)
    j += 1
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
      cv.feature(curScroll, scroll=thisScroll)
      if biblical:
        biblicalFt = 2 if thisScroll in scrollsBoth else 1
        if biblicalFt == 2:
          diag('(NON)-BIBLICAL', f'{thisScroll} scroll', 1)
        cv.feature(curScroll, biblical=biblicalFt)
    if changeFragment or changeScroll:
      curFragment = cv.node(FRAGMENT)
      cv.feature(curFragment, scroll=thisScroll, fragment=thisFragment)
      if biblical:
        biblicalFt = 2 if (thisScroll, thisFragment) in fragmentsBoth else 1
        if biblicalFt == 2:
          diag('(NON)-BIBLICAL', f'{thisScroll} {thisFragment} fragment', 1)
        cv.feature(curFragment, biblical=biblicalFt)
    if changeLine or changeFragment or changeScroll:
      curLine = cv.node(LINE)
      cv.feature(curLine, scroll=thisScroll, fragment=thisFragment, line=thisLine)
      if biblical:
        biblicalLine = 2 if (thisScroll, thisFragment, thisLine) in linesBoth else 1
        if biblicalLine == 2:
          diag('(NON)-BIBLICAL', f'{thisScroll} {thisFragment}:{thisLine} line', 1)
        cv.feature(curLine, biblical=biblicalLine)
      else:
        biblicalLine = None

    after = None if fields[oBOUND] == B else ' '
    fullo = fields[oTRANS]
    fullx = fields[xTRANS]
    lexo = fields[oLEX]
    lang = fields[oLANG]
    morpho = fields[oMORPH]
    script = fields[oSCRIPT]
    interlinear = None if biblical else fields[oINTER]
    glypho = nonGlyphRe.sub('', fullx)
    punco = nonPunctRe.sub('', fullx)
    if punco and glypho:
      diag('CHAR', f'punct and glyphs on same line "{fullx}"', -1)

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
      glexo = nonGlyphLexRe.sub('', lexoB)
      isNoLex = glexo == '0'
      isNumLex = glexo and not isNoLex and digitRe.match(glexo)

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
      if glexo and not isNoLex:
        if isNumLex:
          glexo = glexo[::-1]
          glex = glexo
          glexe = glexo
        else:
          glex = asUni(glexo)
          glexe = asRep(glexo)
        cv.feature(thisLex, glexo=lexo, glexe=glexe, glex=glex)

    curWord = None

    if punco or glypho or lexo:
      curWord = cv.node(WORD)
      if biblical:
        cv.feature(curWord, book=fields[oBOOK])
        cv.feature(curWord, chapter=fields[oCHAPTER])
        cv.feature(curWord, verse=fields[oVERSE])
        cv.feature(curWord, halfverse=fields[oHVERSE])

      cv.feature(curWord, srcLn=ln)
      if biblical:
        if biblicalLine == 2:
          diag('(NON)-BIBLICAL', f'{thisScroll} {thisFragment}:{thisLine} word {fullo}', 1)
        if biblicalLine:
          cv.feature(curWord, biblical=biblicalLine)
      if script:
        cv.feature(curWord, script=script)
      if interlinear:
        cv.feature(curWord, intl=interlinear)
      if fullx:
        cv.feature(curWord, fullo=fullo)
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
    if lexo:
      cv.feature(curWord, lexo=lexo, lexe=lexe, lex=lex)
      cv.edge(thisLex, curWord, occ=None)
      if lexo:
        cv.feature(curWord, glexo=glexo, glexe=glexe, glex=glex)

    isNumTrans = glypho and numeralRe.match(glypho)
    isNum = isNumTrans and isNumLex
    isForeign = glypho and lexo == NOLEX and foreignRe.match(glypho)

    wTyp = (
        PUNCT if punco else
        NUMERAL if isNum else
        GLYPH if glypho or lexo else
        EMPTY if not fullx else
        OTHER
    )
    if curWord:
      cv.feature(curWord, type=wTyp)

    if punco or glypho or lexo:
      cv.feature(
          curWord,
          full=asUni(fullx, asNum=isNum, asForeign=isForeign),
          fulle=asRep(fullx, asNum=isNum, asForeign=isForeign),
      )

    if glypho:
      cv.feature(
          curWord,
          glyph=asUni(glypho, asNum=isNum, asForeign=isForeign),
          glyphe=asRep(glypho, asNum=isNum, asForeign=isForeign),
      )
    if isForeign:
      lang = L_GREEK
    if lang:
      cv.feature(curWord, lang=lang)

    if morpho:
      morph = morpho.replace(*mRepl) if lang == L_ARAMAIC else morpho
      # vs code H means something different in Aramaic
      cv.feature(curWord, morpho=morpho, **morphParsed[morph])

    typ = None
    for c in fullx:
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
        value = FLAGS_VALUE[c]
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
            if biblicalLine == 2:
              diag('(NON)-BIBLICAL', f'{thisScroll} {thisFragment}:{thisLine} cluster {name}', 1)
            if biblicalLine:
              cv.feature(cn, biblical=biblicalLine)
        else:
          cn = curBrackets[key]
          if not cv.linked(cn):
            # ew = cv.node(WORD)
            # cv.feature(ew, type=EMPTY)
            typ = EMPTY
            c = '□'
            addSlot()
            # cv.terminate(ew)
          cv.terminate(cn)
          del curBrackets[key]
    if after and curSlot:
      cv.feature(curSlot, after=after)
    cv.terminate(curWord)
    cv.terminate(thisLex)

    prevScroll = thisScroll
    prevFragment = thisFragment

  cv.terminate(curLine)
  cv.terminate(curFragment)
  cv.terminate(curScroll)

  progress(f' {bib()}:{ln:>6} rows')

  morphMeta()
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
  readSource()
  tweakBiblical()
  if not argValue['nochars']:
    checkChars()
  tokenizeData()
  if not argValue['nochars']:
    checkBrackets()
  if argValue['normwrite']:
    writeProto()
  if argValue['sourceonly']:
    showDiag()
    return True

  readMorph()
  parseMorph()
  showDiag()
  resetDiag()

  if argValue['notf']:
    return True

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
  showDiag()
  return result


# TF LOADING (to test the generated TF)

def loadTf():
  TF = Fabric(locations=[OUT_DIR])
  allFeatures = TF.explore(silent=True, show=True)
  loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
  api = TF.load(loadableFeatures, silent=False)
  if api:
    F = api.F
    info = api.info
    info(f'max node = {api.F.otype.maxNode}')
    for (word, freq) in F.glyph.freqList(nodeTypes={WORD})[0:20]:
      info(f'{freq:>6} x {word}', tm=False)
    info(f'first {ARAMAIC} word:')
    aramaicWords = [w for w in F.otype.s(WORD) if F.lang.v(w) == L_ARAMAIC]
    for w in aramaicWords[0:10]:
      info(f'{ARAMAIC:} {w:>7} = {F.fullo.v(w)} = {F.full.v(w)}', tm=False)
  return 0 if api else 1


# MAIN

def prepare():
  global stamp

  now = datetime.now().isoformat()
  stamp = time.time()

  banner = f'''This is tfFromAbegg converting {REPO} transcriptions to TF:
source version = {VERSION_SRC}
target version = {VERSION_TF}
Run started: {now}

'''
  for (r, rName) in REPORT_FILES.items():
    fh = open(f'{LOG_DIR}/{rName}-{RUNDATE}.txt', 'w')
    REPORT_HANDLES[r] = fh
    fh.write(banner)


def finalize():
  def elapsed():
    interval = time.time() - stamp
    if interval < 10:
      return f'{interval: 2.2f}s'
    interval = int(round(interval))
    if interval < 60:
      return f'{interval:>2d}s'
    if interval < 3600:
      return f'{interval // 60:>2d}m {interval % 60:>02d}s'
    return f'{interval // 3600:>2d}h {(interval % 3600) // 60:>02d}m {interval % 60:>02d}s'

  now = datetime.now().isoformat()
  trailer = f'''

Run ended: {now}
Duration: {elapsed()}
'''
  for (r, rH) in REPORT_HANDLES.items():
    rH.write(trailer)
    rH.close()


def report(msg, newline=True, only=False):
  nl = '\n' if newline else ''
  msg = f'{msg}{nl}'
  if not only:
    sys.stdout.write(msg)
    sys.stdout.flush()
  REPORT_HANDLES[MAIN_R].write(msg)


def progress(msg, newline=True):
  nl = '' if newline is None else '\n' if newline else '\r'
  msg = f'{msg}{nl}'
  sys.stdout.write(msg)


def main():
  global debug

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

  debug = argValue['debug']

  if argValue['loadonly']:
    return loadTf()

  if debug:
    import readline  # noqa
    readMorph()
    parseMorph()
    return 0

  prepare()
  good = convert()
  finalize()

  if not good:
    return 1

  if argValue['load']:
    return loadTf()

    return 0


sys.exit(main())
