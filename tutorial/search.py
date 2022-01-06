# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# <img align="right" src="images/tf.png" width="128"/>
# <img align="right" src="images/logo.png" width="128"/>
# <img align="right" src="images/etcbc.png" width="128"/>
# <img align="right" src="images/dans.png" width="128"/>
#
# ---
#
# To get started: consult [start](start.ipynb)
#
# ---
#
# # Search Introduction
#
# *Search* in Text-Fabric is a template based way of looking for structural patterns in your dataset.
#
# It is inspired by the idea of
# [topographic query](http://books.google.nl/books?id=9ggOBRz1dO4C).
#
# Within Text-Fabric we have the unique possibility to combine the ease of formulating search templates for
# complicated patterns with the power of programmatically processing the results.
#
# This notebook will show you how to get up and running.
#
# ## Alternative for hand-coding
#
# Search is a powerful feature for a wide range of purposes.
#
# Quite a bit of the implementation work has been dedicated to optimize performance.
# Yet I do not pretend to have found optimal strategies for all
# possible search templates.
# Some search tasks may turn out to be somewhat costly or even very costly.
#
# That being said, I think search might turn out helpful in many cases,
# especially by reducing the amount of hand-coding needed to work with special subsets of your data.
#
# ## Easy command
#
# Search is as simple as saying (just an example)
#
# ```python
# results = A.search(template)
# A.show(results)
# ```
#
# See all ins and outs in the
# [search template docs](https://annotation.github.io/text-fabric/tf/about/searchusage.html).

# %load_ext autoreload
# %autoreload 2

from tf.app import use

A = use("dss:clone", checkout="clone", hoist=globals())
# A = use('dss', hoist=globals())

# # Basic search command
#
# We start with the most simple form of issuing a query.
#
# Let's look for the verbs in the `hitpael` with an uncertain character in it.
#
# All work involved in searching takes place under the hood.

query = """
word vs=hitpael
  sign unc
"""
results = A.search(query)
A.table(results, end=10)

# We have multiple uncertain signs per word,
# and for each sign we see the whole word repeated.
#
# We can condense our results to words:

A.table(results, end=10, condensed=True, condenseType="word")

# We can show them in rich layout as well:

A.table(results, end=10, condensed=True, condenseType="word", fmt="layout-orig-full")

# Note that we can choose start and/or end points in the results list.

A.table(
    results,
    start=100,
    end=110,
    condensed=True,
    condenseType="word",
    fmt="layout-orig-full",
)

# We can show the results more fully with `show()`.

A.show(results, fmt="layout-orig-full", start=1, end=3)

# or even more fully by showing the signs as well:

A.show(results, fmt="layout-orig-full", start=1, end=1, baseTypes="sign")

# # Condense results
#
# There are two fundamentally different ways of presenting the results: condensed and uncondensed.
#
# In **uncondensed** view, all results are listed individually.
# You can keep track of which parts belong to which results.
# The display can become unwieldy.
#
# This is the default view, because it is the straightest, most logical, answer to your query.
#
# In **condensed** view all nodes of all results are grouped in containers first (e.g. lines), and then presented
# container by container.
# You loose the information of what parts belong to what result.
#
# As an example of the difference, we look for all proper nouns, but only in lines where there is also
# a word marked with paleohebrew script.

query = """
line
  word sp=subs cl=prp
  word script=paleohebrew
% NB: the order of both words is not specified
% NB: both 'word' items may be instantiated by the same word
"""

# Note that you can have comments in a search template. Comment lines start with a `%`.

results = A.search(query)
A.table(results, start=22, end=25, fmt="layout-orig-full")

# Note result 23: here both words in the query are instantiated by the same word, which satisfies both criteria!

A.table(results, start=30, end=40, fmt="layout-orig-full")

# Note in passing that *numerals* are also marked in as paleohebrew.

# Note results 32-39, all in the same line. Let's switch to condensed view.
# Because results are counted differently now, we narrow down our search as well.

query = """
line scroll=4Q318 fragment=4 line=9
  word sp=subs cl=prp
  word script=paleohebrew
"""
results = A.search(query)
A.table(results, fmt="layout-orig-full", condensed=True)

