class Compare(object):
  def __init__(self, sourceLines, wordsSrc, api, wordsTf):
    self.sourceLines = sourceLines
    self.wordsSrc = wordsSrc
    self.api = api
    self.wordsTf = wordsTf

  def showSrc(self, bib, n, around=2):
    sourceLines = self.sourceLines
    src = 'bib' if bib else 'nonbib'
    srcRep = 'B' if bib else 'N'
    sep = '\t' if bib else ' '
    firstN = max(n - around, 0)
    lastN = min(n + around + 1, len(sourceLines[src]))
    for i in range(firstN, lastN):
      line = sourceLines[src][i - 1].rstrip('\n')
      fields = line.split(sep)
      fieldsRep = '┃'.join(f'{f:<15}' for f in fields)
      prefix = '>>>' if i == n else '   '
      print(f'{prefix} {srcRep}{i}: {fieldsRep}')

  def showTf(self, bib, ln, around=2):
    sourceLines = self.sourceLines
    src = 'bib' if bib else 'nonbib'
    srcRep = 'B' if bib else 'N'
    F = self.api.F
    T = self.api.T
    cases = set()
    firstN = max(ln - around, 0)
    lastN = min(ln + around + 1, len(sourceLines[src]))
    for n in range(firstN, lastN):
      cases = {w for w in (F.srcLn.s(n) or []) if bool(F.biblical.v(w)) == bib}
      prefix = ('>>>' if n == ln else '   ') + f' {srcRep}{n}: '
      if not cases:
        print(f'{prefix}no nodes')
      for case in sorted(cases):
        passage = '{} {}:{}'.format(*T.sectionFromNode(case))
        if bib:
          passage2 = f'{F.book.v(case)} {F.chapter.v(case)}:{F.verse.v(case)}'
          passage = f'{passage2:<15}┃{passage:<15}'
        print(
            f'{prefix}'
            f'{passage:<15}┃'
            f'{F.fullo.v(case):<15}┃'
            f'{F.lang.v(case) or "":<1}┃'
            f'{F.lexo.v(case) or "":<15}┃'
            f'{F.morpho.v(case) or ""}┃'
            f'{case}┃'
        )

  def showDiff(self):
    (i, a, b) = firstDiff(self.wordsTf, self.wordsSrc)
    if i is None:
      print('EQUAL')
      return
    minimum = min((a[1], b[1]))
    diff = abs(a[1] - b[1])
    bibA = a[0]
    bibB = b[0]
    print(f'item {i}:')
    showItem(a, 'TF ')
    showItem(b, 'SRC')
    around = max(1, min(diff, 10))
    print('TF:')
    self.showTf(bibA, minimum, around=around)
    print('SRC:')
    self.showSrc(bibB, minimum, around=around)


def showItem(a, prefix):
  (src, ln, *fields) = a
  srcRep = 'B' if src else 'N'
  fieldsRep = '┃'.join(f'{field:<15}' for field in fields)
  print(f'{prefix} {srcRep}{ln} {fieldsRep}')


def firstDiff(lista, listb):
  na = len(lista)
  nb = len(listb)
  for (i, a) in enumerate(lista):
    if i >= nb:
      return (i, a, None)
    b = listb[i]
    if a != b:
      return (i, a, b)
  if na < nb:
    return (na, None, listb[na])
  return (None, None, None)


def tests():
  test1a = [1, 2, 3]
  test1b = [1, 2, 3]
  test2b = [1, 2, 3, 4]
  test3b = [1, 2]
  test4b = [1, 2, 4]
  test5b = [1, 4, 3]

  good = True

  for (lista, listb, answer) in (
      (test1a, test1b, (None, None, None)),
      (test1a, test2b, (3, None, 4)),
      (test1a, test3b, (2, 3, None)),
      (test1a, test4b, (2, 3, 4)),
      (test1a, test5b, (1, 2, 4)),
  ):
    testAnswer = firstDiff(lista, listb)
    status = testAnswer == answer
    statusRep = 'OK' if status else f'XX expected {answer}'
    print(f'firstDiff of {lista} and {listb} is {testAnswer} {statusRep}')
    if not status:
      good = False

  return good


if __name__ == 'main':
  tests()
