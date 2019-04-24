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


# SOURCE FIXING

FIXES = dict(
    nonbib={
        36148: {
            TRANS: ('≤]', '≥≤', 'spurious ] bracket, missing ≥ bracket'),
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
        291988: {
            TRANS: ('[˝w»b|a|]', '[w»b|a|]', 'strange, unique character removed'),
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


# characters

NB = '\u00a0'  # non-breaking space

# character types

CONSONANT = 'consonant'
VOWEL = 'vowel'
POINT = 'point'
PUNCT = 'punct'
NUMERAL = 'numeral'
MISSING = 'missing'
UNCERTAIN = 'uncertain'
ADD = 'add'
TERM = 'term'

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

PUNCTS = (
    (NB, NB),
    ('\u05be', '-'),  # maqaf
    ('\u05c3', '.'),  # sof pasuq
    ('\u05f3', '/'),  # geresh as morpheme separator
    ('\u05f4', '±'),  # gershayim as paleo divider
)
PUNCTS_SET = {x[1] for x in PUNCTS}

DIGITS = set('0123456789')
CAPITALS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

NUMERALS = (
    (' 1A ', 'A'),
    (' 1a ', 'å'),
    (' 1B ', 'B'),
    (' 1f ', '∫'),
    (' 10 ', 'C'),
    (' 20 ', 'D'),
    (' 100 ', 'F'),
)

NUMERALS_SET = {x[1] for x in NUMERALS} | DIGITS | CAPITALS

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
    ('uncertain', 1, 'Ø', '?'),
    ('uncertain', 2, '«', '#'),
    ('uncertain', 3, '»', '#?'),
    ('uncertain', 4, '|', '##'),
)

FLAGS_SET = {x[2] for x in FLAGS}
FLAGS_INV = {a: name for (name, v, a, k) in FLAGS}
FLAGS_VALUE = {name: v for (name, v, a, k) in FLAGS}

BRACKETS = (
    ('correction', 3, True, '^', '^', '┛', '┗', '(^ ', ' ^)'),  # UL UR
    ('correction', 2, False, '>>', '<<', '┤', '├', '(<< ', ' >>)'),  # vl vr
    ('correction', 1, False, '>', '<', None, None, '(< ', ' >)'),
    ('removed', 2, False, '}}', '{{', '┫', '┣', '{{ ', ' }}'),  # VL VR
    ('removed', 1, False, '}', '{', None, None, '{ ', ' }'),
    ('vacat', 1, False, '≥', '≤', None, None, '(- ', ' -)'),
    ('alternative', 1, False, ')', '(', None, None, '( ', ' )'),
    ('reconstruction', 1, False, ']', '[', None, None, '[ ', ' ]'),
    ('uncertain', 2, True, '»', '«', '┘', '└', '(# ', ' #)'),  # ul ur
)

BRACKETS_INV = {}
BRACKETS_INV.update({x[5] or x[3]: (x[0], x[1], True) for x in BRACKETS})
BRACKETS_INV.update({x[6] or x[4]: (x[0], x[1], False) for x in BRACKETS})

BRACKETS_ESC = tuple(x for x in BRACKETS if x[5] or x[6])
BRACKETS_ESCPURE = tuple(x for x in BRACKETS if (x[5] or x[6]) and not x[2])
BRACKETS_SPECIAL = tuple(x for x in BRACKETS if x[2])

GLYPHS = CONSONANTS_SET | VOWELS_SET | POINTS_SET | PUNCTS_SET | NUMERALS_SET

CHARS = DIGITS | CAPITALS
for kind in (CONSONANTS, VOWELS, POINTS, PUNCTS, NUMERALS):
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

CHARS_UNI = {}
CHARS_REP = {}
for chars in (CONSONANTS, VOWELS, POINTS, PUNCTS):
  for x in chars:
    CHARS_UNI[x[1]] = x[0]
    CHARS_REP[x[1]] = TR.from_hebrew(x[0])
CHARS_UNI.update({x: f' {x} ' for x in CAPITALS})
CHARS_REP.update({x: f' {x} ' for x in CAPITALS})
CHARS_UNI.update({x[1]: x[0] for x in NUMERALS})
CHARS_REP.update({x[1]: x[0] for x in NUMERALS})
CHARS_UNI.update({x: f' {x} ' for x in DIGITS})
CHARS_REP.update({x: f' {x} ' for x in DIGITS})
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
lexDisXRe = re.compile(r'(?:^[0-9]+$)|(?:[_-][0-9]+$)')
numeralRe = re.compile(f'[{"".join(NUMERALS_SET)}]+')


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
    'fmt:text-orig-full': f'{{glyph}}{{after}}',
    'fmt:text-trans-full': f'{{glypha}}{{after}}',
    'fmt:text-source-full': f'{{glyphe}}{{after}}',
    'fmt:text-orig-extra': f'{{full}}{{after}}',
    'fmt:text-trans-extra': f'{{fulla}}{{after}}',
    'fmt:text-source-extra': f'{{fulle}}{{after}}',
    'fmt:lex-orig-full': f'{{lex}}{{after}}',
    'fmt:lex-trans-full': f'{{lexa}}{{after}}',
    'fmt:lex-etcbc-full': f'{{lexe}}{{after}}',
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
    'alternative': {
        'description': 'alternative reading',
        'values': '1',
    },
    'correction': {
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
    'removed': {
        'description': 'removed by an ancient or modern editor',
        'values': '1 = modern, 2 = ancient',
    },
    'reconstruction': {
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
    'uncertain': {
        'description': 'uncertain material in various degrees: higher degree is less certain',
        'values': '1 2 3 4',
    },
    'vacat': {
        'description': 'empty, unwritten space',
        'values': '1',
    },
}

# DATA READING

dataRaw = {}
dataToken = {}
etcbcFromTrans = {}
charGroups = {}
bookFromCode = {}
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
      bookFromCode[code] = book
  report(f'{len(bookFromCode)} manuscripts mapped')


def readData(start=None, end=None):
  diags = []
  fixes = {}

  def V(name, x):
    if name == SCROLL:
      return bookFromCode.get(x, x)
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

  if checkSource:
    report(f'FIXES:')
    for (src, lines) in sorted(FIXES.items()):
      for (line, corrections) in sorted(lines.items()):
        for (name, correction) in sorted(corrections.items()):
          seen = src in fixes and line in fixes[src] and name in fixes[src][line]
          if seen:
            (text, correction, reason, applied) = fixes[src][line][name]
          else:
            (text, correction, reason) = FIXES[src][line][name]
            applied = None
          statusRep = (
              'incorrect location'
              if applied is None else
              'applied'
              if applied is True else
              f'not applicable to "{applied}'
          )
          fixRep = f'{src:<6}:{line:>6} "{text}" => "{correction}" ({reason}'
          report(f'\t{statusRep}: {fixRep}')

    report(f'DIAGNOSTICS {len(diags)} lines')
    for (src, i, diag) in diags:
      report(f'{src:<6}:{i:>6} \t{diag}')


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


def checkBooks():
  booksFound = set()

  for (src, lines) in dataRaw.items():
    for (i, fields) in lines:
      book = fields[SCROLL]
      booksFound.add(book)

  report(f'{len(booksFound)} CODEX ACRONYMS in the data')
  for book in sorted(booksFound):
    report(f'\t{book}', only=True)


def checkChars():
  charsFound = collections.Counter()
  charsMapped = set()
  charsUnmapped = {}
  exampleLimit = 3
  charsLetter = {}
  numerals = collections.Counter()
  lastOfLine = collections.Counter()
  slashInner = {}
  nLines = 0

  def showChars():
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
    for (name, items) in sorted(charsLetterShow.items()):
      report(f'\tin {name} field:')
      for (label, c, freq) in sorted(items):
        report(f'\t\t{label:<5} {c} {freq:>6} x')

  def showNumerals():
    report('NUMERALS')
    for (num, freq) in sorted(numerals.items()):
      report(f'\t{num:<30} : {freq:>5} x')

  def showLastOfLine():
    report(f'LAST-OF-LINE of {nLines} lines')
    nInner = sum(len(x) for x in slashInner.values())
    report(f'\tNumber of times word "/" does not end a line: {nInner}')
    for (src, lines) in slashInner.items():
      for (i, scroll, fragment, line) in lines[0:10]:
        report(f'\t\t{src:<6} : {i:>6} in {scroll} {fragment}:{line}')

    report(f'\tNumber of ways to end a line: {len(lastOfLine)} ways to end a line')
    for (word, amount) in sorted(lastOfLine.items(), key=lambda x: (-x[1], x[0]))[0:20]:
      report(f'\t\t{word:<10} {amount:>6} x')

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
      isNumeral = word.isupper()
      if isNumeral:
        nums = numeralRe.findall(word)
        for num in nums:
          numerals[num] += 1
      for (name, text) in ((TRANS, word), (LEX, lexBare)):
        for c in text:
          charsFound[c] += 1
          if isNumeral and c.isupper() and name == TRANS and c not in CHARS:
            charsMapped.add(c)
          elif c in CHARS:
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

  unused = set(CHARS) - charsMapped - CAPITALS - TOKENS_FIXED
  if unused:
    report(f'WARNING: {len(unused)} declared but unused characters')
    unusedStr = ''.join(sorted(unused))
    report(f'\tunused = {unusedStr}')
  totalUnmapped = 0
  if charsUnmapped:
    report(f'WARNING: {len(charsUnmapped)} unmapped characters')
    for (c, examples) in sorted(charsUnmapped.items()):
      freq = charsFound[c]
      totalUnmapped += freq
      report(f'{c:<6} occurs {freq:>6} x')
      for (src, i, fields) in examples:
        report(f'\t{src}:{i + 1} trans="{unesc(fields[TRANS])}" lex="{fields[LEX]}"')
      report('')
    unmappedStr = ''.join(sorted(charsUnmapped))
    report(f'UNMAPPED: {unmappedStr}')
    report(f'TOTAL {totalUnmapped} occurrences of unmapped characters')
  else:
    report('OK: no unmapped characters')
  report(f'MAPPED ({len(charsMapped)})')
  showChars()
  showNumerals()
  showLastOfLine()


def checkBracketPair(b, e):
  limitErrors = 10
  limitContext = 5

  (bOrig, eOrig) = (bunesc(b), bunesc(e))
  report(f'BRACKETS {bOrig} {eOrig} ...')

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
      report(f'\t{src:>6}:          {nOccs[src]} occurrences')
      report(f'\t{src:>6}: WARNING: {nErrors} imbalances')
      for (i, c) in theseErrors[0:limitErrors]:
        start = max((0, i - limitContext))
        end = min((nLines, i + limitContext + 1))
        report('')
        for (j, fields) in lines:
          if start <= j < end:
            trans = fields[TRANS]
            prefix = '==>' if i == j else '   '
            report(f'\t\t{src:>6}:{j + 1:>6} {bunesc(c):>6} {prefix} {unesc(trans)}')
      msg = f'... and {nErrors -limitErrors} more' if nErrors > limitErrors else ''
      report(f'\t\t{msg}')
    else:
      report(f'\t{src:>6}: OK       {nOccs[src]} balanced occurrences')

    report('')

  totalErrs = sum(len(x) for x in errors.values())
  totalOccs = sum(x for x in nOccs.values())

  report(f'\tIMBALANCES:  {totalErrs}')
  report(f'\tOCCURRENCES: {totalOccs}')

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

  report(f'OVERALL IMBALANCES:  {totalErrs}')
  report(f'OVERALL OCCURRENCES: {totalOccs}')


def prepare():
  global logh
  logh = open(REPORT, 'w')


def finalize():
  logh.close()


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
  if checkOnly:
    return True
  tokenizeData()
  if checkSource:
    checkBrackets()
    checkBooks()

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

  def addSlot():
    nonlocal curSlot
    if token:
      curSlot = cv.slot()
      cv.feature(curSlot, glypha=token, type=typ)
      if typ in {CONSONANT, VOWEL, POINT, PUNCT, NUMERAL} | TOKENS_TYPE:
        glyph = ''.join(CHARS_UNI[c] for c in token)
        glyphe = ''.join(CHARS_REP[c] for c in token)
      cv.feature(curSlot, glyph=glyph, glyphe=glyphe)

      for (name, value) in curBrackets:
        cv.feature(curSlot, **{name: value})

  nScroll = 0
  nBook = 0
  for (src, lines) in dataToken.items():
    curSlot = None
    for (i, fields) in lines:
      thisScroll = fields[SCROLL]
      thisFragment = fields[FRAGMENT]
      thisLine = fields[LINE]
      if thisScroll != prevScroll:
        nScroll += 1
        progress(f'scroll {nScroll:<5} {thisScroll:<20}', newline=False)
        cv.terminate(curLine)
        cv.terminate(curFragment)
        cv.terminate(curScroll)
        curScroll = cv.node(SCROLL)
        curFragment = cv.node(FRAGMENT)
        curLine = cv.node(LINE)
        cv.feature(curScroll, acro=thisScroll)
        cv.feature(curFragment, label=thisFragment)
        cv.feature(curLine, number=int(thisLine))
      elif thisFragment != prevFragment:
        cv.terminate(curLine)
        cv.terminate(curFragment)
        curFragment = cv.node(FRAGMENT)
        curLine = cv.node(LINE)
        cv.feature(curFragment, label=thisFragment)
        cv.feature(curLine, number=int(thisLine))
      elif thisLine != prevLine:
        cv.terminate(curLine)
        curLine = cv.node(LINE)
        cv.feature(curLine, number=int(thisLine))

      if src == 'bib':
        thisBook = fields[BOOK]
        thisChapter = fields[CHAPTER]
        thisVerse = fields[VERSE]
        (thisVerse, thisHalfVerse) = verseNum(thisVerse)
        if thisBook != prevBook:
          nBook += 1
          cv.terminate(curHalfVerse)
          cv.terminate(curVerse)
          cv.terminate(curChapter)
          cv.terminate(curBook)
          curBook = cv.node(BOOK)
          curChapter = cv.node(CHAPTER)
          curVerse = cv.node(VERSE)
          cv.feature(curBook, acro=thisBook)
          cv.feature(curChapter, label=thisChapter)
          cv.feature(curVerse, number=thisVerse)
          if thisHalfVerse:
            curHalfVerse = cv.node(HALFVERSE)
            cv.feature(curHalfVerse, number=thisVerse, label=thisHalfVerse)
        elif thisChapter != prevChapter:
          cv.terminate(curHalfVerse)
          cv.terminate(curVerse)
          cv.terminate(curChapter)
          curChapter = cv.node(CHAPTER)
          curVerse = cv.node(VERSE)
          cv.feature(curChapter, label=thisChapter)
          cv.feature(curVerse, number=thisVerse)
          if thisHalfVerse:
            curHalfVerse = cv.node(HALFVERSE)
            cv.feature(curHalfVerse, number=thisVerse, label=thisHalfVerse)
        elif thisVerse != prevVerse:
          cv.terminate(curHalfVerse)
          cv.terminate(curVerse)
          curVerse = cv.node(VERSE)
          cv.feature(curVerse, number=thisVerse)
          if thisHalfVerse:
            curHalfVerse = cv.node(HALFVERSE)
            cv.feature(curHalfVerse, number=thisVerse, label=thisHalfVerse)
        elif thisHalfVerse != prevHalfVerse:
          cv.terminate(curHalfVerse)
          curHalfVerse = cv.node(HALFVERSE)
          cv.feature(curHalfVerse, number=thisVerse, label=thisHalfVerse)

      word = fields[TRANS]
      lexa = fields[LEX]
      lexaDis = lexDisRe.findall(lexa)
      if lexaDis:
        (lexaB, lexaN) = lexaDis[0]
        lexaN = f'_{lexaN}' if lexaN else ''
        lexa = f'{lexaB}{lexaN}'
      else:
        (lexaB, lexaN) = (lexa, '')
      lex = (''.join(CHARS_UNI[c] for c in lexaB)) + lexaN
      lexe = (''.join(CHARS_REP[c] for c in lexaB)) + lexaN
      thisLex = lexIndex.get(lex, None)
      if thisLex:
        cv.resume(thisLex)
      else:
        thisLex = cv.node(LEX)
        lexIndex[lex] = thisLex
      curWord = cv.node(WORD)
      cv.feature(thisLex, lexa=lexa, lexe=lexe, lex=lex)
      cv.feature(curWord, lexa=lexa, lexe=lexe, lex=lex)
      isNumeral = word.isupper()
      token = ''
      typ = None
      after = ' ' if fields[BOUND] == B else None
      glypha = ''.join(c for c in word if c in GLYPHS)
      glyph = ''.join(CHARS_UNI[c] for c in glypha)
      glyphe = ''.join(CHARS_REP[c] for c in glypha)
      fulla = word
      full = ''.join(CHARS_UNI[c] for c in fulla)
      fulle = ''.join(CHARS_REP[c] for c in fulla)
      for c in word:
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
            cv.terminate(cn)
            del curBrackets[key]
      addSlot()
      punca = ''
      punce = ''
      punc = ''
      cv.feature(curWord, fulla=fulla, fulle=fulle, full=full, after=after)
      if glypha:
        cv.feature(curWord, glypha=glypha)
      if glyphe:
        cv.feature(curWord, glyphe=glyphe)
      if glyph:
        cv.feature(curWord, glyph=glyph)
      if punca:
        cv.feature(curWord, punca=punca)
      if punce:
        cv.feature(curWord, punce=punce)
      if punc:
        cv.feature(curWord, punc=punc)
      cv.terminate(curWord)
      cv.terminate(thisLex)
      prevScroll = thisScroll
      prevFragment = thisFragment
      prevLine = thisLine
      if src == 'bib':
        prevBook = thisBook
        prevChapter = thisChapter
        prevVerse = thisVerse

    cv.terminate(curLine)
    cv.terminate(curFragment)
    cv.terminate(curScroll)
    if src == 'bib':
      cv.terminate(curHalfVerse)
      cv.terminate(curVerse)
      cv.terminate(curChapter)
      cv.terminate(curBook)

  return True


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

report(f'Abegg transcription to TF converter for {REPO}')
report(f'Abegg source version = {VERSION_SRC}')
report(f'TF  target version = {VERSION_TF}')
good = convert()

if not checkOnly and generateTf and good:
  loadTf()