# Let's expand the results display, first uncondensed, which takes a lot of space, so we show only two results:

A.show(results, end=2, withNodes=True, fmt="layout-orig-full")

# As you see, the results are listed per result tuple, even if they occur all in the same line.
# This way you can keep track of what exactly belongs to each result.
#
# Now in condensed mode, and let's forget about the rich layout for a while:

A.show(results, condensed=True)

# This line has 8 results, and all of them are highlighted in the same line display.
#
# We can modify the container in which we see our results.
#
# By default, it is `line`, but we can make it `fragment` as well:

A.show(results, condensed=True, condenseType="fragment")

# We now see the the displays of the whole fragment, with the line with the proper names in it highlighted and the proper names
# themselves highlighted as well.

# # Custom highlighting
#
# Let us make a new search where we look for different things in the same line.

query = """
line
  word sp=verb
  word sp=subs cl=prp
    sign cor
"""

results = A.search(query)
A.table(results, end=10, fmt="layout-orig-full", skipCols="1")

# We can apply different highlight colors to different parts of the result.
#
# The line is member 1.
# the words are members 2 and 3,
# and the sign is member 4.
#
# We do not give a colour to the line, the verb will have thedefault color,
# the proper name cyan, and the sign magenta.
#
# **NB:** You can choose your colors from the
# [CSS specification](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value).

# +
colorMap = {2: "", 3: "cyan", 4: "magenta"}

A.table(results, end=10, fmt="layout-orig-full", colorMap=colorMap)
# -

A.show(results, end=3, fmt="layout-orig-full", colorMap=colorMap)

# Color mapping works best for uncondensed results. If you condense results, some nodes may occupy
# different positions in different results. It is unpredictable which color will be used
# for such nodes:

# # Constraining order
# You can stipulate an order on the things in your template.
# You only have to put a relational operator between them.
# Say we want only lines where a proper noun with an ancient correction precedes a verb

query = """
line
  word sp=subs cl=prp
    sign cor
  < word sp=verb
"""

results = A.search(query)
A.table(results, end=10, fmt="layout-orig-full")

# We can also require the things to be adjacent.

query = """
line
  word sp=subs cl=prp
    sign cor
  <: word sp=verb
"""

results = A.search(query)
colorMap = {2: "cyan", 3: "magenta", 4: ""}
A.table(results, end=10, colorMap=colorMap, fmt="layout-orig-full")
A.show(results, end=3, colorMap=colorMap, fmt="layout-orig-full")

# Finally, we want the proper name start near the start of the line, i.e. nut further away than three signs.

query = """
line
  =3: word sp=subs cl=prp
    sign cor
  <: word sp=verb
"""

results = A.search(query)
colorMap = {2: "cyan", 3: "magenta", 4: ""}
A.table(results, end=10, colorMap=colorMap, fmt="layout-orig-full")
A.show(results, end=3, colorMap=colorMap, fmt="layout-orig-full")

# # Custom feature display
#
# We would like to see the original Abegg code with the marks and brackets.
# They are in the feature `fullo` on words.
#
# The way to do that, is to perform a `A.prettySetup(features)` first.
#
# We concentrate on one specific result.

A.displaySetup(extraFeatures="fullo")

A.show(results, end=1, colorMap=colorMap, fmt="layout-orig-full")

# The features without meaningful values have been left out. We can also change that by passing a set of values
# we think are not meaningful. The default set is
#
# ```python
# {None, 'NA', 'none', 'unknown'}
# ```

A.displaySetup(noneValues=set())
A.show(results, end=1, colorMap=colorMap, fmt="layout-orig-full")

# This makes clear that it is convenient to keep `None` in the `noneValues`:

A.displaySetup(noneValues={None})
A.show(results, end=1, colorMap=colorMap, fmt="layout-orig-full")

# We can even choose to suppress other values, e.g. the value 1.
#
# That will remove all the features such as `rec`.

A.displaySetup(noneValues={None, "NA", "unknown", 1})
A.show(results, end=1, colorMap=colorMap, fmt="layout-orig-full")

