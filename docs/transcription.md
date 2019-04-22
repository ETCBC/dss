<img src="images/dss-logo.png" align="right" width="200"/>
<img src="images/tf.png" align="right" width="200"/>

Feature documentation
=====================

Here you find a description of the transcriptions of the Dead Sea Scrolls (DSS),
the Text-Fabric model in general, and the node types, features of the
DSS corpus in particular.

See also [about](about.md) [text-fabric](textfabric.md)

Conversion from Abegg's data files to TF
-------------------------

Below is a description of document transcriptions in
DSS (see below)
and an account how we transform them into
[Text-Fabric](https://annotation.github.io/text-fabric/) format by means of
[tfFromAbegg.py](../programs/tfFromAbegg.py).

The corpus consists of two files, one for the non-biblical scrolls and one for the 
biblical scrolls. In both files, the material is subdivided into *scroll*, *fragment*, *line*.
In the biblical file, *book*, *chapter* and *verse* are also marked.

Every line in both files has a fields for

* transcription
* lexeme
* morphological tags

and a bit of extra information.

The Text-Fabric model views the text as a series of atomic units, called
*slots*. In this corpus [*signs*](#sign) are the slots.

On top of that, more complex textual objects can be represented as *nodes*. In
this corpus we have node types for:

[*sign*](#sign),
[*word*](#word),
[*cluster*](#cluster),
[*line*](#line),
[*fragment*](#fragment),
[*scroll*](#scroll).
[*verse*](#verse),
[*chapter*](#chapter),
[*book*](#book).

The type of every node is given by the feature
[**otype**](https://annotation.github.io/text-fabric/Api/Features/#node-features).
Every node is linked to a subset of slots by
[**oslots**](https://annotation.github.io/text-fabric/Api/Features/#edge-features).

Nodes can be annotated with features. See the table below.

Text-Fabric supports up to three customizable section levels.
In this corpus we use:
[*scroll*](#scroll) and [*fragment*](#fragment) and [*line*](#line).

Note that we do have node types corresponding to *book*, *chapter*, and *verse*,
but they are not configured as TF-sections.

Unicode Glyphs
--------------
We map the transcriptions and lexemes to Hebrew unicode.
The transcriptions are consonant only, the lexemes are pointed.
It seems that various transcription schemes for the pointing are at work,
so that a single vowel is transcribed by two or sometimes three special characters.
We reduce them to the Hebrew unicodes.

We also supply the ETCBC transcription for Hebrew material.

Other docs
----------

[Text-Fabric API](https://annotation.github.io/text-fabric)

[DSS API](https://annotation.github.io/app-dss/blob/master/api.md)

Reference table of features
===========================

*(Keep this under your pillow)*

Node type [*sign*](#sign)
-------------------------

Basic unit containing a single symbol, mostly a consonant, but it can also be 
a white space, punctuation, or a text-critical sign.

The type of sign is stored in the feature `type`.

type | examples | rewritten/etcbc | description
------- | ------ | ------ | ---
`consonant` | `m` `M` | | normal consonantal letter
`punctuation` | `-` `.` | `&` `00` | maqaf, sof pasuq 
`whitespace` | ` ` | `_` | non-breaking whitespace within a word
`numeral` | `A` `B` `C` `D` `F` `å` `∫`  | ` 1 ` ` 1B ` ` 10 ` ` 20 ` ` 100 ` ` 1a ` ` 1f ` | a numeral, only in words that are a numeral as a whole
`missing` | `--` | ` 0 ` | representation of a missing sign
`doubtful` | `?` | ` ~ ` | representation of a doubtful sign
`uncertain` | `/` `\\` | ` ? ` | representation of an uncertain sign
`unknown` | `�` | ` ! ` | representation of an unknown sign
`add` | `+` | ` + ` | representation of an addition between numerals
`divider` | `±` | ` | ` | representation of paleo divider

feature | values | examples | rewritten/etcbc | description
------- | ------ | ------ | ----------- | ---
**after** | | | | what comes after a sign before the next sign
**correctionAncient** | `1` | `>>zwnh«<<` | `(<< ZWNH# >>)` | whether a sign is corrected by an ancient editor, marked by being within double angle brackets  `<< >>`
**correctionModern** | `1` | `yqw>mw<N` | `YQW(< MW >)n` | whether a sign is corrected by a modern editor, marked by being within single angle brackets  `< >`
**correctionSupra** | `1` | `^dbr/y^` | `(^ DBR ? Y ^)` | whether a sign is corrected by an ancient editor, marked by being within double angle brackets  `<< >>`
**damaged** | `1` | `at«` `aj«y»/K` | `>T#` `>X(# J #) ? k` | indicates the presence of the *damaged* flag `«` or brackets `« »`
**damagedUncertain** | `1` | `a|hrwN` | `>#?HRWn` | indicates the presence of the *damaged_uncertain* flag `|`
**uncertain** | `1` | `b«NØ` | `B#n?` | indicates the presence of the *damaged_uncertain* flag `|`
**type** | | | | type of sign, see table above

Node type [*word*](#word)
-------------------------
Sequence of signs separated by `-`. Sometimes the `-` is omitted. Very rarely there is an other character between two signs, such as `:` or `/`. Words themselves are separated by spaces.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**after** | ` ` | | what comes after a word before the next word
**atf** | `{disz}sze-ep-_{d}suen` | idem | full atf of a word, including flags and clustering characters
**sym** **symr** **symu** | | | essential parts of a word, composed of the **sym**, **symr**, **symu** values of its individual signs; the **-r** variant uses accented letters; the **-u** variant uses cuneiform unicode

Node type [*cluster*](#cluster)
-------------------------------

Grouped sequence of [*signs*](#sign). There are different
types of these bracketings. Clusters may be nested.
But clusters of different types need not be nested properly with respect to each other.

The type of a cluster is stored in the feature `type`.

type | examples | description
------- | ------ | ------
`correctionAncient` | `<<  >>` | correction made by an ancient editor
`correctionModern` | `< >` | correction made by a modern editor
`correctionSupra` | `^ ^` | supralinear (ancient) correction
`removedAncient` | `{{  }}` | removed by an ancient editor
`removedModern` | `{ }` | removed by a modern editor
`reconstructionModern` | `[ ]` | reconstructed by a modern editor
`vacat` | `≤ ≥)` | empty space
`alternative` | `( )` | alternative
`damaged` | `« »` | damaged

Each cluster induces a sign feature with the same name as the type of the cluster,
which gets value 1 precisely when the sign is in that cluster.

Node type [*line*](#line)
-------------------------

Subdivision of a containing [*face*](#face).
Corresponds to a transcription or comment line in the source data.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**col** | `1` | `@column 1` | number of the column in which the line occurs; without prime, see also `primecol`
**ln** | `1` | `1. [a-na]` | ATF line number of a numbered transcription line; without prime, see also `primeln`; see also **lnc**
**lnc** | `$a` `$b` | `$ rest broken` | ATF line number of a comment line (`$`); the value `$` plus `a`, `b` etc., every new column restarts this numbering; see also `ln`
**lnno** | | | combination of **col**, **primecol**, **ln**, **primeln** to identify a line
**primecol** | `1'` | whether the column number has a prime `'` | 
**primeln** | `1'` | whether the line number has a prime `'` | 
**remarks** | `reading la-mi! proposed by Von Soden` | `# reading la-mi! proposed by Von Soden` | the contents of a remark targetedto the contents of a transcription line; the `remark` feature is present on the line that is being commented; multiple remark lines will be joined with a newline
**srcLn** | `1. [a-na x]-da-a-a`| idem | see [source data](#source-data)
**srcLnNum** | 29908 | not represented | see [source data](#source-data)
**trans** | `1` | | indicates whether a line has a translation (in the form of a following meta line (`#`))
**translation@en** | `was given (lit. sealed) to me—` | `#tr.en: was given (lit. sealed) to me—` | English translation in the form of a meta line (`#`)

Node type [*face*](#face)
-------------------------

One of the sides of an *object* belonging to a document [*document*](#document).
In most cases, the object is a *tablet*, but it can also be an *envelope*, or yet an other kind of object. 

feature | values | in ATF | description
------- | ------ | ------ | -----------
**face** | `obverse` `reverse` `seal 1` `envelope - seal 1` | `@obverse` `@reverse` `@seal 1` | type of face, if on an object different from a tablet, the type of object is prepended
**object** | `tablet` `envelope` | `@tablet` `@envelope` | object on which a face is situated; seals are not objects but faces
**srcLn** | `@obverse` | idem | see [source data](#source-data)
**srcLnNum** | 29907 | not represented | see [source data](#source-data)

Node type [*document*](#document)
-----------------------------

The main entity of which the corpus is composed, representing the transcription
of all objects associated with it.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**collection** | `AbB` | `&P509373 = AbB 01, 059` | the collection of a [*document*](#document)
**docnote** | `Bu 1888-05-12, 200` | `&P365091 = CT 02, pl. 10, Bu 1888-05-12, 200` | additional remarks in the document identification
**docnumber** | `059` | `&P509373 = AbB 01, 059` | the identification of a [*document*](#document) as number within a collection - volume
**lang** | `akk` `sux` |  | the language the document is written in. `akk` = *Akkadian*, `sux` = *Sumerian*. See the sign feature `langalt` for the language of smaller portions of the document
**pnumber** | `P509373` | `&P509373 = AbB 01, 059` | the P-number identification of a [*document*](#document)
**srcfile** | AbB-primary or AbB-secondary | not represented | see [source data](#source-data)
**srcLn** | `&P494060 = AbB 14, 226` | idem | see [source data](#source-data)
**srcLnNum** | 29904 | not represented | see [source data](#source-data)
**volume** | `01` | `&P509373 = AbB 01, 059` | the volume of a [*document*](#document) as number within a collection

We also store a bunch of the metadata fields that preced the transliterations in the source
files:

feature | from metadata field | description
------- | ------ | ------
author | Author(s) | author 
pubdate | Publication date | publication date 
museumname | Collection | museum name 
museumcode | Museum no. | museum code 
excavation | Excavation no. | excavation number 
period | Period | period indication 
material | Material | material indication 
genre | Genre | genre 
subgenre | Sub-genre | sub-genre 
transcriber | ATF source | person who did the encoding into ATF 
ARK | UCLA Library ARK | persistent identifier of type ARK 

Source data
===========

All nodes that correspond directly to a line in the corpus, also get features by
which you can retrieve the original transcription.

For documents and faces the line refers to the source line where the encoding starts.

*   **srcfile** the name of the source file, it does not occur as such in the source data;
*   **srcLn** the literal contents of the line in the source;
*   **srcLnNum** the line number of the corresponding line in the source file,
    not the ATF line number, but *n* as in the *n*-th line in the file,
    it does not occur as such in the source data. 

Slots
=====

Slots are the textual positions. They can be occupied by individual signs or inline comments `($ ccc $)`.
We have inserted empty slots on comment lines (starting with `$`)
in order to anchor these lines at the right
place in the text sequence and to store the comment itself in the feature `comment`.

We discuss the node types we are going to construct. A node type corresponds to
a textual object. Some node types will be marked as a section level.

Sign
----

This is the basic unit of writing.

**The node type [*sign*](#sign) is our slot type in the Text-Fabric representation of this corpus.**

All signs have the features **atf**, **atfpre**, **atfpost** and **after**.

Together they are the building blocks by which the complete original ATF sequence for that sign
can be reconstructed:

    atfpre + atf + atfpost + after

*atf* contains the encoding of the sign itself, including possible flags.

*atfpre* and *atfpost* contain the bracketing characters before and after the sign.

*after* contains the linking characters with the next sign, usually a `-` or a ` `.

For analytical purposes, there is a host of other features on signs, depending on the type of sign.

### Simple signs ###

The defining trait of a sign is its *reading* and/or optionally its *grapheme*.

We will collect the name string of a sign, without variants and flags, and store
it in the sign feature **reading** if it is lowercase, and **grapheme** if it is uppercase.

The *type* of such signs is `reading` or `grapheme`. 

Simple signs may be *augmented* with *flags* (see below).

### Unknown signs ###

The letters `x` and `X`, `n` and `N` in isolation stand for an unknown signs.

The *type* of such signs is `unknown`. 

If the value is `x` or `n`, it will stored in **reading**, if it is `X` or `N` in **grapheme**.

The `x` and `X` stand for completely unknown signs, the `n` and `N` stand for unknown signs
of which it is known that they are numerals.

**N.B:** See under numerals below, where `n` plays a slightly different role.

### Ellipsis ###

The value `...`stands for an unknown number of missing signs.

The *type* of such signs is `ellipsis`. 

The **grapheme** feature will be filled with `...`. 

### Numerals: repeats and fractions ###

Signs, especially those with a numeric meaning, may be repeated.

    5(disz)

Numeric signs may also be preceded with a *fraction*:

    5/6(disz)

We store the integral number before the brackets in the feature **repeat**,
and the fraction in the feature **fraction**.

If the repeat is `n`, it means that the amount of repetition is uncertain
or that a repetition is missing.
We store it as `repeat` = `-1`, so repeats always have an integer value.

In a numeral, within the brackets you find the **reading** or **grapheme**,
depending on whether it is lowercase or uppercase..

Numeral signs have type `numeral`.

After the closing bracket the numeral may be augmented with *flags*.

### Complex signs: operators ###

There are two constructs that have the same shape, but not the same meaning.
Both lead to a complex sign.

Correction:

    szu!(LI)

Operator (`x`):

    isx(USZ)

In both cases we see a **reading**, followed by an **operator** (`!` or `x`),
followed by a **grapheme**.

The type of such signs is `complex`.

The grapheme might be quite complex: an expression with or without surrounding `| |`,
and with operators `.` inside.
We have not broken down these graphemes in our conversion, they are stored as is in **grapheme**.

### Comment signs ###

Within a transcription line, you might encounter expressions of the form `($` *ccc* `$)`.

These are *inline* comments, not to be confused with structural line comments (`$` lines)
or other line comments (`#` lines) which occupy a line of their own.

Such comments will be converted to single signs, of type `comment`, and the comment itself
goes into the feature **comment**. 

The comment, surrounded by the `($ $)` goes into the feature **atf**.

### Commentline signs ###
Commentline signs have been artificially added to comment lines (`$` lines) in order to 
anchor them to the textual sequence.

The comment text of the line goes into the feature **comment** of the single commentline
sign of that line. It also goes to features `sym`, `symr`, `symu` and `atf`.

### Empty signs ###

Empty signs may have been generated as the result of faulty inputs.
The conversion program detects these errors and issues messages about them.
The current run of the conversion has not detected empty signs.

### Flags ###

*Signs* may have *flags*.
In transcription they show up as a special trailing character.
Flags code for signs that are damaged, questionable (in their reading), remarkable, or collated.

#### collated `*` ####

Example:

  5. _8(gesz2)* sze gur_ i-ib-szu-u2

Here the numeral `8(gesz2)` is collated.

#### remarkable `!` ####

Only if the `!` is not followed by `(GGG)`

Example:

    8. a-di isz!-ti i-na-an-na

Here the reading `isz` is remarkable.

#### question `?` ####

Questionable identification.

Example:

    6. sza a-na ti?-bi a-bi-ka be-li szu-um-szu

Here the reading `ti` is questionable.

#### damage `#` ####

Example:

    10. _ma2_ a-na ra-ka-ab s,u2-ha-ar-tim#

Here the reading `tim` is damaged.

The other nodes
===============

Cluster
-------

One or more [*signs*](#sign) may be bracketed by `_ _` or by `( )` or by `[ ]` or by `< >` or by `<< >>`:
together they form a *cluster*.

Each pair of boundary signs marks a cluster of a certain type.
This type is stored in the feature **type**.

Clusters are not be nested in clusters of the same type.

Clusters of one type in general do not respect the boundaries of clusters of other types.

Clusters do not cross line boundaries.

Clusters may contain just one [*sign*](#sign).

In Text-Fabric, cluster nodes are linked to the signs it contains.
So, if `c` is a cluster, you can get its signs by 

    L.d(c, otype='sign')

More over, every type of cluster corresponds to a numerical feature on signs with the same name
as that type.
It has value `1` for those signs that are inside a cluster of that type and no value otherwise.

### langalt `_ _` ###

Marks a switch to the alternate language.
In this corpus, the documents are mainly in Akkadian (`akk`). The alternate language is Sumerian (`sux`).

### det `{ }` ###

Marks a glosses of the determinative kind.

### uncertain `( )` ###

Marks uncertain readings.

### missing `[ ]` ###

Marks missing signs.

### excised `<< >>` ###

Marks signs that have been excised by the editor in order to arrive at a reading.

### supplied `< >` ###

Marks signs that have been supplied by the editor in order to arrive at a reading

Word
----

Words are sequences of signs joined by `-` or occasionally `:` or `/`.
Words themselves are separated by spaces ` `.

They have only one feature: **atf**, which contains the original ATF source,
including cluster characters that are glued to the word or occur inside it.

Line
----

**This node type is section level 3**

A node of type *line* corresponds to a numbered line with transcribed
material or to a line with a structural comment (which starts with `$`).

Lines that start with a `#` are comments to the previous line or metadata to the document.
Their contents are turned into document and line features, but they do not give rise
to line nodes.

Lines get a column number from preceding `@column i` lines (if any), and this gets stored in 
**col**.

There is no node type corresponding to columns.

The ATF number at the start of the line goes into **ln**, without the `.`.

If primes `'` are present on column numbers and line numbers, they will not get stored on
**col** and **ln**, but instead the features **primcol** and **primeln** will receive a `1`.

The number of the line in the source file is stored in **srcLnNum**,
the unmodified contents of the line, including the ATF line number goes into **srcLn**.

If the line is a structural comment (`$`), the contents of the line goes into
the **comment** feature of its sole sign, a sign of type `commentline`.

If a line has a comment in the form of one or more following lines that start with `# `,
then these lines will be joined with newlines and collectively go into **remarks**.

If a line has a translation, say in English, marked by a following line starting with 
`#tr.en:`, then the contents of the translation will be added to **translation@en**.

If a line has any translation at all, in whatever language, the feature **trans** becomes `1`.

Face
----

**This node type is section level 2**

[*Lines*](#line) are grouped into [*faces*](#face).

*Faces* are marked by lines like

    @obverse

or

    @reverse

or

    @seal 1

There are a few other possibilities, such as:

    @left edge
    @upper edge

A node of type *face* corresponds to the material after a *face* specifier and
before the next *face* specifier or the end of an object or [*document*](#document).

Note that *objects*, such as *tablets*, *envelopes* and *eyestones* are also 
marked by `@` lines.
Whenever the object is not a tablet, the type of object will prepended to the name of the face:

The obverse of an envelope is

    @envelope - obverse

whereas

    @obverse

is the obverse of a tablet.

Seals are faces, not objects.

The resulting face type is stored in the feature **face**.

The object on which a face resides, goes to the feature **object**.

Faces also have features **srcLn** and **srcLnNum**, like lines.
In this cases, they refer to the line where a face starts.

Document
------

**This node type is section level 1.**

[*Faces*](#face) are grouped into *documents*.

*Documents* are started by lines like

    &P510635 = AbB 12, 112

Here we collect

* `P002174` as the **pnumber** of the *document*,
* `AbB` as the **collection**,
* `12` as the **volume**,
* `112` as the **docnumber**

If this line has irregular content, we put the irregular material into **docnote**:

* `&P497776 = Fs Landsberger 235`
  * **collection**, **volume**, **docnumber** undefined;
  * **docnote** = `Fs Landsberger 235`
* `&P479394 = CT 33, pl. 26, BM 097405`
  * **collection** = `CT`
  * **volume** = `33`
  * **docnumber** = `26`
  * **docnote** = `BM 097405`

We also add the name of the source file as a feature **srcfile**,
with possible values:

* `AbB-primary` for documents whose primary publication is `AbB` ;
* `AbB-secondary` for documents whose secondary publication(s) has `AbB` .

This corpus is just a set of *documents*. The position of a particular document in
the whole set is not meaningful. The main identification of documents is by their
**pnumber**,
not by any sequence number within the corpus.

Text formats
=============

The following text formats are defined (you can also list them with `T.formats`).

format | kind | description
--- | --- | ---
`text-orig-full` | plain | the full atf, including flags and cluster characters
`text-orig-plain` | plain | the essential bits: readings, graphemes, repeats, fractions, operators, no clusters, flags, inline comments
`text-orig-rich` | plain | as `text-orig-plain` but with accented characters
`text-orig-unicode` | plain | as `text-orig-plain` but with cuneiform unicode characters, hyphens are suppressed
`layout-orig-rich` | layout | as `text-orig-rich` but the flag and cluster information is visible in layout
`layout-orig-unicode` | layout | as `text-orig-unicode` but the flag and cluster information is visible in layout

The formats with `text` result in strings that are plain text, without additional formatting.

The formats with `layout` result in pieces html with css-styles; the richness of layout enables us to code more information
in the plain representation, e.g. blurry characters when signs are damaged or uncertain.

See also the 
[showcases](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/oldbabylonian/display.ipynb).

