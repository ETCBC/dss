import sys
import os
import collections
import re
from shutil import rmtree

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
SCROLL = 'scroll'
FRAGMENT = 'fragment'
LINE = 'line'
TRANS = 'trans'
LEX = 'lex'
MORPH = 'morph'
BOUND = 'bound'
INTERLINEAR = 'interlinear'
SCRIPT = 'script'

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
    ('m', 'M'),
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
CONSONANT_SET = {x[1] for x in CONSONANTS}

VOWELS = (
    ('\u05b0', 'V'),  # sheva
    ('\u05b0', '∂'),  # sheva ??
    ('\u05b0', '√'),  # sheva ??
    ('\u05b0', 'J'),  # sheva after kaf
    ('\u05b1', 'T'),  # hataf segol
    ('\u05b2', 'S'),  # hataf patah
    ('\u05b3', 'F'),  # hataf qamats
    ('\u05b3', 'ƒ'),  # hataf qamats ??
    ('\u05b4', 'I'),  # hiriq
    ('\u05b4', 'ˆ'),  # hiriq ??
    ('\u05b4', 'î'),  # hiriq ??
    ('\u05b4', 'Ê'),  # hiriq without preceding consonant
    ('\u05b5', 'E'),  # tsere
    ('\u05b5', 'é'),  # tsere ??
    ('\u05b5', '´'),  # tsere ??
    ('\u05b6', 'R'),  # segol
    ('\u05b6', '®'),  # segol ??
    ('\u05b6', '‰'),  # segol ??
    ('\u05b7', 'A'),  # patah
    ('\u05b8', 'D'),  # qamats
    ('\u05b8', 'Î'),  # qamats ??
    ('\u05b8', 'Å'),  # qamats ??
    ('\u05b9', 'O'),  # holam
    ('\u05ba', 'ø'),  # holam ??
    ('\u05ba', 'Ï'),  # holam ??
    ('\u05bb', 'U'),  # qubbuts
    ('\u05bb', 'ü'),  # qubbuts ??
    ('\u05bb', '¨'),  # qubbuts ??
)
VOWEL_SET = {x[1] for x in VOWELS}

LETTERS = (
)
LETTER_SET = {x[1] for x in LETTERS}

POINTS = (
    ('\u05bc', ';'),  # dagesh
)

POINT_SET = {x[1] for x in POINTS}

ACCENTS = (
    ('', '◊'),  # ??
    ('', '…'),  # ??
    ('', 'Ú'),  # ??
    ('', '¥'),  # ??
    ('', 'Ω'),  # ??
)

ACCENT_SET = {x[1] for x in ACCENTS}

PUNCTS = (
    ('־', '-'),
    ('׃', '.'),
)
PUNCT_SET = {x[1] for x in PUNCTS}

HEBREW_MAP = {}
for chars in (CONSONANTS, VOWELS, POINTS, ACCENTS, PUNCTS):
  for (o, t) in chars:
    HEBREW_MAP[t] = o

CONSONANT = 'consonant'
VOWEL = 'vowel'
POINT = 'point'
ACCENT = 'point'
PUNCT = 'punct'

