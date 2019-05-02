<img src="images/dss-logo.png" align="right" width="200"/>
<img src="images/tf.png" align="right" width="200"/>

# Feature documentation

Here you find a description of the transcriptions of the Dead Sea Scrolls (DSS),
the
[Text-Fabric model](https://annotation.github.io/text-fabric/Model/Data-Model/)
in general, and the node types, features of the
DSS corpus in particular.

See also

*   [about](about.md) for the provenance of the data;
*   [TF docs](https://annotation.github.io/text-fabric/) for documentation on Text-Fabric.
*   [DSS API](https://annotation.github.io/app-dss/blob/master/api.md) on how to use the
    TF-app DSS.

The corpus consists of two files, one for the non-biblical scrolls and one for the 
biblical scrolls.
In both files, the material is subdivided into *scroll*, *fragment*, *line*.
In the biblical file, *book*, *chapter* and *verse* are also marked.

Every line in both files has fields for

* transcription
* lexeme
* morphological tags

and some bits of extra information.

The Text-Fabric model views the text as a series of atomic units, called
*slots*. In this corpus [*signs*](#sign) are the slots.

On top of that, more complex textual objects can be represented as *nodes*. In
this corpus we have node types for:

[*sign*](#sign),
[*word*](#word),
[*lex*](#lex),
[*cluster*](#cluster),
[*line*](#line),
[*fragment*](#fragment),
[*scroll*](#scroll),
[*halfverse*](#halfverse),
[*verse*](#verse),
[*chapter*](#chapter),
[*book*](#book).

The type of every node is given by the feature
[**otype**](https://annotation.github.io/text-fabric/Api/Features/#node-features).
Every node is linked to a subset of slots by
[**oslots**](https://annotation.github.io/text-fabric/Api/Features/#edge-features).

Nodes can be annotated with features.
Relations between nodes can be annotated with edge features.
See the table below.

Text-Fabric supports up to three customizable section levels.
In this corpus we use:
[*scroll*](#scroll) and [*fragment*](#fragment) and [*line*](#line).

Note that we do have node types corresponding to *book*, *chapter*, *verse*,
and *halfverse*,
but they are not configured as TF-sections.

## Transcription

We map the transcriptions and lexemes to Hebrew unicode.
The transcriptions are consonant only, the lexemes are pointed.
The vowels we encounter in those lexemes have
been transcribed by one or more special characters, probably
in order to fine-tune the position of those points with respect to their
consonants.
We reduce them to single Hebrew unicodes per vowel.

There are bracketing constructs in the transcription, such as `<< >>`, `« »`, `[ ]`.
It turns out that in the files as we see them, they are consistently written as if in the right to left writing
direction. So they appear as `>> <<`, `» «`, `] [`.
When we reproduce the orginal transcription, we put them allback into the left-to-right orientation, because
this is the intended direction. The cause that we encounter them in the opposite orientation might be that
we have stripped all unicode orientation characters (202A-202E)
in our sanitizing preprocessing step.

We also supply the ETCBC transcription for Hebrew material.
For the full details see the extensive
[Hebrew transcription table](https://annotation.github.io/text-fabric/Writing/Hebrew.html).

# Reference table of features

*(Keep this under your pillow)*

Some features come in three variants, a main variant
and two variants with the letter *e* of *o* after the feature name.

* *main variant* the unicode value
* **e** the ETCBC transliteration, or something that extends it
* **o** the original transcription (Abegg)

## Node type [*sign*](#sign)

Basic unit containing a single symbol, mostly a consonant, but it can also be 
punctuation, or a text-critical sign.

The type of sign is stored in the feature `type`.

type | source | etcbc | unicode | description
------- | ------ | ------ | --- | ---
`cons` | `m` `M` | `M` `m`| `מ` `ם` | normal consonantal letter
`vowel` | `I` | `I`| ` ִ ` | vowel point
`sep` | ` ` | `_` | ` ` | non-breaking space
`sep` | `-` | `&` | `־` | maqaf
`sep` | `/`| `'`| `׳` | morpheme break 
`punct` | `.` | `00` | `׃` | sof pasuq
`punct` | `±` | `0000` | `׃׃` | paleo divider
`numeral` | `A` `D` | `>'` `k'` | `א֜` `ך֜` | a numeral 
`missing` | `--` | ` 0 ` | `ε` | representation of a missing sign
`uncertain` | `?` | ` ? ` | ` ? ` | representation of an uncertain sign (degree 1)
`uncertain` | ``\`` | ` # ` | ` # ` | representation of a uncertain sign (degree 2)
`uncertain` | `�` | ` #? ` | ` #? `| representation of an uncertain sign (degree 3)
`add` | `+` | ` + ` | `+` | representation of an addition between numerals
`term` | `/` | `╱` | `╱` | representation of an end of line

feature | values | Abegg | ETCBC | Unicode | description
------- | ------ | ------ | ----------- | --- | ---
**alternative** | `1` | `lwz/)h(` | `LWZ61(H)` | | indicates an alternative material, marked by being within brackets `( )`
**correction** | `1` | `yqw>mw<N` | `JQW(< MW >)n` | | material is corrected by a modern editor, marked by being within single angle brackets  `< >`
**correction** | `2` | `>>zwnh«<<` | `(<< ZWNH# >>)` | | material is corrected by an ancient editor, marked by being within double angle brackets  `<< >>`
**correction** | `3` | `^dbr/y^` | `(^ DBR ? J ^)` | | material is corrected by an ancient editor, marked by being within double angle brackets  `<< >>`
**reconstruction** | `1` | `]p[n»y` | `[P]N#?Y` | | material is reconstructed by a modern editor, marked by being within square brackets  `[ ]`
**removed** | `1` | `}m«x«r«yØM«{` | `{M#Y#R#J?m#}` | | material is removed by a modern editor, marked by being within single braces  `{ }`
**removed** | `2` | `twlo}}t{{` | `TWL<{{t}}` | | material is removed by an ancient editor, marked by being within double braces  `{{ }}`
**glyph[eo]** | | `m` | `M` | `מ` | transliteration of an individual sign
**type** | | | | | type of sign, see table above
**uncertain** | `1` | `b«NØ` | `B#n?` | | indicates *uncertainty of degree=1* by flag `|`
**uncertain** | `2` | `at«` `aj«y»/K` | `>T#` `>X#J#?) ? k` | | indicates *uncertainty of degree=2* by flag `«` or brackets `« »`, in this example the `« »` are not brackets but individual tokens
**uncertain** | `3` | `]p[n»y` | `[P]N#?Y` | | indicates *uncertainty of degree=3* by flag `»`
**uncertain** | `4` | `a\|hrwN` | `>#?HRWn` | | indicates *uncertainty of degree=4* by flag `\|`
**vacat** | `1` | `≥ ≤` | `(- -)` | | indicates an empty, unwritten space by brackets `≤ ≥`

## Node type [*word*](#word)

Sequence of signs separated corresponding to a single line in the Abegg data files.
If a word is adjacent to a next word, the Abegg data file has `B` in a certain column,
and we leave the *after* feature without value.

There are several types of things that can occupy a word:
a string of consonants, a numeral, punctuation, nothing, ...

The type of word is stored in the feature `type`.

type | description
------- | ------
`empty` | nothing
`glyph` | a sequence of consonants or uncertain tokens
`numeral` | a numeral
`punc` | punctuation
`other` | nothing of the above

If a transcription field is empty, but there is lexeme information,
we insert a word node with type `glyph`
and all of its textual features (*full[eo], glyph[eo], punc[eo]*) absent.
We add a slot of type `empty` to this word.

feature | Abegg | ETCBC | Unicode | description
------- | ------ | ------ | --- | --------
**after** | ` ` | | | whether there is a space after a word and before the next word
**biblical** | `1` | | | whether this word is in a biblical scroll or not
**full[eo]** | `mm/nw[` | `MM61NW]` | `ממ׳נו]` | full transcription of a word, including flags and clustering characters
**glyph[eo]** | `mmnw` | `MMNW]` | `ממנו` | letters of a word excluding flags and brackets
**lex[eo]** | `mIN` | `MIn` | `מִן` | lexeme of a word
**punc[eo]** | `.` | `00` | `׃` | punctuation at the end of a word
**morpho** | `vHi1cpX3mp` | | | original morphological tag for this word; all information in this has been decomposed into the morphological features below
**type** | | | | | type of word, see table above
**srcLn** | `424242` | | | | line number of this word in its source data file

A word has several morphology features.
If a word is divided into morphemes, each of the morphemes can carry morphology.
If we have gender masculine on the main word,
and gender feminine on the suffix,
and gender common on the second suffix, it will be represented by

```
  gn=m
  gn2=f
  gn3=c
```  

Below is a summary table.
For all values, look at the morphology
[configuration file](https://github.com/ETCBC/dss/blob/master/yaml/morph.yaml).
There you see also the connection with the original Abegg encoding of morphological tags.
We have switched to slightly more verbose feature values, and to feature names that are
in line with those of the 
[BHSA](https://etcbc.github.io/bhsa/).
The original tag as a whole is also available in the feature **morpho**.

We only describe the plain features here, but keep in mind that they may be accompanied
by their numbered brothers.

Al these features may contain the value `unknown`.

feature | examples | description
------- | ------ | ------
**sp** | `subs` `verb` `numr` `ptcl` | part-of-speech
**cl** | `card` `proper` `prep` | class, i.e. a sub category within its part-of-speech
**ps** | `1` `2` `3` | person
**gn** | `m` `f` `c` `b` | gender, also with *common* and *both*
**nu** | `s` `p` `d` | number, also with *dual*
**st** | `a` `c` `d` | state, also with *determined*
**cs** | `nom` `acc` `gen` | case
**vs** | `qal` `passive` `piel` `hithpolel` | verbal stem, also with *passive*, some are Hebrew, some are Aramaic
**vt** | `perf` `impf` `wayy` `impv` `infc` `infa` `ptca` `ptcp` | verbal tense or aspect, also with *wayyiqtol*
**md** | `juss` `coho` `cons` | mood 

## Node type [*cluster*](#cluster)

Grouped sequence of [*signs*](#sign). There are different
types of these bracketings. Clusters of the same type are not nested.
Clusters of different types need not be nested properly with respect to each other.

The type of a cluster is stored in the feature `type`.

This is a summary of the source encoding, see also the features at the sign level with the same names above.

type | value | examples | description
------- | ------ | ------ | ---
`correction` | `1` | `< >` | correction made by a modern editor
`correction` | `2` | `<<  >>` | correction made by an ancient editor
`correction` | `3` | `^ ^` | supralinear (ancient) correction
`removed` | `1` | `{ }` | removed by a modern editor
`removed` | `2` | `{{  }}` | removed by an ancient editor
`reconstruction` | `1` | `[ ]` | reconstructed by a modern editor
`vacat` | `1` | `≤ ≥` | empty space
`alternative` | `1` | `( )` | alternative
`uncertain` | `2` | `« »` | uncertain, with level of uncertainty 2

Each cluster induces a sign feature with the same name as the type of the cluster,
which gets a numeric value, as indicated in the table.

Note the *vacat* cluster: by definition, it contains no signs.
In order to anchor it into the text sequence, we have generated an empty slot in each vacat cluster.

We have done the same for other clusters that happened to be without other slots.

Other features:

feature | examples | description
------- | ------ | ------
**biblical** | `1` | whether this cluster is in a biblical scroll or not

## Node type [*line*](#line)

Section level 3.

Subdivision of a containing [*fragment*](#fragment).
Corresponds to a set of source data lines with the same value in the *line* column.

feature | values | description
------- | ------ | ------
**biblical** | `1` | whether this line is in a biblical scroll or not
**label** | `3` | number of a physical line (not necessarily integer valued)

There are lines in the source data with number `0` and with a subdivision by means of an
other number. We have converted this situation to a sequence of lines numbered as
`0.1`, `0.1`, etc. Hence the number of a line is not always an integer.
So we store the number in a feature named `label`, instead of number.

## Node type [*fragment*](#fragment)

Section level 2.

Subdivision of a containing [*scroll*](#scroll).
Corresponds to a set of source data lines with the same value in the *fragment* column.

For non-biblical scrolls, the fragment is usually called *column*. 

feature | values | description
------- | ------ | ------
**biblical** | `1` | whether this fragment is in a biblical scroll or not
**label** | `f3` | label of a physical fragment or column

## Node type [*scroll*](#scroll)

Section level 1.

Corresponds to a set of source data lines with the same value in the *scroll* column.

feature | values | description
------- | ------ | ------
**biblical** | `1` | whether this scroll is in a biblical scroll or not
**acro** | `1Q1` | short name of a physical scroll

## Node type [*halfverse*](#halfverse)

Only for biblical scrolls. Not a section type.

Subdivision of a containing [*verse*](#verse).
Corresponds to a set of source data lines with the same non-numerical part in the *verse* column.

Not every verse is divided in half verses.

feature | values | description
------- | ------ | ------
**number** | `3` | number of its containing part
**label** | `a` | the non-numerical part of the verse number

## Node type [*verse*](#verse)

Only for biblical scrolls. Not a section type.

Subdivision of a containing [*chapter*](#chapter).
Corresponds to a set of source data lines with the same numerical part in the *verse* column.

The division in verses may or may not coincide with the division in lines.

feature | values | description
------- | ------ | ------
**number** | `3` | number of a verse line (integer valued), without the non-integer part

## Node type [*chapter*](#chapter)

Only for biblical scrolls. Not a section type.

Subdivision of a containing [*book*](#book).
Corresponds to a set of source data lines with the same value in the *chapter* column.

The division in chapters may or may not coincide with the division in fragments.

feature | values | description
------- | ------ | ------
**label** | `6` `f6` | label of a chapter

## Node type [*book*](#book)

Only for biblical scrolls. Not a section type.

Corresponds to a set of source data lines with the same value in the *book* column.

The division in books may or may not coincide with the division in scrolls.

feature | values | description
------- | ------ | ------
**acro** | `Gen` `1Q1` | short name of a book

# More about the node types

We discuss the node types we are going to construct. A node type corresponds to
a textual object. Some node types will be marked as a section level.

## Sign

This is the basic unit of writing.

**The node type [*sign*](#sign) is our slot type in the Text-Fabric representation of this corpus.**

Slots are the textual positions.
They are be occupied by individual glyphs (consonants, "digits", punctuation, miscellaneous glyphs).

All signs have the features **type** and **glyph[eo]**.

### Glyphs

The *type* stores the kind of glyph, such as `cons`.
The *glyph glyphe glypho* features store the transcription of the glyph, without any flags
and brackets. They store it in Unicode, ETCBC transcription, and original Abegg code.

These features do not suffice to reconstruct the original Abegg transcription, because the flags
and brackets are not part of them.

#### Punctuation

Punctuation is either a mark or a white space, or a boundary.
All punctuation characters have Unicode representations.
For some we have *borrowed* a Hebrew character that has a different meaning in the Masoretic text,
but that does not occur otherwise in the Dead Sea Scrolls.
The reason is that we can represent Hebrew consonants plus punctuation in a smooth,
right-to-left way.

source | etcbc | unicode | description
--- | --- | --- | ---
` ` | `_` | ` ` | non-breaking intra-word space
`-` | `&` | `־` | maqaf
`.` | `00` | `׃` | sof pasuq
`±` | `0000` | `׃׃` | double sof pasuq (mis)used as paleo divider 
`/` | `61` | `׳` | geresh (punctuation, not accent) (mis)used as morpheme break

#### Numerals

Numerals are ancient signs for denoting quantities.

source | etcbc | unicode | value
--- | --- | --- | ---
`A` | `>'` | `א֜` | 1
`å` | `>52` | `אׄ` | 1
`B` | `>53` | `אׅ` | 1
`∫` | `>35` | `אֽ` | 1
`C` | `J'` | `י֜` | 10
`D` | `k'` | `ך֜` | 20
`F` | `Q'` | `ק֜` | 100

#### Miscellaneous

Several characters have to do with uncertainty and illegibility.
They have an improvised Unicode representations.
We propose an transcription that works inside the ETCBC transcription.
Note that these have spaces around them.

source | etcbc | unicode | description
--- | --- | --- | ---
`--` | ` 0 ` | `ε` | missing sign
`?` | ` ? ` | ` ? ` | uncertain sign, degree 1
``\`` | ` # ` | `#` | uncertain sign, degree 2
`�` | ` #? ` | `#?` | uncertain sign, degree 3
`+` | ` + ` | `+` | addition symbol between numerals
`/` | `╱` | `╱` | end of line token

### Text-critical marks

Signs also have features corresponding to flags and brackets, that store under which flag
or inside which brackets the sign occurs:
**uncertain** **correction** **remove** **vacat** **alternative** **reconstruction**.

#### Flags

*Signs* may have *flags*.
In transcription they show up as a special trailing character.
Flags code for signs that are damaged, questionable (in their reading), in short: uncertain.
They apply to the preceding character.

We propose an transcription that works inside the ETCBC transcription.
Note that these have *no* spaces around them.

We use this for the Unicode represenatation as well.

source | etcbc / unicode | description
--- | --- | ---
`Ø` | `?` | uncertain, degree 1
`«` | `#` | uncertain, degree 2
`»` | `#?` | uncertain, degree 3
`\|` | `##` | uncertain, degree 4

Note that there is also a bracket pair for uncertainty level 2.

#### Brackets

We discuss the brackets under the node type [*cluster*](#cluster).
Each type of bracket corresponds to a feature of the same name at the *sign* level.

With some difficulty, you can reconstruct the Abegg source from this, modulo the order
of flags and brackets. 

The recommended way to reconstruct the original transcriptions by Abegg is to go to the
word level.

## Cluster

One or more [*signs*](#sign) may be bracketed by certain delimiters.
Together they form a *cluster*.

Each pair of boundary signs marks a cluster of a certain type.
This type is stored in the feature **type**.

Clusters are not be nested in clusters of the same type.

Clusters of one type in general do not respect the boundaries of clusters of other types.

Clusters may contain just one [*sign*](#sign).

Cluster boundaries are usually within words.

In Text-Fabric, cluster nodes are linked to the signs it contains.
So, if `c` is a cluster, you can get its signs by 

    L.d(c, otype='sign')

More over, every type of cluster corresponds to a numerical feature on signs with the same name
as that type.

We propose an transcription that works inside the ETCBC transcription.
Note that these have *sometimes* a space at the inner side.

We use the original brackets for the Unicode representation as well.
But note that in the original the direction of the brackets is inverted, due to the conversion process
that has stripped RTL and LTR triggering characters.
In the Unicode representation we restore the proper direction.

In the table below, the *value* is the value that the associated feature has for 
signs within that type of brackets under the given description.

source / unicode | etcbc | value | type | description
--- | --- | --- | --- | ---
`^ ^` | `(^ ^)` | 3 | `correction3` | correction by ancient editor, supralinear
`<< >>` | `(<< >>)` | 2 | `correction2` | correction by ancient editor
`< >` | `(< >)` | 1 | `correction` | correction by modern editor
`{{ }}` | `({{ }})` | 2 | `removed2` | removed by ancient editor
`} {` | `({ })` | 1 | `removed` | removed by modern editor
`≤ ≥` | `(- -)` | 1 | `vacat` | vacat: an empty, unwritten space in the manuscript
`( )` | `( )` | 1 | `alternative` | alternative reading
`[ ]` | `[ ]` | 1 | `reconstruction` | modern reconstruction
`« »` | `(# #)` | 2 | `uncertain2` | uncertainty of degree 2

## Word

Words are the contents of the transcription fields of the source data lines.
Words will be separated by spaces or by nothing, in case the
connection field in the same source data line has a `B`. 

They have features **glyph[eo] full[eo] punc[eo] after**.

* **full[eo]** full value of the word: letters, symbols, punctuation, flags, brackets;
  **fullo** is the original content of the *trans* field in the source data file
* **glyph[eo]** letter value of the word: consonants, vowels, digits, numerals;
  no punctuation, flags, or brackets;
* **punc[eo]** the punctuation of a word, if any;
* **after** a space when the word should be followed by a space,
  i.e. when the *connection* field does not have a `B`.

The source transcription can be reconstructed by walking over all words and printing

```
fullo + after
```

for each word.

A non-text-critical transcription can be generated by printing 

```
glypho + punco + after
```

for each word.

Or, in ETCBC transcription / Unicode:

```
glyphe + punce + after
glyph + punc + after
```

These features will be used in the *text-formats* below.

# Text formats

The following text formats are defined (you can also list them with `T.formats`).

format | kind | description
--- | --- | ---
`text-orig-full`     | plain | the source text, glyphs only, no flags / brackets, in unicode
`text-trans-full`    | plain | the source text, glyphs only, no flags / brackets, in etcbc transcription
`text-source-full`   | plain | the source text, glyphs only, no flags / brackets, in Abegg transcription
`text-orig-extra`    | plain | the source text with flags and brackets, in unicode
`text-trans-extra`   | plain | the source text with flags and brackets, in etcbc transcription
`text-source-extra`  | plain | the source text with flags and brackets, in Abegg transcription
`lex-orig-full`      | plain | lexeme of a word in unicode
`lex-trans-full`     | plain | lexeme of a word in etcbc transcription
`lex-source-full`    | plain | lexeme of a word in Abegg transcription
`layout-orig-full`   | layout | as `text-orig-full`   but the flag and cluster information is visible in layout
`layout-trans-full`  | layout | as `text-trans-full`  but the flag and cluster information is visible in layout
`layout-source-full` | layout | as `text-source-full` but the flag and cluster information is visible in layout

The formats with `text` result in strings that are plain text, without additional formatting.

The formats with `layout` result in pieces html with css-styles; the richness of layout enables us to code more information
in the plain representation, e.g. blurry characters when signs are damaged or uncertain.

See also the 
[showcases](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/dss/display.ipynb).

