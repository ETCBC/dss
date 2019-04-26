import sys
import os
import collections
import re
from shutil import rmtree
from functools import reduce

from tf.fabric import Fabric
from tf.writing.transcription import Transcription
from tf.convert.walker import CV

# LOCATIONS

ORG = 'etcbc'
REPO = 'dss'
VERSION_SRC = '1.0'
VERSION_TF = '1.0'

LOCAL_BASE = os.path.expanduser('~/local')
GH_BASE = os.path.expanduser('~/github')

SOURCE_DIR = f'{LOCAL_BASE}/{REPO}/prepared/{VERSION_SRC}'

BASE = f'{GH_BASE}/{ORG}/{REPO}'
TF_PATH = f'{BASE}/tf'
OUT_DIR = f'{TF_PATH}/{VERSION_TF}'

META_DIR = f'{BASE}/sources/meta'
MAN_TABLE = f'{META_DIR}/mans.txt'

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

B = 'B'

# fields

COLUMNS = {
    BIB: (
        BOOK,
        CHAPTER,
        VERSE,
        SCROLL,
        FRAGMENT,
        LINE,
        TRANS,
        LEX,
        MORPH,
        BOUND,
        SCRIPT,
    ),
    NONBIB: (
        SCROLL,
        FRAGMENT,
        LINE,
        TRANS,
        LEX,
        MORPH,
        BOUND,
        INTERLINEAR,
        SCRIPT,
    ),
}

CINDEX = {}
CLEN = {}

for (src, fields) in COLUMNS.items():
  for (i, field) in enumerate(fields):
    CINDEX.setdefault(src, {})[field] = i
    CLEN[src] = len(CINDEX[src])


# characters

NB = '\u00a0'  # non-breaking space

# SOURCE FIXING

FIXES = dict(
    nonbib={
        36148: {
            TRANS: ('≤]', '≥≤', 'spurious ] bracket, missing ≥ bracket'),
        },
        53527: {
            TRANS: ('CHAG', 'chag', 'lowercasing'),
        },
        53566: {
            TRANS: ('HN', 'hn', 'lowercasing'),
        },
        53584: {
            TRANS: ('THE', 'hn', 'lowercasing'),
        },
        55019: {
            TRANS: (f'{NB}±', '≥≤', 'spurious non-breaking space before paleodivider'),
        },
        140504: {
            TRANS: ('b]', 'b', 'spurious ] bracket'),
        },
        140582: {
            TRANS: ('b]', 'b', 'spurious ] bracket'),
        },
        140616: {
            TRANS: ('b]', 'b', 'spurious ] bracket'),
        },
        157910: {
            TRANS: ('^b', '^b^', 'imbalance in ^ brackets'),
        },
        191862: {
            TRANS: ('y»tkwØ_nw', 'y»tkwØnw', '_ removed (1 of 3)'),
        },
        225327: {
            TRANS: ('t_onh]', 'tonh]', '_ removed (1 of 3)'),
        },
        259060: {
            TRANS: ('oyN_', 'oyN', '_ removed (1 of 3)'),
        },
        261956: {
            TRANS: ('a', 'A', 'a is numeral A'),
        },
        263103: {
            TRANS: ('a', 'A', 'a is numeral A'),
        },
        291988: {
            TRANS: ('[˝w»b|a|]', '[w»b|a|]', 'strange, unique character removed'),
        },
        301907: {
            TRANS: ('3', ']3[', 'wrapped a digit in "] ["'),
        },
        313324: {
            LEX: ('\\0', '\\', 'distribute "\\0" over two fields'),
            MORPH: ('', '0', 'distribute "\\0" over two fields'),
        },
        313632: {
            LINE: ('13,3,1', '13', 'strange numbering replaced by plain number'),
        }
    },
    bib={
        87334: {
            TRANS: ('≥', '≥≤', 'missing ≤ bracket'),
        },
        147775: {
            TRANS: ('[^≥', '[≥', 'imbalance in ^ brackets'),
        },
        154735: {
            TRANS: ('≥1a≤', '≥a≤', 'spurious character "1"'),
        },
        154751: {
            TRANS: ('≥2a≤', '≥a≤', 'spurious character "2"'),
        },
        158295: {
            TRANS: ('[\\\\]^', '[\\\\]', 'imbalance in ^ brackets'),
        },
        185452: {
            TRANS: ('h«\\\\wØ(', 'h«\\\\wØ', 'spurious ( bracket'),
        },
        202008: {
            TRANS: ('alwhiM', 'alwhyM', 'hireq => yod'),
        },
    },
)


# various types (of characters, flags, brackets/clusters)

CONSONANT = 'consonant'
VOWEL = 'vowel'
POINT = 'point'
SEP = 'separator'
PUNCT = 'punct'
NUMERAL = 'numeral'
MISSING = 'missing'
UNCERTAIN = 'uncertain'
ADD = 'add'
TERM = 'term'

