# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
# %load_ext autoreload
# %autoreload 2

# %%
import os
import pickle
import gzip

from tf.app import use
from tf.fabric import Fabric


# %%
ghBase = os.path.expanduser("~/github")
org = "etcbc"
repo = "dss"
subdir = "parallels"
mainpath = f"{org}/{repo}/tf"
path = f"{org}/{repo}/{subdir}/tf"
location = f"{ghBase}/{path}"
mainlocation = f"{ghBase}/{mainpath}"
version = "0.6"
module = version
tempdir = f"{ghBase}/{org}/{repo}/_temp"

# %%
TF = Fabric(locations=mainlocation, modules=module)

# %%
api = TF.load("lex type")
docs = api.makeAvailableIn(globals())

# %% [markdown]
# # Parallels
#
# We make edges between similar lines.
#
# When are lines similar?
#
# If a certain distance metric is above a certain threshold.
#
# We choose this metric:
#
# * we reduce a line to the set of lexemes in it.
# * the similarity between two lines is the length of the intersection divided by the length of the union of their sets times 100.

# %% [markdown]
# # Preparation
#
# We pre-compute all sets for lines.
#
# But because not all lines are filled with definite material, we exclude lines with 5 or less consonants.

# %%
CONS = "cons"

valid = set()

allLines = F.otype.s("line")

TF.indent(reset=True)
for ln in F.otype.s("line"):
    if ln in valid:
        continue
    if sum(1 for s in L.d(ln, otype="sign") if F.type.v(s) == CONS) >= 5:
        valid.add(ln)

TF.info(f"{len(valid)} contentful lines out of {len(allLines)}")


# %%
def makeSet(ln):
    lineSet = set()
    for s in L.d(ln, otype="word"):
        r = F.lex.v(s)
        if r:
            lineSet.add(r)
    return lineSet


# %%
lines = {}

TF.indent(reset=True)
for ln in valid:
    lineSet = makeSet(ln)
    if lineSet:
        lines[ln] = lineSet

nLines = len(lines)
TF.info(f"{nLines} lines")

# %% [markdown]
# # Measure


# %%
def sim(lSet, mSet):
    return int(round(100 * len(lSet & mSet) / len(lSet | mSet)))


# %% [markdown]
# # Compute all similarities
#
# We are going to perform more than half a billion of comparisons, each of which is more than an elemetary operation.
#
# Let's measure time.

# %%
THRESHOLD = 60


def computeSim(limit=None):
    similarity = {}

    lineNodes = sorted(lines.keys())
    nLines = len(lineNodes)

    nComparisons = nLines * (nLines - 1) // 2

    print(f"{nComparisons} comparisons to make")
    chunkSize = nComparisons // 1000

    co = 0
    b = 0
    si = 0
    p = 0

    TF.indent(reset=True)

    stop = False
    for i in range(nLines):
        nodeI = lineNodes[i]
        lineI = lines[nodeI]
        for j in range(i + 1, nLines):
            nodeJ = lineNodes[j]
            lineJ = lines[nodeJ]
            s = sim(lineI, lineJ)
            co += 1
            b += 1
            if b == chunkSize:
                p += 1
                TF.info(f"{p:>3}‰ - {co:>12} comparisons and {si:>10} similarities")
                b = 0
                if limit is not None and p >= limit:
                    stop = True
                    break

            if s < THRESHOLD:
                continue
            similarity[(nodeI, nodeJ)] = sim(lineI, lineJ)
            si += 1
        if stop:
            break

    TF.info(f"{p:>3}% - {co:>12} comparisons and {si:>10} similarities")
    return similarity


# %% [markdown]
# We are going to run it to several ‰ first and do some checks then.

# %%
similarity = computeSim(limit=3)

# %% [markdown]
# We check the sanity of the results.

# %%
print(min(similarity.values()))
print(max(similarity.values()))

# %%
eq = [x for x in similarity.items() if x[1] >= 100]
neq = [x for x in similarity.items() if x[1] <= 70]

# %%
print(len(eq))
print(len(neq))

# %%
print(eq[0])
print(neq[0])

# %%
print(T.text(eq[0][0][0]))
print(T.text(eq[0][0][1]))

# %% [markdown]
# Looks good.
#
# Now the whole computation.
#
# But if we have done this before, and nothing has changed, we load previous results from disk.
#
# If we do not find previous results, we compute them and save the results to disk.

# %%
PARA_DIR = f"{tempdir}/parallels"


def writeResults(data, location, name):
    if not os.path.exists(location):
        os.makedirs(location, exist_ok=True)
    path = f"{location}/{name}"
    with gzip.open(path, "wb") as f:
        pickle.dump(data, f)
    TF.info(f"Data written to {path}")