DIGITS = (
    ('0', '0'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
    ('6', '6'),
    ('7', '7'),
    ('8', '8'),
    ('9', '9'),
)

NUMERALS = (
    ('1A', 'A'),
    ('1a', 'å'),
    ('1B', 'B'),
    ('1f', '∫'),
    ('10', 'C'),
    ('20', 'D'),
    ('100', 'F'),
)
CAPITALS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

NUMERAL_SET = {x[1] for x in NUMERALS + DIGITS} | CAPITALS
NUMERALS_INV = {}
NUMERALS_INV.update({k: k for k in CAPITALS})
NUMERALS_INV.update({k: value for (value, k) in NUMERALS})
NUMERALS_INV.update({k: value for (value, k) in DIGITS})

ONE = '\\'
ONE_REPL = '/'

TOKENS = (
    ('missing', '░'),
    ('doubtful', '?'),
    ('uncertain', '/'),
    ('uncertain', '\\'),
    ('unknown', '�'),
    ('add', '+'),
    ('paleodivider', '±'),
)
TOKEN_SET = {x[1] for x in TOKENS}
TOKENS_INV = {k: name for (name, k) in TOKENS}

MISSING = '--'
MISSING_ESC = '░'

# nonbib 53527 lex: CHAG
# nonbib 53566 lex: HN
# nonbib 53584 lex: THE
#    only occurrences of GH

WHITESPACE = (
    (' ', '\u00a0'),
)
WHITESPACE_SET = {x[1] for x in WHITESPACE}

FLAGS = (
    ('damaged', '«'),
    ('damagedUncertain', '|'),
    ('uncertain', 'Ø'),
)

FLAGS_INV = {k: name for (name, k) in FLAGS}

BRACKETS = (
    ('correction_ancient', False, '>>', '<<', '┤', '├'),  # vl vr
    ('correction_modern', False, '>', '<'),
    ('correction_supra', True, '^', '^', '┛', '┗'),  # UL UR
    ('removed_ancient', False, '}}', '{{', '┫', '┣'),  # VL VR
    ('removed_modern', False, '}', '{'),
    ('vacat', False, '≥', '≤'),
    ('alternative', False, ')', '('),
    ('reconstruction_modern', False, ']', '['),
    ('c1', True, '»', '«', '┘', '└'),  # ul ur
)

BRACKETS_INV = {}
BRACKETS_INV.update({x[4] if len(x) > 4 else x[2]: (x[0], True) for x in BRACKETS})
BRACKETS_INV.update({x[5] if len(x) > 4 else x[3]: (x[0], False) for x in BRACKETS})

BRACKETS_ESC = tuple(x for x in BRACKETS if len(x) > 4)
BRACKETS_ESCPURE = tuple(x for x in BRACKETS if len(x) > 4 and not x[1])
BRACKETS_SPECIAL = tuple(x for x in BRACKETS if x[1])

BRACKETS_ESCAPED = (
    {x[2] for x in BRACKETS_ESC} |
    {x[3] for x in BRACKETS_ESC}
)

CHARS = set()
for kind in (CONSONANTS, VOWELS, POINTS, ACCENTS, PUNCTS, LETTERS, NUMERALS, WHITESPACE, DIGITS):
  CHARS |= {x[1] for x in kind}

for kind in (TOKENS, FLAGS):
  CHARS |= {x[1] for x in kind}

CHARS |= {b[2] for b in BRACKETS}
CHARS |= {b[3] for b in BRACKETS}

bEsc = {}
bEsc.update({x[2]: x[4] for x in BRACKETS_ESC})
bEsc.update({x[3]: x[5] for x in BRACKETS_ESC})

bUnesc = {}
bUnesc.update({x[4]: x[2] for x in BRACKETS_ESC})
bUnesc.update({x[5]: x[3] for x in BRACKETS_ESC})


bSpecialRe = {}
for bs in BRACKETS_SPECIAL:
  name = bs[0]
  b = re.escape(bs[2])
  e = re.escape(bs[3])
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
  text = text.replace(MISSING_ESC, MISSING)
  return text


# SOURCE FIXING

FIXES = dict(
    nonbib={
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
    },
    bib={
        147775: {
            TRANS: ('[^≥', '[≥', 'imbalance in ^ brackets'),
        },
        158295: {
            TRANS: ('[\\\\]^', '[\\\\]', 'imbalance in ^ brackets'),
        },
        202008: {
            TRANS: ('alwhiM', 'alwhyM', 'hireq => yod'),
        },
    },
)


# TF CONFIGURATION

slotType = 'consonant'

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
    'sectionTypes': 'codex,fragment,line',
    'fmt:text-orig-full': f'{{lettersu}}{{after}}',
    'fmt:text-trans-full': f'{{lettersa}}{{after}}',
    'fmt:text-etcbc-full': f'{{letterse}}{{after}}',
    'fmt:lex-orig-full': f'{{lexu}}{{after}}',
    'fmt:lex-trans-full': f'{{lexa}}{{after}}',
    'fmt:lex-etcbc-full': f'{{lexe}}{{after}}',
}

intFeatures = set('''
    number
'''.strip().split())

