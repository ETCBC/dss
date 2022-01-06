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
# # Display
#
# We show the ins and outs of displaying Dead Sea Scroll material.

# %load_ext autoreload
# %autoreload 2

from tf.app import use

# If you want to use a version of the DSS ahead of a release, use the incantation with `hot` in it.
# That will take time, not only for the download itself, but also for the one-time preprocessing of the data.
#
# If you are content with the latest stable release, use the line without the `hot`.
#
# I have the data locally in my github clone of the DSS, so I use the variant with `clone`.
#
# If you do a `git clone https://github.com/ETCBC/dss` from your directory
# `~/github/etcbc` you can use this as well.

# A = use('dss', hoist=globals())
# A = use('dss:hot', checkout='hot', hoist=globals())
A = use("dss:clone", checkout="clone", hoist=globals())

# We pick an example fragment with which we illustrate many ways to represent the DSS material.

examplefragment = ("1Q1", "f1")
f = T.nodeFromSection(examplefragment)
lines = L.d(f, otype="line")
words = L.d(f, otype="word")
signs = L.d(f, otype="sign")

# # Text formats
#
# The TF API supports *text formats*. Text formats make selections and apply templates and styles based
# on the analysed features of the text. For example: a text-format may ignore flags or clusters, or
# format numerals in special ways.
#
# Text formats are not baked into TF, but they are defined in the feature `otext` of the corpus.
#
# Moreover, for this corpus a TF app has been build that defines additional text-formats.
#
# Whereas the formats defined in `otext` are strictly plain text formats, the formats
# defined in the app are able to use typographic styles to shape the text, such as bold, italic, colors, etc.
#
# Here is the list of all formats.

T.formats

# ## Plain text formats
#
# The formats whose names start with `text-` are the plain text formats.
#
# ### `text-orig-full`
#
# This is the plain Hebrew text of the transcriptions, without text-critical signs and brackets.
#
# This is the default format. We do not have to specify it.

for ln in lines:
    A.plain(ln)

# The `plain()` function focuses on the *contents*, and instead of the line number, it gives a full specification
# of the location,
# linked to the [Leon Levy digital library](https://www.deadseascrolls.org.il/home).
#
# But we can omit the locations:

for ln in lines:
    A.plain(ln, withPassage=False)

# Now the lines themselves are linked to the Leon Levy library.

# ### `text-source-extra`
#
# This format is really close to the Abegg transcription. It contains all original information.

for ln in lines:
    A.plain(ln, fmt="text-source-extra")

# ### `text-trans-extra`
#
# This format gives the ETCBC transcription:

for ln in lines:
    A.plain(ln, fmt="text-trans-extra")

# ## Styled text formats
#
# The formats whose names start with `layout-` are the styled text formats.
#
# ### `layout-orig-full`
#
# This format looks like `text-orig-full`, but now we re-introduce the flags and clusters by specific
# layout devices.

for ln in lines:
    A.plain(ln, fmt="layout-orig-full")

# The teal font color indicates that the material is a *reconstruction*.
# In the source, it is between `[ ]` brackets.
#
# See below for a detailed list of examples.

# ### `layout-trans-full`
#
# The same layout, but now using ETCBC transcriptions.

for ln in lines:
    A.plain(ln, fmt="layout-trans-full")

# ### `layout-source-full`
#
# The same layout, but now using Abegg's transcriptions.

for ln in lines:
    A.plain(ln, fmt="layout-source-full")

# Or, if you want to see all the marks:

# # Pretty
#
# The ultimate of graphical display is by means of the `pretty()` function.
#
# This display is less useful for reading, but instead optimized for showing all information that you might
# wish for.
#
# It shows a base representation according to a text format of your choice
# (here we choose `layout-orig-full`).

A.pretty(F.otype.s("word")[100], extraFeatures=["fulle"])

A.pretty(F.otype.s("word")[100], extraFeatures=["fulle"], standardFeatures=True)

# You can enrich the display with the values of a standard set of features.

A.pretty(lines[0], fmt="layout-orig-full", lineNumbers=False)

# Normally, pretty displays dig to the word level and not further. But if you want to dig to the sign level, you can do that:

A.pretty(
    lines[0],
    fmt="layout-orig-full",
    withNodes=False,
    lineNumbers=False,
    baseTypes="sign",
)

# Later on, in the [search](search.ipynb) tutorial we see that `pretty()` can also display other features,
# even features that you or other people have created and added later.
#
# Here we call for the feature `fullo`, defined word words, not signs, which shows the original source code for the word in question
# including the bracketing characters.
#
# Consult the
# [feature documentation](https://github.com/etcbc/dss/blob/master/docs//transcription.md)
# to see what information is stored in all the features.
#
# We show it with node numbers, but you could leave them out in an obvious way.

A.pretty(lines[0], extraFeatures="fullo", fmt="layout-orig-full", withNodes=True)

# We can even do it for a whole fragment:

A.pretty(f, extraFeatures="fullo", fmt="layout-orig-rich", withNodes=True)