# In the rest of the notebook we stick to our normal setup, so we reset the extra features.

A.displayReset()
A.show(results, end=1, colorMap=colorMap, fmt="layout-orig-full")

# # Features from queries
#
# In earlier displays we saw the *types* of signs, because the query mentioned it.
#
# Suppose we want to display the type also here, then we can modify the query by mentioning the feature `type`.
#
# But we do not want to impose extra limitations, so we say `type*`, meaning: no conditions on type whatsoever.

query = """
line
  =3: word sp=subs cl=prp
    sign cor type*
  <: word sp=verb
"""

results = A.search(query)
A.show(results, end=1, colorMap=colorMap, fmt="layout-orig-full")

# # Show your own tuples
#
# So far we have `show()`n the results of searches.
# But you can also construct your own tuples and show them.
#
# Whereas you can use search to get a pretty good approximation of what you want, most of the times
# you do not arrive precisely at your destination.
#
# Here is an example where we use search to come close, and then work our way to produce the end result.
#
# ## More reconstructed/uncertain than certain
#
# We look for lines that have more reconstructed/uncertain consonants than certain consonants.
#
# In our search templates we cannot formulate that a feature has different values on two nodes in the template.
# We could spell out all possible combinations of values and make a search template for each of them,
# but that is needlessly complex.
#
# Let's first use search to find all lines containing reconstructed/uncertain/certain consonants.

query = """
line
/with/
  sign type=cons rec
/or/
  sign type=cons unc
/-/
/with/
  sign type=cons rec# unc#
/-/
"""
results = A.search(query)

# That is a lot, how does that compare to the total number of lines?

queryl = """
line
"""
resultsl = A.search(queryl)

# or, by hand-coding:

len(F.otype.s("line"))

# Now the real hand-coding begins. We are going to extract the tuples we want.
# How are they structured?

for (i, tup) in enumerate(results[0:5]):
    print(f"tuple {i}")
    for (j, n) in enumerate(tup):
        print(f"\tmember {j} = {F.otype.v(n)} {n}")


# Very simple indeed!

# Now we have all lines with hypothetical and certain consonants.
#
# For each line we make a set with its hypothetical consonants and one with its certain consonants.
#
# We filter in order to retain the lines with more hypothetical than certain consonants.
# We put all hypothetical consonants in one big set and all certain consonants in one big set.

# +
answer = []
hypo = set()
cert = set()

for (line,) in results:
    signs = L.d(line, otype="sign")
    myHypo = set()
    myCert = set()
    for s in signs:
        if F.type.v(s) != "cons":
            continue
        if F.rec.v(s) or F.unc.v(s):
            myHypo.add(s)
        else:
            myCert.add(s)
    if len(myHypo) > len(myCert):
        answer.append((line, *myHypo, *myCert))
        hypo |= myHypo
        cert |= myCert
len(answer)
# -

# One third of the lines is more than half uncertain!

answer[0]

# We are going to make a dictionary of highligts: one color for the hypothetical signs and one for the certain.

highlights = {}
colorH = "lightsalmon"
colorC = "mediumaquamarine"
for s in hypo:
    highlights[s] = colorH
for s in cert:
    highlights[s] = colorC

# And now we can show them (note that we descend from the word level to the sign level by passing `baseType="sign"`:

A.show(answer, start=1, end=5, highlights=highlights, baseTypes="sign")

# As you see, you have total control.

# ---
#
# All chapters:
#
# * **[start](start.ipynb)** become an expert in creating pretty displays of your text structures
# * **[display](display.ipynb)** become an expert in creating pretty displays of your text structures
# * **search** turbo charge your hand-coding with search templates
# * **[exportExcel](exportExcel.ipynb)** make tailor-made spreadsheets out of your results
# * **[share](share.ipynb)** draw in other people's data and let them use yours
# * **[similarLines](similarLines.ipynb)** spot the similarities between lines
#
# ---
#
# See the [cookbook](cookbook) for recipes for small, concrete tasks.
#
# CC-BY Dirk Roorda