EMPTY = 'empty'

CORRECTION = 'correction'
REMOVED = 'removed'
VACAT = 'vacat'
ALTERNATIVE = 'alternative'
RECONSTRUCTION = 'reconstruction'

CONSONANTS = (
    ('א', 'a'),
    ('ב', 'b'),
    ('ג', 'g'),
    ('ד', 'd'),
    ('ה', 'h'),
    ('ו', 'w'),
    ('ז', 'z'),
    ('ח', 'j'),
    ('ט', 'f'),
    ('י', 'y'),
    ('כ', 'k'),
    ('ך', 'K'),
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
    ('ק', 'q'),
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

SEPS = (
    (NB, NB),
    ('\u05be', '-'),  # maqaf
    ('\u05c0', '/'),  # paseq as morpheme separator
)
SEPS_SET = {x[1] for x in SEPS}

PUNCTS = (
    ('\u05c3', '.'),  # sof pasuq
    ('\u05c3' * 2, '±'),  # double sof pasuq as paleo divider
)
PUNCTS_SET = {x[1] for x in PUNCTS}

N1A = 'å'
N1F = '∫'

NUMERALS = (
    ('\u05d0', 'A'),  # alef
    ('\u05d0\u05c4', N1A),  # alef with upper dot
    ('\u05d0\u05c5', 'B'),  # alef with lower dot
    ('\u05d0\u05bd', N1F),  # alef with meteg
    ('\u05d9', 'C'),  # yod
    ('\u05da', 'D'),  # kaf
    ('\u05e7', 'F'),  # qof
)
GERESH = '\u05f3'
GERSHAYIM = '\u05f4'

NUMERALS_SET = {x[1] for x in NUMERALS}
NUMERALS_INV = {x[1]: x[0] for x in NUMERALS}


def uniFromNum(num):
  if len(num) == 1:
    return f'{GERESH}{NUMERALS_INV[num]}'
  return f'{"".join(NUMERALS_INV[c] for c in num[0:-1])}{GERSHAYIM}{NUMERALS_INV[num[-1]]}'


TOKENS = (
    (MISSING, '--', '░', ' 0 ', 'ε'),
    (UNCERTAIN, '?', None, ' ? ', ' ? '),
    (UNCERTAIN, '\\', None, ' # ', ' # '),
    (UNCERTAIN, '�', None, ' #? ', ' #? '),
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
    (CORRECTION, 3, True, '^', '^', '┛', '┗', '(^ ', ' ^)'),  # UL UR
    (CORRECTION, 2, False, '>>', '<<', '┤', '├', '(<< ', ' >>)'),  # vl vr
    (CORRECTION, 1, False, '>', '<', None, None, '(< ', ' >)'),
    (REMOVED, 2, False, '}}', '{{', '┫', '┣', '{{ ', ' }}'),  # VL VR
    (REMOVED, 1, False, '}', '{', None, None, '{ ', ' }'),
    (VACAT, 1, False, '≥', '≤', None, None, '(- ', ' -)'),
    (ALTERNATIVE, 1, False, ')', '(', None, None, '( ', ' )'),
    (RECONSTRUCTION, 1, False, ']', '[', None, None, '[ ', ' ]'),
    (UNCERTAIN, 2, True, '»', '«', '┘', '└', '(# ', ' #)'),  # ul ur
)

BRACKETS_INV = {}
BRACKETS_INV.update({x[5] or x[3]: (x[0], x[1], True) for x in BRACKETS})
BRACKETS_INV.update({x[6] or x[4]: (x[0], x[1], False) for x in BRACKETS})

BRACKETS_ESC = tuple(x for x in BRACKETS if x[5] or x[6])
BRACKETS_ESCPURE = tuple(x for x in BRACKETS if (x[5] or x[6]) and not x[2])
BRACKETS_SPECIAL = tuple(x for x in BRACKETS if x[2])

DIGITS_H = (
    ('a', '1'),
    ('b', '2'),
    ('g', '3'),
    ('d', '4'),
    ('h', '5'),
    ('w', '6'),
    ('z', '7'),
    ('j', '8'),
    ('f', '9'),
    ('y', '10'),
    ('ya', '11'),
    ('yb', '12'),
)
DIGITS_SET = set('0123456789')
DIGITSH_SET = set('abgdhwzjfy')
DIGITS_INV = {x[1]: x[0] for x in DIGITS_H}

GLYPHS_ALPHA = CONSONANTS_SET | VOWELS_SET | POINTS_SET | SEPS_SET
GLYPHS_LEX = GLYPHS_ALPHA | DIGITS_SET
GLYPHS_SET = GLYPHS_ALPHA | NUMERALS_SET
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
bUnesc.update({x[5]: x[3] for x in BRACKETS_ESC})
bUnesc.update({x[6]: x[4] for x in BRACKETS_ESC})


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
  for (tx, t) in TOKENS_UNESC.items():
    text = text.replace(tx, t)
  return text


lexDisRe = re.compile(r'^(.*?)(?:[_-]?)([0-9]+$)')
lexDisXRe = re.compile(r'[_-][0-9]+$')
capitalRe = re.compile(f'^[A-Z{N1A}{N1F}]+$')
numeralRe = re.compile(f'^[{"".join(NUMERALS_SET)}]+$')
numeralMRe = re.compile(f'''(^'[{DIGITSH_SET}]+$)|(^[{DIGITSH_SET}]+"[{DIGITSH_SET}]$)''')
digitRe = re.compile(f'^[0-9]+$')
ambiRe = re.compile(f'^[{"".join(GLYPHS_AMBI)}]+$')
nonGlyphRe = re.compile(f'[^A-Za-z{re.escape("".join(GLYPHS_SET))}]+')
nonGlyphLexRe = re.compile(f'[^A-Za-z{re.escape("".join(GLYPHS_LEX))}]+')

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
    'sectionFeatures': 'acro,label,number',
    'sectionTypes': 'scroll,fragment,line',
    'fmt:text-orig-full': f'{{glyph}}{{punc}}{{after}}',
    'fmt:text-trans-full': f'{{glyphe}}{{punce}}{{after}}',
    'fmt:text-source-full': f'{{glypha}}{{punca}}{{after}}',
    'fmt:text-orig-extra': f'{{full}}{{after}}',
    'fmt:text-trans-extra': f'{{fulle}}{{after}}',
    'fmt:text-source-extra': f'{{fulla}}{{after}}',
    'fmt:lex-orig-full': f'{{lex}}{{punc}}{{after}}',
    'fmt:lex-trans-full': f'{{lexe}}{{punce}}{{after}}',
    'fmt:lex-etcbc-full': f'{{lexa}}{{punca}}{{after}}',
}

