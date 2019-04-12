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
CHAR_TABLE = f'{META_DIR}/chars.txt'
MAN_TABLE = f'{META_DIR}/mans.txt'

LOG_DIR = f'{BASE}/log'
REPORT = f'{LOG_DIR}/conversion.txt'

TF_DIR = f'{BASE}/tf'


# SOURCE DECODING

BIB = 'bib'
NONBIB = 'nonbib'

SOURCES = (BIB, NONBIB)

NOFIELD = '-'

COLUMNS = {
    BIB: '''
        book
        chapter
        verse
        scroll
        fragment
        line
        trans
        lex
        morph
        bound
        script
        ''',
    NONBIB: '''
        scroll
        column
        line
        trans
        lex
        morph
        bound
        interlinear
        script
        ''',
}

CINDEX = {}
CLEN = {}

for (src, fieldStr) in COLUMNS.items():
  for (i, field) in enumerate(fieldStr.strip().split()):
    CINDEX.setdefault(src, {})[field] = i
    CLEN[src] = len(CINDEX[src])


TRANS = 'trans'
LEX = 'lex'

nonBreakingRe = re.compile(r' +')  # this is non-breaking space \u0xa0


def V(name, x):
  if name == TRANS or name == LEX:
    x = nonBreakingRe.sub(' ', x)
  if name == TRANS:
    return esc(x)
  if name == 'scroll':
    return bookFromCode.get(x, x)
  return '' if x == NOFIELD else x


BRACKETS_DOUBLE = (
    ('>>', '<<', '┤', '├'),  # vl vr
    ('}}', '{{', '┫', '┣'),  # VL VR
    (']]', '[[', '┐', '┌'),  # dl dr
)

BRACKETS_SPECIAL = (
    ('»', '«', '┘', '└'),  # ul ur
)

BRACKETS = (
    (
        ('≥', '≤'),
        ('»', '«'),
        (')', '('),
        ('>', '<'),
        ('}', '{'),
        (']', '['),
    )
    +
    tuple((x[0], x[1]) for x in BRACKETS_DOUBLE)
)

ESCAPE_CHARS = (
    {x[2] for x in BRACKETS_DOUBLE} |
    {x[3] for x in BRACKETS_DOUBLE} |
    {x[2] for x in BRACKETS_SPECIAL} |
    {x[3] for x in BRACKETS_SPECIAL}
)

bEsc = {}
bEsc.update({x[0]: x[2] for x in BRACKETS_DOUBLE})
bEsc.update({x[1]: x[3] for x in BRACKETS_DOUBLE})
bEsc.update({x[0]: x[2] for x in BRACKETS_SPECIAL})
bEsc.update({x[1]: x[3] for x in BRACKETS_SPECIAL})

bUnesc = {}
bUnesc.update({x[2]: x[0] for x in BRACKETS_DOUBLE})
bUnesc.update({x[3]: x[1] for x in BRACKETS_DOUBLE})
bUnesc.update({x[2]: x[0] for x in BRACKETS_SPECIAL})
bUnesc.update({x[3]: x[1] for x in BRACKETS_SPECIAL})


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

data = {}
origFromTrans = {}
etcbcFromTrans = {}
charGroups = {}
bookFromCode = {}
logh = None


def report(msg, newline=True, only=False):
  nl = '\n' if newline else ''
  msg = f'{msg}{nl}'
  if not only:
    sys.stdout.write(msg)
  if logh:
    logh.write(msg)


BS = BRACKETS_SPECIAL[0]

fishBracketRe = re.compile(
    f'{BS[0]}'
    f'([^{BS[0]}{BS[1]}]*)'
    f'{BS[1]}'
)


def fishBracketRepl(match):
  return f'{BS[2]}{match.group(1)}{BS[3]}'


def besc(c):
  return bEsc.get(c, c)


def bunesc(c):
  return bUnesc.get(c, c)


def esc(text):
  for bd in BRACKETS_DOUBLE:
    text = text.replace(bd[0], bd[2]).replace(bd[1], bd[3])
  text = fishBracketRe.sub(fishBracketRepl, text)
  return text


def unesc(text):
  for bd in BRACKETS_DOUBLE:
    text = text.replace(bd[2], bd[0]).replace(bd[3], bd[1])
  text = text.replace('┘', '»').replace('└', '«')
  return text


codexRe = re.compile(r'^([0-9]+)[^0-9]')
codexMinRe = re.compile(r'^-([0-9]*)[^0-9]')


def parseLine(src, i, line, prevX):
  fields = line.strip().split('\t')
  if len(fields) != CLEN[src]:
    print(f'{src}:{i} ERROR: wrong number of columns: {len(fields)} instead of {CLEN[src]}')
    return (prevX, None)

  result = {name: V(name, fields[i]) for (name, i) in CINDEX[src].items()}
  codex = result['scroll']
  match = codexMinRe.match(codex)
  if match:
    if prevX is None:
      report(f'\tSCROLL WARNING {codex:<10} => ?? (NO PREVIOUS EXAMPLE')
    else:
      number = match.group(1)
      newCodex = (prevX[0] if len(number) else prevX) + codex[1:]
      result['scroll'] = newCodex
      report(f'\tSCROLL {codex:<10} => {newCodex}')
  else:
    match = codexRe.match(codex)
    prevX = match.group(1) if match else None
  return (prevX, result)


