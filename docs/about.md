<img src="images/dss-logo.png" align="right" width="200"/>
<img src="images/tf.png" align="right" width="200"/>

# The Dead Sea Scrolls (DSS)

> The Dead Sea Scrolls (also Qumran Caves Scrolls) are ancient Jewish religious manuscripts
found in the Qumran Caves in the Judaean Desert,
near Ein Feshkha on the northern shore of the Dead Sea.

> [Wikipedia article on DSS](https://en.m.wikipedia.org/wiki/Dead_Sea_Scrolls).

> Martin G. Abegg, Jr. (b. 1950) is a notable Dead Sea Scrolls scholar,
researcher, and professor.
Abegg is responsible for reconstructing the full text of the Dead Sea Scrolls
from the Dead Sea Scrolls concordance,
a project that broke the lengthy publication monopoly held on the scrolls.

> [Wikipedia article on Abegg](https://en.wikipedia.org/wiki/Martin_Abegg)

# Provenance

The contents of this repo is created during the project ?? url ??
carried out by Jarod Jacobs, Martijn Naaijer and Robert Rezetko.

Martin Abegg has given permission to Jarod Jacobs to use his data files for this
project and to distribute the results under a CC-BY-NC license.

**to fill in: more info about the provenance of Abegg's data files**

The corpus consists of two files, one for the non-biblical scrolls and one for the 
biblical scrolls.

Jarod Jacobs took the files, straightened out the columns and handed them
as tab-separated text files to Dirk Roorda, who
converted the data into Text-Fabric format by means of a special purpose
Python program [tfFromAbegg.py](../programs/tfFromAbegg.py).

This program performs numerous checks, and as a results several corrections have been made.

The result of the conversion are the files in the `.tf` subdirectory.
They afre plain text files that roughly correspond with the columns in the files by Abegg.
A single `.tf` file is called a feature. It maps nodes to values.

However, we have separated out all text-critical and morphological information into
additional features, thereby greatly uncluttering the mass of information in these files.

# Acknowledgements

We are indebted to Martin Abegg for making his data files available and for 
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
[Accordance](https://www.accordancebible.com), maker of top-notch commerical Bible software,
also uses the data files of Martin Abegg.
Accordance has candidly made clear that our use of his files does not infringe on
rights held by Accordance.

If you have any questions about how you can use this material,
please contact [Jarod Jacobs](https://warnerpacific.academia.edu/JarodJacobs)

# Links

* https://www.deadseascrolls.org.il