def readResults(location, name):
    TF.indent(reset=True)
    path = f"{location}/{name}"
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    with gzip.open(path, "rb") as f:
        data = pickle.load(f)
    TF.info(f"Data read from {path}")
    return data


# %%
similarity = readResults(PARA_DIR, f"sim-{version}.zip")
if not similarity:
    similarity = computeSim()
    writeResults(similarity, PARA_DIR, f"sim-{version}.zip")

# %%
len(similarity)

# %% [markdown]
# So, just over 50,000 pairs of similar lines.

# %% [markdown]
# # Add parallels to the TF dataset
#
# We can add this information to the DSS dataset as an *edge feature*.
#
# An edge feature links two nodes and may annotate that link with a value.
#
# For parallels, we link each line to each of its parallel lines and we annotate that link with the similarity between
# the two lines. The similarity is a percentage, and we round it to integer values.
#
# If *n1* is similar to *n2*, then *n2* is similar to *n1*.
# In order to save space, we only add such links once.
#
# We can then use
# [`E.sim.b(node)`](https://annotation.github.io/text-fabric/tf/core/edgefeature.html#tf.core.edgefeature)
# to find all nodes that are parallel to node.
#

# %%
metaData = {
    "": {
        "acronym": "dss",
        "description": "parallel lines in the DSS (computed)",
        "createdBy": "Dirk Roorda",
        "createdDate": "2019-05-09",
        "sourceCreatedDate": "2015",
        "sourceCreatedBy": "Martin G. Abegg, Jr., James E. Bowley, and Edward M. Cook",
        "convertedBy": "Jarod Jacobs, Martijn Naaijer and Dirk Roorda",
        "source": "Martin Abegg's data files, personal communication",
        "license": "Creative Commons Attribution-NonCommercial 4.0 International License",
        "licenseUrl": "http://creativecommons.org/licenses/by-nc/4.0/",
        "sourceDescription": "Dead Sea Scrolls: biblical and non-biblical scrolls",
    },
    "sim": {
        "valueType": "int",
        "edgeValues": True,
        "description": "similarity between lines, as a percentage of the common material wrt the combined material",
    },
}

# %%
simData = {}

for ((f, t), d) in similarity.items():
    simData.setdefault(f, {})[t] = d

# %%
TF.save(
    edgeFeatures=dict(sim=simData), metaData=metaData, location=location, module=module
)

# %% [markdown]
# # Turn the parallels feature into a module
#
# Here we show how to turn the new feature `sim` into a module, so that users can easily load it in a Jupyter notebook or in the TF browser.

# %% language="bash"
# text-fabric-zip 'etcbc/dss/parallels/tf'

# %% [markdown]
# I have added this file to a new release of the DSS Github repo.

# %% [markdown]
# # Use the parallels module
#
# We load the DSS corpus again, but now with the parallels module.

# %%
A = use("ETCBC/dss:clone", checkout="clone", hoist=globals())

# %% [markdown]
# Lo and behold: you see the parallels module listed with one feature: `sim`. It is in *italics*, which indicates
# it is an edge feature.
#
# We just do a quick check here and in another notebook we study parallels a bit more, using the feature `sim`.
#
# We count how many similar pairs their are, and how many 100% similar pairs there are.

# %%
query = """
line
-sim> line
"""
results = A.search(query)
refNode = results[20000][0]
refNode

# %%
query = """
line
-sim=100> line
"""
results = A.search(query)

# %% [markdown]
# Let's show a few of the pairs are 100 percent similar.

# %%
A.table(results, start=1, end=10, withNodes=True)

# %% [markdown]
# There is also a lower level way to work with edge features.
#
# We can list all edges going out from a reference node.
# What we see is tuple of pairs: the target node and the similarity between the reference node and that target node.

# %%
E.sim.f(refNode)

# %% [markdown]
# Likewise, we can observe the nodes that target the reference node:

# %%
E.sim.t(refNode)

# %% [markdown]
# Both sets of nodes are similar to the reference node and it is inconvenient to use both `.f()` and `.t()` to get the similar lines.
#
# But there is another way:

# %%
E.sim.b(refNode)

# %% [markdown]
# Let's make sure that `.b()` gives the combination of `.f()` and `.t()`.

# %%
f = {x[0] for x in E.sim.f(refNode)}
b = {x[0] for x in E.sim.b(refNode)}
t = {x[0] for x in E.sim.t(refNode)}

# are f and t disjoint ?

print(f"the intersection of f and t is {f & t}")

# is b the union of f and t ?

print(f"t | f = b ? {f | t == b}")
