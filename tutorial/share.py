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
# # Sharing data features
#
# ## Explore additional data
#
# Once you analyse a corpus, it is likely that you produce data that others can reuse.
# Maybe you have defined a set of proper name occurrences, or special numerals, or you have computed part-of-speech assignments.
#
# It is possible to turn these insights into *new features*, i.e. new `.tf` files with values assigned to specific nodes.
#
# ## Make your own data
#
# New data is a product of your own methods and computations in the first place.
# But how do you turn that data into new TF features?
# It turns out that the last step is not that difficult.
#
# If you can shape your data as a mapping (dictionary) from node numbers (integers) to values
# (strings or integers), then TF can turn that data into a feature file for you with one command.
#
# ## Share your new data
# You can then easily share your new features on GitHub, so that your colleagues everywhere
# can try it out for themselves.
#
# You can add such data on the fly, by passing a `mod={org}/{repo}/{path}` parameter,
# or a bunch of them separated by commas.
#
# If the data is there, it will be auto-downloaded and stored on your machine.
#
# Let's do it.

# %load_ext autoreload
# %autoreload 2

import os
from tf.app import use


# A = use('dss', hoist=globals())
A = use("dss:clone", checkout="clone", hoist=globals())


# # Making data
#
# We illustrate the data creation part by creating a new feature, `cert`.
# The idea is that we mark every consonant sign voor certainty.
#
# A certain consonant gets `cert=100`.
#
# If the consonant has the uncertain feature `unc`, then 10 times its value is subtracted from 100.
#
# If the consonant has the feature `rec`, it loses 45 points.
#
# Ancient removal `rem2` leads to minus 20, modern removal `rem` to minus 40.
#
# Ancient correction `cor2` leads to minus 12, modern correction `cor` to minus 18.
#
# Alternate marking `alt` leads to minus 25.
#
# The minimum is `1`.
#
# We extend the `cert` measure to words, fragments and scrolls by averaging over signs that
# have received a `cert` measure.


def measure(s):
    c = 100
    d = F.unc.v(s)
    if d:
        c -= 10 * d
    d = F.rec.v(s)
    if d:
        c -= 45
    d = F.rem.v(s)
    if d == 1:
        c -= 40
    elif d == 2:
        c -= 20
    d = F.cor.v(s)
    if d == 2 or d == 3:
        c -= 12
    elif d == 1:
        c -= 18
    d = F.alt.v(s)
    if d:
        c -= 25
    if c < 1:
        c = 1
    return c


# +
CONS = "cons"
cert = {}

A.indent(reset=True)

for sc in F.otype.s("scroll"):
    fN = 0
    fSum = 0
    for f in L.d(sc, otype="fragment"):
        lN = 0
        lSum = 0
        for ln in L.d(f, otype="line"):
            wN = 0
            wSum = 0
            for w in L.d(ln, otype="word"):
                sN = 0
                sSum = 0
                for s in L.d(w, otype="sign"):
                    if F.type.v(s) != CONS:
                        continue
                    sCert = measure(s)
                    cert[s] = sCert
                    sN += 1
                    sSum += sCert
                if sN:
                    wCert = int(round(sSum / sN))
                    cert[w] = wCert
                    wN += 1
                    wSum += wCert
            if wN:
                lCert = int(round(wSum / wN))
                cert[ln] = lCert
                lN += 1
                lSum += lCert
        if lN:
            fCert = int(round(lSum / lN))
            cert[f] = fCert
            fN += 1
            fSum += fCert
    if fN:
        scCert = int(round(fSum / fN))
        cert[sc] = scCert

A.info(f"{len(cert)} certainties determined")
# -

# # Saving data
#
# The [documentation](https://annotation.github.io/text-fabric/tf/core/fabric.html#tf.core.fabric.FabricCore.save) explains how to save this data into a text-fabric
# data file.
#
# We choose a location where to save it, the `exercises` folder in the `dss` repository in the `dss` organization.
#
# In order to do this, we restart the TF api, but now with the desired output location in the `locations` parameter.

GITHUB = os.path.expanduser("~/github")
ORG = "etcbc"
REPO = "dss"
PATH = "exercises"
VERSION = A.version

