﻿<img src="images/dss-logo.png" align="right" width="200"/>
<img src="images/tf.png" align="right" width="200"/>

# The Dead Sea Scrolls (DSS)

> The Dead Sea Scrolls (also Qumran Caves Scrolls) are ancient Jewish religious
manuscripts found in the Qumran Caves in the Judaean Desert,
near Ein Feshkha on the northern shore of the Dead Sea.

> [Wikipedia article on DSS](https://en.m.wikipedia.org/wiki/Dead_Sea_Scrolls).

> Martin G. Abegg, Jr. (b. 1950) is a notable Dead Sea Scrolls scholar,
researcher, and professor.
Abegg is responsible for reconstructing the full text of the Dead Sea Scrolls
from the Dead Sea Scrolls concordance,
a project that broke the lengthy publication monopoly held on the scrolls.

> [Wikipedia article on Abegg](https://en.wikipedia.org/wiki/Martin_Abegg)

# Provenance

The contents of this repo is created during the
[*Creating Annotated Corpora of Classical Hebrew Texts (CACCHT) project*]()
carried out by Jarod Jacobs, Martijn Naaijer, Dirk Roorda, Robert Rezetko,
Oliver Glanz, and Willem van Peursen.

The DSS texts and morphological data connected with them were generously
provided by Martin Abegg.
They consist of two foundational sets of data: transcriptions and morphological tagging.
The transcriptions come from various sources,
but primarily reflect what is found in the Discoveries in the Judean Desert
series (Oxford:Clarendon Press, 1955-). 
For full details see:

[DSSB-Read me first](assets/readme-dssb.pdf) and
[QUMRAN - Read me first](assets/readme-qumran.pdf).

In addition to what is derived from the Abegg sources, Martijn Naaijer has
provided several extras:

*   ETCBC morphological feature data 
*   clause and phrase boundaries

Both kinds of data are the result of creating models (*machine learning
models*) from the BHSA and
applying them to the DSS. This is experimental.

## Abegg sources

Abegg started morphologically tagging the Qumran texts in the mid-90s
with the assistance of several people that he mentions in the above read me first files.
Over the following decades, Abegg completed full morphological tagging 
of nearly every Hebrew and Aramaic scroll found in the Judaean Desert between
1947 and today.
For more information about the development and particularities of Abegg’s data,
we will once again point you to the DSSB and QUMRAN read me first files.

The tagging scheme itself is also 
[documented](assets/morph.pdf).

After conversion to Text-Fabric, the these tags have been normalized into
separate features, such as
*`sp` (part-of-speech)*, *`ps` (person)*, *`nu` (number)*, *`gn` (gender)*, etc.

See [morphological features in TF](transcription.md#morphological-features).

Upon learning of the current project, Martin Abegg graciously gave permission
to Jarod Jacobs to use his data and 
to distribute the results under a CC-BY-NC license.

The corpus consists of two files, one for the non-biblical scrolls and one for the 
biblical scrolls.

Jarod Jacobs has made preliminary analysis of these source files
and has communicated his observations to Dirk Roorda,
who subsequently converted the source data files to Text-Fabric format
by means of a special purpose Python program
[tfFromAbegg.py](../programs/tfFromAbegg.py).

This program performs numerous checks, and as a result several corrections have
been made.

The conversion logs have been
[preserved](https://github.com/ETCBC/dss/tree/master/log).
The files there contain several diagnostics, an account of the morphology tag parsing,
and lists of all (scroll, fragment, line) entries in the source data,
before and after conversion.

The result of the conversion are the files in the `.tf` subdirectory.
They are plain text files that roughly correspond to the columns in the data files.
A single `.tf` file is called a feature. It maps nodes to values.

However, we have separated out all text-critical and morphological information into
additional features, thereby greatly uncluttering the wealth of information in
these files.

## Naaijer extras

As of data version 0.7, additional features have been added in, mostly
adaptions of existing features to the ETCBC format, prepared by Martijn Naaijer.

Version 0.9 contains clause and phrase boundaries. 
This version is available on GitHub but is still work in process, so it is not yet
an official release. You can work with it by means of

``` sh
text-fabric ETCBC/dss:hot --version=0.9
```

and

``` python
A = use("ETCBC/dss:hot", version="0.9")
```

!!! caution "Rate limit"
    This will load the files one by one from GitHub, make sure you have an
    [increased rate limit]( https://annotation.github.io/text-fabric/tf/advanced/repo.html#increase-the-rate-limit)

Version 1.0 will contain phrase and clause nodes, result of Martijn Naaijer working
for the [CACCHT](https://github.com/ETCBC/CACCHT) project.

The details of the data production can be found in
[ETCBC/DSS2ETCBC](https://github.com/ETCBC/DSS2ETCBC).

## Details of the encoding

For the details of the way the DSS have been encoded into TF,
see [transcription](transcription.md).

# Acknowledgements

We are indebted to Martin Abegg for making his data available and for 
guidance during the conversion stage.
 
# License

The program code in this repo is freely available under the MIT license.

The data in this repo, notably the contents of its `.tf` subdirectory, 
is available under a 
[CC-BY-NC license](https://creativecommons.org/licenses/by-nc/4.0/)

That means that you are free to:

*   Share — copy and redistribute the material in any medium or format
*   Adapt — remix, transform, and build upon the material
*   The licensor cannot revoke these freedoms as long as you follow the license terms.

provided:

*   Attribution — You must give appropriate credit, provide a link to the license,
    and indicate if changes were made.
    You may do so in any reasonable manner,
    but not in any way that suggests the licensor endorses you or your use.
*   NonCommercial — You may not use the material for commercial purposes.
*   No additional restrictions — You may not apply legal terms or technological measures
    that legally restrict others from doing anything the license permits.

**N.B.**
If you have any questions about how you can use this material,
or suggestions for improvements, 
or other feedback, consider these options:

*   look through the
    [issues](https://github.com/ETCBC/dss/issues) on this repository and/or file a new one;
*   send an email to [Martijn Naaijer](mailto:martijn.naayer@upcmail.nl)
*   via both means you can request an invite to join our
    **ETCBC/DSS slack channel** and the community there will attempt to assist you.

# Links

* https://www.deadseascrolls.org.il
