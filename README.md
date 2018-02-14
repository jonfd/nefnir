
# Nefnir
Nefnir is a rule-based lemmatizer for Icelandic text. It has been trained on the [Database of Modern Icelandic Inflection](http://bin.arnastofnun.is/DMII/), which contains over 6,000,000 tagged inflectional forms and their lemmas.

## Usage
```
optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input-file INPUT_FILE
                        read input from specified file
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        write output to specified file
  -f FROM_ENCODING, --from-encoding FROM_ENCODING
                        character encoding of input file (default: utf-8)
  -t TO_ENCODING, --to-encoding TO_ENCODING
                        character encoding of output file (default: utf-8)
  -s SEPARATOR, --separator SEPARATOR
                        the string separating word forms, tags and lemmas
                        (default: \t)
```

Before a text file can be lemmatized, it first has to be tokenized and tagged by a tool such as [IceNLP](http://icenlp.sourceforge.net/) or [IceStagger](http://www.ling.su.se/english/nlp/tools/stagger). Input files should contain a single word form and tag per line (in that order), optionally with empty lines as sentence delimiters:

```
Hvað	fshen
var	sfg3eþ
þetta	fahen
?	?

Maðurinn	nkeng
leit	sfg3eþ
upp	aa
frá	aþ
verkinu	nheþg
.	.
```
Nefnir will append a lemma to each line:
```
Hvað	fshen	hver
var	sfg3eþ	vera
þetta	fahen	þessi
?	?	?

Maðurinn	nkeng	maður
leit	sfg3eþ	líta
upp	aa	upp
frá	aþ	frá
verkinu	nheþg	verk
. . .
```
## Examples
Lemmatize a UTF-8 encoded document with a single tab character separating word forms and tags.

* `nefnir.py -i tagged.txt -o lemmatized.txt`

Lemmatize a CP-1252 (Windows-1252) encoded document with a single space separating word forms and tags, and encode the output as latin1 (ISO-8859-1).
* `nefnir.py -i tagged.txt -o lemmatized.txt -f cp1252 -t latin1 -s ' '`

## Requirements
Python 3.2+

## License
    Copyright © 2018 Jón Friðrik Daðason

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