# Note the version: we have built the version against a specific version of the data:

A.version

# Later on, we pass this version on, so that users of our data will get the shared data in exactly the same version as their core data.

# We have to specify a bit of metadata for this feature:

metaData = {
    "cert": dict(
        valueType="int",
        description="measure of certainty of material, between 1 and 100 (most certain)",
        creator="Dirk Roorda",
    ),
}

# Now we can give the save command:

TF.save(
    nodeFeatures=dict(cert=cert),
    metaData=metaData,
    location=f"{GITHUB}/{ORG}/{REPO}/{PATH}/tf",
    module=VERSION,
)

# # Sharing data
#
# How to share your own data is explained in the
# [documentation](https://annotation.github.io/text-fabric/tf/about/datasharing.html).
#
# Here we show it step by step for the `cert` feature.
#
# If you commit your changes to the exercises repo, and have done a `git push origin master`,
# you already have shared your data!
#
# If you want to make a stable release, so that you can keep developing, while your users fall back
# on the stable data, you can make a new release.
#
# Go to the GitHub website for that, go to your repo, and click *Releases* and follow the nudges.
#
# If you want to make it even smoother for your users, you can zip the data and attach it as a binary to the release just created.
#
# We need to zip the data in exactly the right directory structure. Text-Fabric can do that for us:

# + language="sh"
#
# text-fabric-zip etcbc/dss/exercises/tf
# -

# All versions have been zipped, but it works OK if you only attach the newest version to the newest release.
#
# If a user asks for an older version in this release, the system can still find it.

# # Use the data
#
# We can use the data by calling it up when we say `use('dss', ...)`.
#
# Here is how:
#
# (use the line without `clone` if the data is really published,
# use the line with `clone` if you want to test your local copy of the feature).

# A = use('dss', hoist=globals(), mod='etcbc/dss/exercises/tf')
A = use(
    "dss:clone", checkout="clone", hoist=globals(), mod="etcbc/dss/exercises/tf:clone"
)

# Above you see a new section in the feature list: **etcbc/dss/exercises/tf** with our foreign feature in it: `cert`.
#
# Now, suppose did not know much about this feature, then we would like to do a few basic checks:

F.cert.freqList()

# Which nodes have the lowest uncertainty?

{F.otype.v(n) for n in N.walk() if F.cert.v(n) and F.cert.v(n) < 10}

# Only signs are this uncertain.
#
# Let's look for pretty uncertain fragments:

results = A.search(
    """
fragment cert<50
"""
)

results = A.search(
    """
fragment cert<60
"""
)

A.table(results, start=1, end=20)

# Same for scrolls:

results = A.search(
    """
scroll cert<50
"""
)

results = A.search(
    """
scroll cert<60
"""
)

A.show(results)

# Lines with certainty of 50:

results = A.search(
    """
line cert<57
"""
)

A.show(results, start=100, end=102)

# With highlights and drilled down to sign level:

# +
highlights = {}

for s in F.otype.s("sign"):
    if not F.cert.v(s):
        continue
    color = "lightsalmon" if F.cert.v(s) < 56 else "mediumaquamarine"
    highlights[s] = color
# -

A.show(
    results,
    start=100,
    end=102,
    withNodes=True,
    condensed=True,
    highlights=highlights,
    baseTypes="sign",
)

# # All together!
#
# If more researchers have shared data modules, you can draw them all in.
#
# Then you can design queries that use features from all these different sources.
#
# In that way, you build your own research on top of the work of others.

# Hover over the features to see where they come from, and you'll see they come from your local github repo.

# ---
#
# All chapters:
#
# * **[start](start.ipynb)** become an expert in creating pretty displays of your text structures
# * **[display](display.ipynb)** become an expert in creating pretty displays of your text structures
# * **[search](search.ipynb)** turbo charge your hand-coding with search templates
# * **[exportExcel](exportExcel.ipynb)** make tailor-made spreadsheets out of your results
# * **share** draw in other people's data and let them use yours
# * **[similarLines](similarLines.ipynb)** spot the similarities between lines
#
# ---
#
# See the [cookbook](cookbook) for recipes for small, concrete tasks.
#
# CC-BY Dirk Roorda