featureMeta = {
    'acro': {
        'description': 'Acronym of codex',
    },
    'label': {
        'description': 'label of fragment',
    },
    'number': {
        'description': 'Number of line',
    },
    'lettersu': {
        'description': 'unicode hebrew letters of a word or consonant',
    },
    'lettersa': {
        'description': 'transliterated text (Abegg) of a word or consonant',
    },
    'letterse': {
        'description': 'transliterated text (ETCBC) of a word or consonant',
    },
    'lexu': {
        'description': 'unicode hebrew letters of a lexeme',
    },
    'lexa': {
        'description': 'transliterated text (Abegg) of a lexeme',
    },
    'lexe': {
        'description': 'transliterated text (ETCBC) of a lexeme',
    },
    'after': {
        'description': 'material between this word and the next',
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
          fixRep = f'{src:<6}:{line:>6} "{text}" => "{correction}"'
          report(f'\t{fixRep:<40} : {statusRep}')

    report(f'DIAGNOSTICS {len(diags)} lines')
    for (src, i, diag) in diags:
      report(f'{src:<6}:{i:>6} \t{diag}')


def tokenizeData():

  nonBreakingRe = re.compile(r' +')  # this is non-breaking space \u0xa0

  def esc(text):
    nonlocal prevS

    text = text.replace(ONE, ONE_REPL)
    text = text.replace(MISSING, MISSING_ESC)
    for bs in BRACKETS_SPECIAL:
      bRe = bSpecialRe[bs[0]]
      text = bRe.sub(bSpecialRepl(bs[4], bs[5]), text)
      b = bs[2]
      e = bs[3]
      bEsc = bs[4]
      eEsc = bs[5]
      if b == e and b in text:
        r = eEsc if prevS == bEsc else bEsc
        prevS = r
        text = text.replace(b, r)
    for be in BRACKETS_ESCPURE:
      text = text.replace(be[2], be[4]).replace(be[3], be[5])
    return text

  def V(name, x):
    if name == TRANS or name == LEX:
      x = nonBreakingRe.sub(' ', x)
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

  def showFlagChars():
    lexes = set(charsLetter[LEX]) if LEX in charsLetter else set()
    transes = set(charsLetter[TRANS]) if TRANS in charsLetter else set()
    for (name, freqs) in sorted(charsLetter.items()):
      report(f'\t{name}:')
      for (c, freq) in sorted(freqs.items(), key=lambda x: (-x[1], x[0])):
        label = (
            'both'
            if c in lexes and c in transes else
            'lex'
            if c in lexes else
            'trans'
        )
        report(f'\t\t{label:<5} {c} {freq:>6} x')

  def showNumerals():
    report('NUMERALS')
    for (num, freq) in sorted(numerals.items()):
      report(f'\t{num:<30} : {freq:>5} x')

  lexDisRe = re.compile(r'(?:^[0-9]+$)|(?:[_-][0-9]+$)')
  numeralRe = re.compile(f'[{"".join(NUMERALS_INV)}]+')

  for src in dataRaw:
    for (i, fields) in dataRaw[src]:
      word = fields[TRANS]
      lex = fields[LEX]
      lexBare = lexDisRe.sub('', lex)
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
          if c in LETTER_SET:
            charsLetter.setdefault(name, collections.Counter())[c] += 1

  unused = set(CHARS) - charsMapped - BRACKETS_ESCAPED - {MISSING_ESC}
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
  showFlagChars()
  showNumerals()


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
  for (name, kind, b, e, *x) in BRACKETS:
    (bEsc, eEsc) = x if len(x) else (b, e)

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


# DIRECTOR

def director(cv):
  report('Compiling feature data from tokens')

  prevScroll = None
  prevFragment = None
  prevLine = None

  curScroll = None
  curFragment = None
  curLine = None

  def addSlot():
    nonlocal curSlot
    if token:
      curSlot = cv.slot()
      cv.feature(curSlot, lettersa=token, type=typ)
      if typ in {CONSONANT, VOWEL, POINT, ACCENT, PUNCT}:
        letterso = ''.join(HEBREW_MAP[c] for c in token)
        letterse = TR.from_hebrew(letterso)
        cv.feature(curSlot, letterso=letterso, letterse=letterse)

      for kind in curBrackets:
        cv.feature(curSlot, **{kind: 1})

  nScroll = 0
  for (src, lines) in dataToken.items():
    curSlot = None
    curBrackets = set()
    for (i, fields) in lines:
      thisScroll = fields[SCROLL]
      thisFragment = fields[FRAGMENT]
      thisLine = fields[LINE]
      if fields[SCROLL] != prevScroll:
        nScroll += 1
        progress(f'scroll {nScroll:<5} {thisScroll:<20}', newline=False)
        cv.terminate(curLine)
        cv.terminate(curFragment)
        cv.terminate(curScroll)
        curScroll = cv.node(SCROLL)
        curFragment = cv.node(FRAGMENT)
        curLine = cv.node(LINE)
      elif fields[FRAGMENT] != prevFragment:
        cv.terminate(curLine)
        cv.terminate(curFragment)
        curFragment = cv.node(FRAGMENT)
        curLine = cv.node(LINE)
      elif fields[LINE] != prevLine:
        cv.terminate(curLine)
        curLine = cv.node(LINE)

      word = fields[TRANS]
      isNumeral = word.isupper()
      token = ''
      typ = None
      for c in word:
        if c in TOKEN_SET:
          addSlot()
          token = c
          typ = TOKENS_INV[c]
          addSlot()
        elif c in CONSONANT_SET:
          addSlot()
          token = c
          typ = 'consonant'
        elif c in VOWEL_SET:
          if token and typ == 'consonant':
            token += c
          else:
            addSlot()
            token = c
            typ = 'vowel'
            addSlot()
        elif isNumeral and c in NUMERAL_SET:
          if token and typ == 'numeral':
            token += c
          else:
            addSlot()
            token = c
            typ = 'numeral'
        elif c in PUNCT_SET:
          addSlot()
          token = c
          typ = 'punctuation'
          addSlot()
        elif c in WHITESPACE_SET:
          addSlot()
          token = c
          typ = 'whitespace'
        elif c in FLAGS_INV:
          cv.feature(curSlot, **{FLAGS_INV[c]: 1})
        elif c in BRACKETS_INV:
          (kind, isOpen) = BRACKETS_INV[c]
          if isOpen:
            curBrackets.add(kind)
          else:
            curBrackets.discard(kind)
      addSlot()
      prevScroll = thisScroll
      prevFragment = thisFragment
      prevLine = thisLine

    cv.terminate(curLine)
    cv.terminate(curFragment)
    cv.terminate(curScroll)

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

report(f'Abegg transcription to TF converter for {REPO}')
report(f'Abegg source version = {VERSION_SRC}')
report(f'TF  target version = {VERSION_TF}')
good = convert()

if generateTf and good:
  loadTf()