# We do not see much, because the default condense type is `line`, and a `fragment` is bigger than that.
# Objects bigger than de condense type will be abbreviated to a label that indicates their identity,
# not their contents.
#
# But we can override this by adding `full=True`.
#
# See also the documentation on [`pretty`](https://annotation.github.io/text-fabric/tf/advanced/display.html#tf.advanced.display.pretty).

A.pretty(f, extraFeatures="full", fmt="layout-orig-full", withNodes=False, full=True)

# # Layout formats: the details
#
# We give detailed examples of how the material is styled in the `layout-` formats.
#
# We show the representation of all kinds of signs and also what the influence of
# clustering and flags are.
#
# Here are the design principles:
#
# * when the color changes as per one the cases below, the font will be bolded, except
#   for reconstructions
# * uncertain text `? # (# #) #? ##`
#   cause the signs in their scope to be in italics, grey and blurry,
#   increasingly so as the degree of uncertainty goes up from 1 to 4
# * alternate text `( )` is overlined
# * vacats `(- -)` have a red border
# * reconstructions `[ ]` are in color teal and in a smaller font
# * removed text is striked through, if by an ancient editor `{{ }}` it is set in color maroon
#   if by a modern editor, the color is red
# * corrected text is overlined, if by an ancient editor `<< >>` the color is navy,
#   if supralinear (also ancient editor) `^ ^` the color is also navy
#   and the text is superscripted, if by a modern editor `< >` the color is dodgerblue
# * interlinear text is subscripted or extra subscripted (depending on the interlinear value 1 or 2)
# * non-Hebrew text (Aramaic or Greek) is underlined
# * text that is marked by script (paleo Hebrew or Greek Capital) gets a straight border around it

# Just a quick overview of the cluster types:

clusterFreqs = F.type.freqList(nodeTypes={"cluster"})
clusterFreqs

clusterTypes = [x[0] for x in clusterFreqs]
clusterNodes = F.otype.s("cluster")
clusterByType = {
    typ: [n for n in clusterNodes if F.type.v(n) == typ] for typ in clusterTypes
}
clusterExamples = {typ: clusterByType[typ][0:2] for typ in clusterTypes}


# We have now example nodes for each type of cluster.
#
# Likewise, we want examples of the uncertain flag, the languages, the scripts, the interlinears.
#
# We write a generic function to provide example nodes for each value that a `feature` of interest can have.
# Of all those nodes, we select a sub list, from `start` to `end`.


def compileExamples(feature, start, end):
    print(f'Examples for feature "{feature}"')
    fObj = Fs(feature)
    f = fObj.v
    freqs = fObj.freqList()
    for (c, amount) in freqs:
        print(f"\t{c} occurs {amount:>6} x")
    values = [x[0] for x in freqs]
    nodes = [n for n in F.otype.s("sign") if f(n)]
    nodesByValue = {v: [n for n in nodes if f(n) == v] for v in values}
    print(f'\t{len(nodes)} nodes have the feature "{feature}"')
    examples = {
        f'{feature}{"" if v == 0 else v}': nodesByValue[v][start - 1 : end]
        for v in values
    }
    for (v, ns) in examples.items():
        print(f'\t{v:<10} {", ".join(str(n) for n in ns)}')
    return examples


# We collect the examples in a dictionary `allExamples`, keyed by a string that combines the feature name with
# a value.
#
# **For the technically inclined:**
# In the TF-app for DSS, we use that key as a CSS class name to trigger special formatting.
#
# The following link takes you directly to where that happens.
# [display.css](https://github.com/annotation/app-dss/blob/d430bfe1601ff961bbed425e1c6a7a3934a81ba8/code/static/display.css#L209-L280).

# +
allExamples = {}
allExamples.update(clusterExamples)

for (feature, start, end) in (
    ("unc", 1, 2),
    ("lang", 2, 10),
    ("script", 2, 10),
    ("intl", 1, 2),
):
    allExamples.update(compileExamples(feature, start, end))
# -

allExamples

for (typ, examples) in sorted(allExamples.items()):
    A.dm("---\n")
    print(f'Examples of "{typ}"')
    nodes = set()
    for n in examples:
        isCluster = F.otype.v(n) == "cluster"
        ref = L.d(n, otype="sign")[0] if isCluster else n
        w = L.u(ref, otype="word")
        if w:
            nodes.add(w[0])
        else:
            nodes.add(n)
    for n in nodes:
        A.pretty(n, fmt="layout-orig-full", withNodes=True)

# ---
#
# All chapters:
#
# * **[start](start.ipynb)** introduction to computing with your corpus
# * **display** become an expert in creating pretty displays of your text structures
# * **[search](search.ipynb)** turbo charge your hand-coding with search templates
# * **[exportExcel](exportExcel.ipynb)** make tailor-made spreadsheets out of your results
# * **[share](share.ipynb)** draw in other people's data and let them use yours
# * **[similarLines](similarLines.ipynb)** spot the similarities between lines
#
# ---
#
# See the [cookbook](cookbook) for recipes for small, concrete tasks.
#
# CC-BY Dirk Roorda
