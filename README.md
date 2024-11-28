<div>
<img src="docs/images/dss-logo.png" align="left" width="300"/>
<img src="docs/images/etcbc.png" align="right" width="200"/>
<img src="docs/images/tf.png" align="right" width="200"/>
<img src="docs/images/dans.png" align="right" width="100"/>
</div>

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/ETCBC/dss/)](https://archive.softwareheritage.org/browse/origin/https://github.com/ETCBC/dss/)
[![DOI](https://zenodo.org/badge/168822533.svg)](https://zenodo.org/badge/latestdoi/168822533)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

# The Dead Sea Scrolls in Text-Fabric

This repo contains transcriptions of biblical and non-biblical Dead Sea Scrolls with linguistic annotations.

See also
[about](docs/about.md)
and
[feature documentation](docs/transcription.md).

You can run your own programs off-line, and publish your work in online notebooks.

### The CACCHT project: Creating Annotated Corpora of Classical Hebrew Texts

This dataset is developed as part of the CACCHT project, which is a collaboration of Martijn Naaijer, Christian Canu Højgaard, Martin Ehrensvärd, Robert Rezetko, Oliver Glanz, and Willem van Peursen. The goal of CACCHT is to prepare and publish ancient Semitic texts digitally, that can be used for research and education.

### Software

The main processing tool is [Text-Fabric](https://github.com/annotation/text-fabric/).
It is instrumental to turn the analysis of ancient data into computing narratives.

The ecosystem is Python and Jupyter notebooks.

### Getting started

Start with the
[tutorial](https://nbviewer.jupyter.org/github/etcbc/dss/blob/master/tutorial/start.ipynb).

### Authors

*   [Jarod Jacobs](https://warnerpacific.academia.edu/JarodJacobs)
    at 
    [Warner Pacific College](http://www.warnerpacific.edu)
*   [Martijn Naaijer](https://vu-nl.academia.edu/MartijnNaaijer)
    at 
    [Eep Talstra Center for Bible and Computer](http://etcbc.nl)
*   [Dirk Roorda](https://github.com/dirkroorda) at
    [DANS](https://www.dans.knaw.nl)

### Acknowledgements

* [Martin Abegg](https://en.wikipedia.org/wiki/Martin_Abegg)
  for providing his data files to us;

**N.B.:** Releases of this repo have been archived at
the
[Software Heritage Archive](https://www.softwareheritage.org)
and
[Zenodo](https://zenodo.org).
Click the badges to be taken to the archives. There you find ways to cite this work.

### Status

We will collect feedback for quite some time before we bump the version to 1.0 or higher.

*   2019-06-11 Release 0.6, fixed the fact that the dotless shin was represented as sin, spotted by Oliver Glanz
*   2019-05-20 Release 0.5,
    new
    [tests](https://nbviewer.jupyter.org/github/etcbc/dss/blob/master/programs/checks.ipynb).
*   2019-05-09 Release 0.4.
*   2019-05-08 Release 0.3.
*   2019-05-05 Release 0.2.

## Related datasets
### BHSA Family

* [bhsa](https://github.com/etcbc/bhsa) Core data and feature documentation
* [phono](https://github.com/etcbc/phono) Phonological representation of Hebrew words
* [parallels](https://github.com/etcbc/parallels) Links between similar verses
* [valence](https://github.com/etcbc/valence) Verbal valence for all occurrences
  of some verbs
* [trees](https://github.com/etcbc/trees) Tree structures for all sentences
* [bridging](https://github.com/etcbc/bridging) Open Scriptures morphology
  ported to the BHSA
* [pipeline](https://github.com/etcbc/pipeline) Generate the BHSA and SHEBANQ
  from internal ETCBC data files
* [shebanq](https://github.com/etcbc/shebanq) Engine of the
  [shebanq](https://shebanq.ancient-data.org) website

### Extended family

* [dss](https://github.com/etcbc/dss) Dead Sea Scrolls
* [sp](https://github.com/dt-ucph/sp) Samaritan Pentateuch
* [extrabiblical](https://github.com/etcbc/extrabiblical)
  Extra-biblical writings from ETCBC-encoded texts
* [peshitta](https://github.com/etcbc/peshitta)
  Syriac translation of the Hebrew Bible
* [syrnt](https://github.com/etcbc/syrnt)
  Syriac translation of the New Testament
