import os
import collections

BASE = os.path.expanduser('~/github')
ORG = 'etcbc'
REPO = 'dss'
VERSION = '0.1'

REPO_DIR = f'{BASE}/{ORG}/{REPO}'
META_DIR = f'{REPO_DIR}/sources/meta'

CHAR_TABLE = f'{META_DIR}/chars.txt'
MAN_TABLE = f'{META_DIR}/mans.txt'

LOCAL = os.path.expanduser('~/local')
DATA_DIR = f'{LOCAL}/{REPO}/sanitized'

SOURCES = '''
  bib
  nonbib
'''.strip().split()

COLUMNS_B = '''
    bookAcro chapter:verse
    manRef part:line
    trans
    lex@morph
    num.subnum
'''
COLUM_SEP_B = '\t'

COLUMNS_NB = '''
    manName
    column:line
    line,word
    trans
    lex@morph
'''


def splitLineBib(line):
  parts = line.split('\t')


def getSourceLine():
  for src in SOURCES:
    with open(f'{DATA_DIR}/dss_{src}.txt') as fh:
      for (i, line) in enumerate(fh):
        if line.startswith('>'):
          continue
        yield (src, i + 1, line.rstrip())


origFromTrans = {}
bookFromCode = {}


def readChars():
  with open(CHAR_TABLE) as fh:
    for line in fh:
      (orig, trans) = line.rstrip().split('\t')
      origFromTrans[trans] = orig
  print(f'{len(origFromTrans)} characters mapped')


def readBooks():
  with open(MAN_TABLE) as fh:
    for line in fh:
      (code, book) = line.rstrip().split('\t')
      bookFromCode[code] = book
  print(f'{len(bookFromCode)} mans mapped')


def readData():
  srcLines = collections.Counter()
  for (src, i, line) in getSourceLine():
    srcLines[src] += 1
  for (src, amount) in srcLines.items():
    print(f'{src:<15}: {amount:>5} lines')


def convert():
  readChars()
  readBooks()
  readData()


convert()
