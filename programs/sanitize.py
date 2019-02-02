import os
from shutil import rmtree

BASE = os.path.expanduser('~/local/dss')
SOURCE_BASE = f'{BASE}/source'
SAN_BASE = f'{BASE}/sanitized'

SRC1 = 'dss_morph.txt'
SRC2 = 'dssbib_morph.txt'

if os.path.exists(SAN_BASE):
  rmtree(SAN_BASE)
os.makedirs(SAN_BASE, exist_ok=True)


def sanitize(src):
  infile = f'{SOURCE_BASE}/{src}'
  outfile = f'{SAN_BASE}/{src}'

  with open(infile, encoding='mac_roman') as f:
    text = f.read()

  text = text.replace('\r', '\n')

  with open(outfile, 'w') as f:
    f.write(text)


for src in (SRC1, SRC2):
  sanitize(src)