intFeatures = set('''
    number
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
    CORRECTION: {
        'description': 'correction made by an ancient or modern editor',
        'values': '1 = modern, 2 = ancient, 3 = ancient supralinear',
    },
    'glypha': {
        'description': 'representation (Abegg) of a word or sign',
    },
    'glyphe': {
        'description': 'representation (ETCBC) of a word or sign',
    },
    'glyph': {
        'description': 'representation (Unicode) of a word or sign',
    },
    'label': {
        'description': 'label of a fragment or chapter',
    },
    'lexa': {
        'description': 'representation (Abegg) of a lexeme',
    },
    'lexe': {
        'description': 'representation (ETCBC) of a lexeme',
    },
    'lex': {
        'description': 'representation (Unicode) of a lexeme',
    },
    'number': {
        'description': 'number of line or verse',
    },
    'punca': {
        'description': 'trailing punctuation (Abegg) of a word',
    },
    'punce': {
        'description': 'trailing punctuation (ETCBC) of a word',
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
    'fulla': {
        'description': (
            'full transcription (Abegg) of a word'
            ' including flags and brackets'
        ),
    },
    'fulle': {
        'description': (
            'full transcription (ETCBC) of a word'
            ' including flags and brackets'
        ),
    },
    'full': {
        'description': (
            'full transcription (Unicode) of a word'
            ' including flags and brackets'
        ),
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

dataRaw = {}
dataToken = {}
etcbcFromTrans = {}
charGroups = {}
acroFromCode = {}
logh = None


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


codexRe = re.compile(r'^([0-9]+)[^0-9]')
codexMinRe = re.compile(r'^-([0-9]*)[^0-9]')


def readBooks():
  with open(MAN_TABLE) as fh:
    for line in fh:
      (code, book) = line.rstrip().split('\t')
      acroFromCode[code] = book
  report(f'SCROLL acronym mapping: {len(acroFromCode)} names mapped', only=True)
  report('', only=True)


def readData(start=None, end=None):
  diags = []
  fixes = {}
  numFixes = {}

  def V(name, x):
    if name == SCROLL:
      return acroFromCode.get(x, x)
    return '' if x == NOFIELD else x

  def parseLine():
    nonlocal prevX
    nonlocal result

    fields = line.strip().split('\t')
    if len(fields) != CLEN[src]:
      diags.append((
          src, i, f'ERROR: wrong number of columns: {len(fields)} instead of {CLEN[src]}'
      ))
      return

    result = {name: V(name, fields[i]) for (name, i) in CINDEX[src].items()}

    if lineFixes:
      for (name, (text, correction, reason)) in lineFixes.items():
        fixed = False
        value = result[name]
        if value == text:
          fixed = True
          result[name] = correction
        else:
          fixed = text
        fixes.setdefault(src, {}).setdefault(i + 1, {})[name] = (text, correction, reason, fixed)

    text = result[TRANS]
    if text.startswith(']') and text.endswith('['):
      num = text[1:-1]
      if len(num) > 1:
        num = num[::-1]
      if num in DIGITS_INV:
        numNew = DIGITS_INV[num]
        numNew = f"'{numNew}" if len(numNew) == 1 else f'{numNew[0:-1]}"{numNew[-1]}'
        result[TRANS] = numNew
        numFixes.\
            setdefault(f'{num} => {numNew}', {}).\
            setdefault(src, []).\
            append(i + 1)

    codex = result[SCROLL]
    match = codexMinRe.match(codex)
    if match:
      if prevX is None:
        diags.append((src, i, f'SCROLL WARNING {codex:<10} => ?? (NO PREVIOUS EXAMPLE'))
      else:
        number = match.group(1)
        newCodex = (prevX[0] if len(number) else prevX) + codex[1:]
        result[SCROLL] = newCodex
        diags.append((src, i, f'SCROLL {codex:<10} => {newCodex}'))
    else:
      match = codexRe.match(codex)
      prevX = match.group(1) if match else None

  for src in SOURCES:
    startRep = 'beginning' if start is None else start
    endRep = 'end' if end is None else end
    report(f'Reading {src:>6} {startRep}-{endRep} ...', newline=False)
    theseFixes = FIXES[src]
    with open(f'{SOURCE_DIR}/dss_{src}.txt') as fh:
      prevX = None
      for (i, line) in enumerate(fh):
        if start is not None and i < start - 1:
          continue
        if end is not None and i > end - 1:
          break
        lineFixes = theseFixes.get(i + 1, None)
        result = None
        parseLine()
        dataRaw.setdefault(src, []).append((i, result))
    report(f'{len(dataRaw[src]):<6} lines')
  report('', only=True)

  if checkSource:
    nDeclared = sum(sum(len(x) for x in srcs.values()) for srcs in FIXES.values())
    report(f'FIXES: DECLARED', only=True)
    nApplied = 0
    for (src, lines) in sorted(FIXES.items()):
      for (line, corrections) in sorted(lines.items()):
        for (name, correction) in sorted(corrections.items()):
          seen = src in fixes and line in fixes[src] and name in fixes[src][line]
          if seen:
            (text, correction, reason, applied) = fixes[src][line][name]
          else:
            (text, correction, reason) = FIXES[src][line][name]
            applied = None
          if applied is True:
            nApplied += 1
          statusRep = (
              'incorrect location'
              if applied is None else
              'applied'
              if applied is True else
              f'not applicable to "{applied}'
          )
          fixRep = f'{src:<6}:{line:>6} "{text:>10}" => "{correction:<10}" ({reason}'
          report(f'\t{statusRep}: {fixRep}', only=True)
    statusRep = (
        f'all {nDeclared} applied'
        if nDeclared == nApplied else
        f'ERROR: {nDeclared - nApplied} not applied'
    )
    report(f'FIXES: {nDeclared} declared: {statusRep}')
    report('', only=True)

    report(f'FIXES: DIGITS', only=True)
    nOccs = 0
    for (num, srcs) in sorted(numFixes.items()):
      report(f'{num} ({sum(len(x) for x in srcs.values())} x)', only=True)
      for (src, lines) in srcs.items():
        nOccs += len(lines)
        linesRep = ' '.join(str(i + 1) for i in lines[0:LIMIT])
        report(f'\t{src:<6} {len(lines)} x: {linesRep}', only=True)
    report(f"FIXES: DIGITS ]n[ => {len(numFixes)} numerals in {nOccs} occurrences")
    report('', only=True)

    report(f'FIXES: SCROLLS: {len(diags)} scroll name completions')
    for (src, i, diag) in diags:
      report(f'{src:<6}:{i:>6} \t{diag}', only=True)
    report('', only=True)


def tokenizeData():

  nonBreakingRe = re.compile(f'{NB}+')

  def esc(text):
    nonlocal prevS

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
    return text

  def V(name, x):
    if name == TRANS or name == LEX:
      x = nonBreakingRe.sub(NB, x)
    if name == TRANS:
      xEsc = esc(x)
      return xEsc
    return x

  def parseLine():
    nonlocal result
    result = {name: V(name, value) for (name, value) in fields.items()}

  for (src, lines) in dataRaw.items():
    report(f'Tokenizing {src:>6} ...', newline=False)
    prevS = None
    for (i, fields) in lines:
      result = None
      parseLine()
      dataToken.setdefault(src, []).append((i, result))
    report(f'{len(dataToken[src]):<6} entries')
  report('', only=True)


def checkBooks():
  scrollsFound = set()

  for (src, lines) in dataRaw.items():
    for (i, fields) in lines:
      book = fields[SCROLL]
      scrollsFound.add(book)

  report(f'SCROLLS: {len(scrollsFound)} ACRONYMS in the data')
  for book in sorted(scrollsFound):
    report(f'\t{book}', only=True)
  report('', only=True)


def checkChars():
  charsFound = collections.Counter()
  charsMapped = set()
  charsUnmapped = {}
  exampleLimit = 3
  charsLetter = {}
  numerals = collections.Counter()
  numeralCand = {}
  numeralLexTF = {}
  numeralLexFT = {}
  lastOfLine = collections.Counter()
  slashInner = {}
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

  def showNumerals():
    report(f'NUMERALS: {len(numerals)} distinct numerals in {sum(numerals.values())} occurrences')
    report(f'\t{"LEX":>7} = {"WORD":<17} (freq x)', only=True)
    for ((word, lex), freq) in sorted(numerals.items()):
      lexRep = f'"{lex}"'
      wordRep = f'"{word}"'
      report(f'\t{lexRep:>7} = {wordRep:<17} : {freq:>5} x', only=True)
    report('', only=True)

    for (dest, msg) in (
        (numeralCand, f'NUMERALS: {len(numeralCand)} unrecognized potential numerals'),
        (numeralLexTF, f'NUMERALS: TRANS-yes LEX-no:  {len(numeralLexTF):>2} conflicts'),
        (numeralLexFT, f'NUMERALS: TRANS-no  LEX-yes: {len(numeralLexFT):>2} conflicts'),
    ):
      report(msg, only=not len(dest))
      if len(dest):
        report(f'\t{"LEX":>7} = {"WORD":<15} (freq x)', only=True)
      for ((word, lex), srcs) in sorted(dest.items()):
        nF = sum(len(x) for x in srcs.values())
        lexRep = f'"{lex}"'
        wordRep = f'"{word}"'
        report(f'\t{lexRep:>7} = {wordRep:<17} ({nF} x)', only=True)
        for (src, lines) in srcs.items():
          report(f'\t{"":>7}{src} ({len(lines)} x)', only=True)
          for (i, scroll, fragment, line) in lines[0:10]:
            report(f'\t{"":>7}\t{i + 1:>6} in {scroll} {fragment}:{line} "{word}"', only=True)
      report('', only=True)

  def showLastOfLine():
    report(f'LINES: {nLines} lines')
    nInner = sum(len(x) for x in slashInner.values())
    report(f'\tNumber of times word "/" does not end a line: {nInner}', only=True)
    for (src, lines) in slashInner.items():
      for (i, scroll, fragment, line) in lines[0:10]:
        report(f'\t\t{src:<6} : {i:>6} in {scroll} {fragment}:{line}', only=True)
    report('', only=True)

    report(f'\tNumber of ways to end a line: {len(lastOfLine)} ways to end a line', only=True)
    for (word, amount) in sorted(lastOfLine.items(), key=lambda x: (-x[1], x[0]))[0:20]:
      report(f'\t\t{word:<10} {amount:>6} x', only=True)
    report('', only=True)

  prevTrans = None
  prevLine = None
  prevFragment = None
  prevScroll = None

  for src in dataRaw:
    for (i, fields) in dataRaw[src]:
      word = fields[TRANS]
      lex = fields[LEX]
      thisLine = fields[LINE]
      thisFragment = fields[FRAGMENT]
      thisScroll = fields[SCROLL]
      if (prevScroll, prevFragment, prevLine) != (thisScroll, thisFragment, thisLine):
        nLines += 1
        if prevTrans is not None:
          lastOfLine[prevTrans] += 1
      else:
        if prevTrans == '/':
          slashInner.setdefault(src, []).append((i, prevScroll, prevFragment, prevLine))

      lexBare = lexDisXRe.sub('', lex)
      lexPure = nonGlyphLexRe.sub('', lexBare)
      isNumLex = lexPure and digitRe.match(lexPure)
      if isNumLex:
        lex = lex[::-1]
        lexPure = lexPure[::-1]

      isNumM = numeralMRe.match(word)
      wordPure = nonGlyphRe.sub('', word)
      isNumTrans = wordPure and numeralRe.match(wordPure)
      isAmbi = wordPure and ambiRe.match(wordPure)

      isNumCand = capitalRe.match(wordPure)

      if isNumCand and not isNumTrans and (isNumLex or not lexPure):
        numeralCand.\
            setdefault((wordPure, lexPure), {}).\
            setdefault(src, []).\
            append((i, thisScroll, thisFragment, thisLine))

      if isNumTrans and isNumLex:
        numerals[(wordPure, lexPure)] += 1

      if not isAmbi:
        dest = (
            numeralLexTF
            if isNumTrans and not isNumLex else
            numeralLexFT
            if not isNumTrans and isNumLex else
            None
        )
        if dest is not None:
          dest.\
              setdefault((wordPure, lexPure), {}).\
              setdefault(src, []).\
              append((i, thisScroll, thisFragment, thisLine))

      digital = DIGITS_SET | {"'", '"'}

      for (name, legal, text) in ((TRANS, CHARS, word), (LEX, CHARS_LEX, lexBare)):
        for c in text:
          charsFound[c] += 1
          if (
              c in legal
              or
              (
                  c in digital
                  and
                  (
                      (name == TRANS and isNumM)
                      or
                      (name == LEX and isNumLex)
                  )
              )
          ):
            charsMapped.add(c)
          else:
            if c in charsUnmapped:
              if len(charsUnmapped[c]) < exampleLimit:
                charsUnmapped[c].append((src, i, fields))
            else:
              charsUnmapped[c] = [(src, i, fields)]
          charsLetter.setdefault(name, collections.Counter())[c] += 1
      prevLine = thisLine
      prevFragment = thisFragment
      prevScroll = thisScroll
      prevTrans = word

  unused = (CHARS | CHARS_LEX) - charsMapped - TOKENS_FIXED
  if unused:
    unusedStr = ''.join(sorted(unused))
    report(f'CHARACTERS: WARNING: UNUSED: {unusedStr} ({len(unused)} chars)')
  totalUnmapped = 0
  if charsUnmapped:
    unmappedStr = ''.join(sorted(charsUnmapped))
    for (c, examples) in sorted(charsUnmapped.items()):
      freq = charsFound[c]
      totalUnmapped += freq
      report(f'{c:<6} occurs {freq:>6} x', only=True)
      for (src, i, fields) in examples:
        report(f'\t{src}:{i + 1} trans="{unesc(fields[TRANS])}" lex="{fields[LEX]}"', only=True)
      report('', only=True)
    report(
        f'CHARACTERS: WARNING: UNMAPPED:'
        f' {unmappedStr} ({len(charsUnmapped)} distinct chars in {totalUnmapped} occurrences)'
    )
    report('', only=True)
  showChars()
  showNumerals()
  showLastOfLine()


def checkBracketPair(b, e):
  limitErrors = 10
  limitContext = 5

  (bOrig, eOrig) = (bunesc(b), bunesc(e))
  report(f'BRACKETS {bOrig} {eOrig} ...', only=True)

  last = None
  errors = {}
  nOccs = collections.Counter()

  for (src, lines) in dataToken.items():
    last = None
    for (i, fields) in lines:
      nLines = len(lines)
      word = fields[TRANS]
      for c in word:
        isB = c == b
        isE = c == e
        if (
            isB and last == b
            or
            isE and (last == e or last is None)
        ):
            errors.setdefault(src, []).append((i, c))
        if isB or isE:
          nOccs[src] += 1
          last = c
    if last is not None and last != e:
      errors.setdefault(src, []).append((i + 1, f'last={last}'))

  for (src, lines) in dataToken.items():
    nLines = len(lines)
    theseErrors = errors.get(src, [])
    nErrors = len(theseErrors)
    if nErrors:
      report(f'\t{src:>6}:          {nOccs[src]} occurrences', only=True)
      report(f'\t{src:>6}: WARNING: {nErrors} imbalances', only=True)
      for (i, c) in theseErrors[0:limitErrors]:
        start = max((0, i - limitContext))
        end = min((nLines, i + limitContext + 1))
        report('', only=True)
        for (j, fields) in lines:
          if start <= j < end:
            trans = fields[TRANS]
            prefix = '==>' if i == j else '   '
            report(f'\t\t{src:>6}:{j + 1:>6} {bunesc(c):>6} {prefix} {unesc(trans)}', only=True)
      msg = f'... and {nErrors -limitErrors} more' if nErrors > limitErrors else ''
      report(f'\t\t{msg}', only=True)
    else:
      report(f'\t{src:>6}: OK       {nOccs[src]} balanced occurrences', only=True)
    report('', only=True)

  totalErrs = sum(len(x) for x in errors.values())
  totalOccs = sum(x for x in nOccs.values())

  report(f'\tIMBALANCES:  {totalErrs}', only=True)
  report(f'\tOCCURRENCES: {totalOccs}', only=True)
  report('', only=True)

  return (totalErrs, totalOccs)


def checkBrackets():
  totalErrs = 0
  totalOccs = 0
  for (name, value, kind, b, e, bEsc, eEsc, *x) in BRACKETS:
    if bEsc is None:
      bEsc = b
    if eEsc is None:
      eEsc = e
    (errs, occs) = checkBracketPair(bEsc, eEsc)
    totalErrs += errs
    totalOccs += occs

  status = f'ERROR: {totalErrs} imbalances' if totalErrs else 'all balanced'
  report(f'BRACKETS: {status} ({totalOccs} bracket occurrences)')
  report('', only=True)


def prepare():
  global logh
  logh = open(REPORT, 'w')


def finalize():
  global logh
  logh.close()
  logh = None


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
  readBooks()
  # readData(start=5310, end=5310)
  readData()
  if checkSource:
    checkChars()
  tokenizeData()
  if checkSource:
    checkBrackets()
    checkBooks()

  if checkOnly:
    return True

  cv = getConverter()

  result = cv.walk(
      director,
      slotType,
      otext=otext,
      generic=generic,
      intFeatures=intFeatures,
      featureMeta=featureMeta,
      generateTf=generateTf,
  )
  finalize()
  return result


def verseNum(text):
  if text.isdigit():
    return (text, None)
  return (text[0:-1], text[-1])


# DIRECTOR

def director(cv):
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

  def error(kind, instance):
    errors.setdefault(kind, []).append((src, i, instance))

  def showErrors():
    progress('')
    if not errors:
      report('NO ERRORS')
    else:
      for (kind, instances) in sorted(errors.items()):
        report(f'ERROR: {kind} ({len(instances)} x)')
        for (e, (src, i, instance)) in enumerate(instances):
          report(f'\t{src:<6} : {i + 1:>6} = {instance}', only=e >= LIMIT)
      report('END OF ERRORS')

  def addSlot():
    nonlocal curSlot
    if token:
      curSlot = cv.slot()
      cv.feature(curSlot, glypha=token, type=typ)
      if typ == NUMERAL:
        glyph = uniFromNum(token)
        glyphe = TR.from_hebrew(glyph)
      elif typ in {CONSONANT, VOWEL, POINT, SEP, PUNCT} | TOKENS_TYPE:
        glyph = ''.join(CHARS_UNI[c] for c in token)
        glyphe = ''.join(CHARS_REP[c] for c in token)
      cv.feature(curSlot, glyph=glyph, glyphe=glyphe)

      for (name, value) in curBrackets:
        cv.feature(curSlot, **{name: value})

  def terminateWord():
    if 'B' in glypha:
      print(f'\n"{glypha}"\n')
      print(f'\n"{fulla}"\n')
    glyph = ''.join(CHARS_UNI[c] for c in glypha)
    glyphe = ''.join(CHARS_REP[c] for c in glypha)
    full = ''.join(CHARS_UNI[c] for c in fulla)
    fulle = ''.join(CHARS_REP[c] for c in fulla)
    if (fulla or punca) and curWord is None:
      error('Word material but no current word node', fulla)
    if curWord:
      cv.feature(curWord, fulla=fulla, fulle=fulle, full=full)
      if glypha:
          cv.feature(curWord, glypha=glypha, glyphe=glyphe, glyph=glyph)
      if after:
          cv.feature(curWord, after=after)
    if punca:
      punc = ''.join(CHARS_UNI[c] for c in punca)
      punce = ''.join(CHARS_REP[c] for c in punca)
      if curWord:
        cv.feature(
            curWord,
            punca=punca, punce=punce, punc=punc,
        )
    cv.terminate(curWord)
    cv.terminate(thisLex)

  nScroll = 0
  nBook = 0
  glypha = ''
  fulla = ''
  punca = ''
  after = ''
  thisLex = None

  for (src, lines) in dataToken.items():
    curSlot = None
    for (i, fields) in lines:
      thisScroll = fields[SCROLL]
      thisFragment = fields[FRAGMENT]
      thisLine = fields[LINE]
      changeScroll = thisScroll != prevScroll
      changeFragment = thisFragment != prevFragment
      changeLine = thisLine != prevLine
      if changeLine or changeFragment or changeScroll:
        terminateWord()
        cv.terminate(curLine)
      if changeFragment or changeScroll:
        cv.terminate(curFragment)
      if changeScroll:
        cv.terminate(curScroll)
        nScroll += 1
        curScroll = cv.node(SCROLL)
        cv.feature(curScroll, acro=thisScroll)
        progress(f'scroll {nScroll:<5} {thisScroll:<20}', newline=False)
      if changeFragment or changeScroll:
        curFragment = cv.node(FRAGMENT)
        cv.feature(curFragment, label=thisFragment)
      if changeLine or changeFragment or changeScroll:
        curLine = cv.node(LINE)
        cv.feature(curLine, number=int(thisLine))
        curWord = cv.node(WORD)
        glypha = ''
        fulla = ''
        punca = ''
        after = ''

      if src == 'bib':
        thisBook = fields[BOOK]
        thisChapter = fields[CHAPTER]
        thisVerse = fields[VERSE]
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

      after = ' ' if fields[BOUND] == B else None
      thisFulla = fields[TRANS]
      lexa = fields[LEX]
      thisGlypha = ''.join(c for c in thisFulla if c in GLYPHS_SET)
      thisPunca = ''.join(c for c in thisFulla if c in PUNCTS_SET)
      if thisPunca and thisGlypha:
        error('punctuation and glyphs on same line', thisFulla)
      if thisGlypha:
        terminateWord()
        fulla = thisFulla
        glypha = thisGlypha
        punca = ''
        curWord = cv.node(WORD)
      else:
        cv.terminate(thisLex)
        fulla += thisFulla
        punca += thisPunca

      (lexaB, lexaN) = (lexa, '')
      isNumLex = False
      if lexa:
        lexaDis = lexDisRe.findall(lexa)
        if lexaDis:
          (lexaB, lexaN) = lexaDis[0]
          lexaN = f'_{lexaN}' if lexaN else ''
          lexa = f'{lexaB}{lexaN}'
        else:
          (lexaB, lexaN) = (lexa, '')
        lexPure = nonGlyphLexRe.sub('', lexaB)
        isNumLex = lexPure and digitRe.match(lexPure)
        if lexa == 'B':
          error('Unknown lexeme', lexa)
          lexaB = ''
        elif isNumLex:
          lexaB = lexaB[::-1]
          lex = lexaB + lexaN
          lexe = lexaB + lexaN
        else:
          lex = (''.join(CHARS_UNI[c] for c in lexaB)) + lexaN
          lexe = (''.join(CHARS_REP[c] for c in lexaB)) + lexaN
        thisLex = lexIndex.get(lex, None)
        if thisLex:
          cv.resume(thisLex)
        else:
          thisLex = cv.node(LEX)
          lexIndex[lex] = thisLex
        cv.feature(thisLex, lexa=lexa, lexe=lexe, lex=lex)
        cv.feature(curWord, lexa=lexa, lexe=lexe, lex=lex)

      isNumTrans = thisGlypha and numeralRe.match(thisGlypha)
      isNumeral = isNumTrans and isNumLex
      isNumH = numeralMRe.match(thisFulla)

      if isNumH:
        token = thisFulla
        typ = NUMERAL
        addSlot()
        token = ''
        typ = None
        terminateWord()
        glypha = ''
        fulla = ''
      else:
        token = ''
        typ = None
        for c in thisFulla:
          if c in TOKENS_SET:
            addSlot()
            token = c
            typ = TOKENS_INV[c]
            addSlot()
          elif c in CONSONANTS_SET:
            addSlot()
            token = c
            typ = CONSONANT
          elif c in VOWELS_SET:
            if token and typ == CONSONANT:
              token += c
            else:
              addSlot()
              token = c
              typ = VOWEL
              addSlot()
          elif isNumeral and c in NUMERALS_SET:
            if token and typ == NUMERAL:
              token += c
            else:
              addSlot()
              token = c
              typ = NUMERAL
          elif c in SEPS_SET:
            addSlot()
            token = c
            typ = SEP
            addSlot()
          elif c in PUNCTS_SET:
            addSlot()
            token = c
            typ = PUNCT
            addSlot()
          elif c in FLAGS_INV:
            name = FLAGS_INV[c]
            value = FLAGS_VALUE[name]
            cv.feature(curSlot, **{FLAGS_INV[c]: value})
          elif c in BRACKETS_INV:
            (name, value, isOpen) = BRACKETS_INV[c]
            key = (name, value)
            if isOpen:
              cn = cv.node(CLUSTER)
              curBrackets[key] = cn
              cv.feature(cn, type=f'{name}{value}')
            else:
              cn = curBrackets[key]
              if not cv.linked(cn):
                em = cv.slot()
                cv.feature(em, type=EMPTY)
              cv.terminate(cn)
              del curBrackets[key]
        addSlot()

      prevScroll = thisScroll
      prevFragment = thisFragment
      prevLine = thisLine
      if src == 'bib':
        prevBook = thisBook
        prevChapter = thisChapter
        prevVerse = thisVerse
        prevHalfVerse = thisHalfVerse

    terminateWord()
    cv.terminate(curLine)
    cv.terminate(curFragment)
    cv.terminate(curScroll)
    if src == 'bib':
      cv.terminate(curHalfVerse)
      cv.terminate(curVerse)
      cv.terminate(curChapter)
      cv.terminate(curBook)

  showErrors()
  return not errors


# TF LOADING (to test the generated TF)

def loadTf():
  TF = Fabric(locations=[OUT_DIR])
  allFeatures = TF.explore(silent=True, show=True)
  loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
  api = TF.load(loadableFeatures, silent=False)
  if api:
    report(f'max node = {api.F.otype.maxNode}')
    report(api.F.root.freqList()[0:20])


# MAIN

generateTf = len(sys.argv) == 1 or '-notf' not in sys.argv[1:]
checkSource = len(sys.argv) > 1 and '-check' in sys.argv[1:]
checkOnly = len(sys.argv) > 1 and '-checkonly' in sys.argv[1:]
checkSource = checkSource or checkOnly

report(f'This is tfFromAbegg converting {REPO} transcriptions to TF:')
report(f'\tsource version = {VERSION_SRC}')
report(f'\ttarget version = {VERSION_TF}')
good = convert()

if not checkOnly and generateTf and good:
  loadTf()
