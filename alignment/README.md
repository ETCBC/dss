# caccht automatic alignment with BHSA

This folder contains the javascript function used to automatically align the BHSA with the 1Qisaa scroll. The texts are first aligned on verse level. This is done by asigning to each word a verse id, or `vid`, which is calculated as follows:
```js
const vid = (bookNr * 1000 + chapterNr) * 1000 + verseNr
```
The book, chapter and verse information is present on the Abegg DSS data. Data from both tables are exported to the 1Qisaa.csv and bhs_ref.csv files for reference.

Then, when from both the scroll and the BHSA the same words of a verse are loaded, the words need to be aligned. This is what the `matchWoorden` function is used for. It checks for the longest strings of continuous matches. It checks whether the consonants are equal, or uses the morphological code to eliminate differences by matres lectionis. For 1Qisaa, the program was able to automatically predict 70% of the words, and found a further 11% of possible correspondences. This greatly enhanced the speed at which the scroll could be checked.