def readChars():
  tr = Transcription()
  with open(CHAR_TABLE) as fh:
    curGroup = ''
    for line in fh:
      line = line.rstrip('\n')
      if not line:
        continue
      if line.startswith('#'):
        curGroup = line.split(maxsplit=1)[1]
      else:
        parts = line.split('\t', maxsplit=1)
        if len(parts) == 1:
          parts.append(parts[0])
        (orig, transa) = parts
        transe = tr.from_hebrew(orig)
        origFromTrans[transa] = orig
        etcbcFromTrans[transa] = transe
        charGroups.setdefault(curGroup, set()).add(transa)
  print(f'{len(origFromTrans)} characters mapped')


def readBooks():
  with open(MAN_TABLE) as fh:
    for line in fh:
      (code, book) = line.rstrip().split('\t')
      bookFromCode[code] = book
  print(f'{len(bookFromCode)} manuscripts mapped')


def readData(limit=None):
  for src in SOURCES:
    sys.stdout.write(f'Reading {src:>6} ...')
    with open(f'{SOURCE_DIR}/dss_{src}.txt') as fh:
      prevX = None
      for (i, line) in enumerate(fh):
        if limit and i >= limit:
          break
        (prevX, result) = parseLine(src, i, line, prevX)
        data.setdefault(src, []).append(result)
    print(f'{len(data[src]):<6} lines')


lexDisRe = re.compile(r'(?:^[0-9]+$)|(?:[_-][0-9]+$)')


def checkBooks():
  booksFound = set()

  for (src, lines) in data.items():
    for fields in lines:
      book = fields['scroll']
      booksFound.add(book)

  report(f'{len(booksFound)} CODEX ACRONYMS in the data')
  for book in sorted(booksFound):
    report(f'\t{book}', only=True)


def checkChars():
  charsFound = collections.Counter()
  charsMapped = set()
  charsUnmapped = {}

  for src in data:
    for (i, fields) in enumerate(data[src]):
      word = fields[TRANS]
      lex = fields[LEX]
      lexBare = lexDisRe.sub('', lex)
      for c in word + lexBare:
        charsFound[c] += 1
        if c in ESCAPE_CHARS or c in origFromTrans:
          charsMapped.add(c)
        else:
          if c in charsUnmapped:
            if len(charsUnmapped[c]) < 3:
              charsUnmapped[c].append((src, i, fields))
          else:
            charsUnmapped[c] = [(src, i, fields)]

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
  report(f'MAPPED ({len(charsMapped)})', only=True)
  for c in sorted(charsMapped):
    if c in ESCAPE_CHARS:
      cRep = bunesc(c)
      orig = f'{cRep} (bracket)'
    else:
      cRep = c
      orig = origFromTrans[c]
    freq = charsFound[c]
    charRep = cRep if cRep == orig else f'{cRep} => {orig}'
    report(f'{charRep} occurs {freq:>6} x', only=True)


def checkBracketPair(bOrig, eOrig):
  limitErrors = 10
  limitContext = 5

  report(f'BRACKETS {bOrig} {eOrig} ...')

  (b, e) = (besc(bOrig), besc(eOrig))

  last = None
  errors = {}
  nOccs = collections.Counter()

  for (src, lines) in data.items():
    last = None
    for (i, fields) in enumerate(lines):
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

  for (src, lines) in data.items():
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
        for j in range(start, end):
          fields = lines[j]
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
  for (b, e) in BRACKETS:
    (errs, occs) = checkBracketPair(b, e)
    totalErrs += errs
    totalOccs += occs

  report(f'OVERALL IMBALANCES:  {totalErrs}')
  report(f'OVERALL OCCURRENCES: {totalOccs}')


def prepare():
  global logh
  logh = open(REPORT, 'w')

  if os.path.exists(OUT_DIR):
    rmtree(OUT_DIR)
  os.makedirs(LOG_DIR, exist_ok=True)
  if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
  TF = Fabric(locations=[OUT_DIR])
  return CV(TF)


def finalize():
  logh.close()


# SET UP CONVERSION

def getConverter():
  if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
  if os.path.exists(OUT_DIR):
    rmtree(OUT_DIR)
  TF = Fabric(locations=[OUT_DIR])
  return CV(TF)


def convert():
  prepare()
  readChars()
  readBooks()
  readData(limit=None)
  if checkSource:
    checkChars()
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
  # print('Parsing Abegg data files')
  return True


# TF LOADING (to test the generated TF)

def loadTf():
  TF = Fabric(locations=[OUT_DIR])
  allFeatures = TF.explore(silent=True, show=True)
  loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
  api = TF.load(loadableFeatures, silent=False)
  if api:
    print(f'max node = {api.F.otype.maxNode}')
    print(api.F.root.freqList()[0:20])


# MAIN

generateTf = len(sys.argv) == 1 or '-notf' not in sys.argv[1:]
print(generateTf)
checkSource = len(sys.argv) > 1 and '-check' in sys.argv[1:]

print(f'Abegg transcription to TF converter for {REPO}')
print(f'Abegg source version = {VERSION_SRC}')
print(f'TF  target version = {VERSION_TF}')
good = convert()

if generateTf and good:
  loadTf()
