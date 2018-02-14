#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import codecs
import json
import logging
import os
import sys
import time

FORMAT = '%(asctime)s - %(levelname)s %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class Nefnir(object):
    """
    A rule-based lemmatizer
    """
    def __init__(self):
        """
        Initialize an instance of the Nefnir lemmatizer.
        """
        nefnir_dir = os.path.dirname(sys.argv[0])

        # Load rules
        rules_path = os.path.join(nefnir_dir, 'rules.json')

        with open(rules_path, encoding='utf-8') as f:
            self.rules = json.load(f)

        # Load tagset
        tag_path = os.path.join(nefnir_dir, 'tags.json')

        with open(tag_path, encoding='utf-8') as f:
            self.tagmap = json.load(f)

        self.proper = {t for t in self.tagmap if t[0] == 'n' and t[-1] in {'m', 'ö', 's'}}
        self.unanalyzed = {t for t in self.tagmap if t[:2] == 'nx'} | {'x', 'e', 'as'}

    def lemmatize(self, form, tag):
        """
        Lemmatize a word form given its part-of-speech tag.

        :param form: A word form.
        :param tag: The word form's part-of-speech tag.
        :return: The word form's lemma.
        """
        try:
            ntag = self.tagmap[tag]
        except KeyError:
            if any((c for c in tag if c.isalpha())):
                logger.warning("Unknown tag: {}".format((form, tag)))
            return form

        # Websites and interjections
        if tag in {'v', 'au'}:
            return form.lower()

        # Unanalyzed words
        if tag in self.unanalyzed:
            return form

        # Words that end with a hyphen
        if form[-1] == '-':
            if tag in self.proper:
                return self.recase(form, tag, form)
            return form.lower()

        # Words that end with a punctuation mark
        if not form[-1].isalpha():
            return form

        form_lower = form.lower()

        if ntag not in self.rules:
            logger.debug("No rules for this tag: {} {} {}".format(form, tag, ntag))
            return self.recase(form, tag, form)

        if form_lower in self.rules[ntag]['form']:
            suffix_from, suffix_to = self.rules[ntag]['form'][form_lower]
        else:
            suffixes = get_suffixes(form_lower)

            try:
                target = next(s for s in suffixes if s in self.rules[ntag]['suffix'])
                suffix_from, suffix_to = self.rules[ntag]['suffix'][target]
            except StopIteration:
                logger.debug("No rules for this word form: {} {} {}".format(form, tag, ntag))
                return self.recase(form, tag, form)

        form_prefix = form_lower[:-len(suffix_from)] if suffix_from else form_lower
        lemma = form_prefix + suffix_to

        if not lemma:
            logger.warning("Rule produced an empty lemma: ({}, {}, {}) ('{}' -> '{}')".format(form, tag, ntag,
                                                                                              suffix_from, suffix_to))
            lemma = form_lower

        return self.recase(form, tag, lemma)

    def recase(self, form, tag, lemma):
        """
        Determine how to properly case a lemma given the word form and part of speech tag it was derived from.

        Nefnir transforms words into lowercase prior to lemmatization. Some words, such as proper nouns, abbreviations
        and foreign words therefore need to be re-capitalized or changed back into uppercase.

        :param form: A word form, cased as it was written.
        :param tag: The word form's part-of-speech tag.
        :param lemma: The word form's lemma, in lowercase.
        :return: A properly cased lemma.
        """
        # Hyphenated words: try to maintain original casing in every part
        #   1) (DNA-þræðinum, nþeþg) -> dna-þráður -> DNA-þráður
        #   2) (Vestur-Íslendingum, nkfþ-s) -> vestur-íslendingur -> Vestur-Íslendingur
        #   3) (Stoke-on-Trent, e) -> stoke-on-trent -> Stoke-on-Trent
        if '-' in form[1:-1]:
            fparts = form.split('-')
            lparts = lemma.split('-')

            result = []
            for fpart, lpart in zip(fparts, lparts):
                if fpart.lower() == lpart.lower():
                    # part was not transformed by lemmatization
                    result.append(fpart)
                elif fpart.isupper():
                    # part was transformed and was uppercase
                    result.append(lpart.upper())
                elif fpart.istitle():
                    # part was transformed and was capitalized
                    result.append(lpart.title())
                else:
                    # part was transformed and not uppercase or capitalized
                    result.append(lpart.lower())

            if tag in self.proper and not result[0].isupper():
                result[0] = result[0].title()

            return "-".join(result)

        # Proper nouns: capitalize the lemma
        #   1) (Halldórs, nken-s) -> halldór -> Halldór
        #   2) (HALLDÓRS, nken-s) -> halldór -> Halldór
        if tag in self.proper:
            # if len(form) > 1 and form.isupper():
            #     return lemma.upper()
            return lemma.title()

        # If none of the above applies, return lemma in lowercase
        return lemma


def get_suffixes(s):
    """
    Return an iterator yielding a string's suffixes, from the largest to the smallest.

    :param s: A text string.
    :return: An iterator for the string's suffixes.
    """
    return (s[pos:] for pos in range(len(s) + 1))


def main():
    # Command line interface
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-file", help="read input from specified file", required=True)
    parser.add_argument("-o", "--output-file", help="write output to specified file", required=True)
    parser.add_argument("-f", "--from-encoding", help="character encoding of input file (default: utf-8)",
                        default="utf-8")
    parser.add_argument("-t", "--to-encoding", help="character encoding of output file (default: utf-8)",
                        default="utf-8")
    parser.add_argument("-s", "--separator", help="the string separating word forms, tags and lemmas (default: \\t)",
                        default='\t')
    args = parser.parse_args()

    args.separator = codecs.decode(args.separator, 'unicode_escape')

    # Lemmatize input
    time_start = time.time()
    nefnir = Nefnir()

    logger.info("Reading input from {} ({})".format(args.input_file, args.from_encoding))
    logger.info("Separator set to {}".format(repr(args.separator)))

    with open(args.input_file, encoding=args.from_encoding) as f:
        lines = f.read().splitlines()
        num_lines = len(lines)
        lines = {l: None for l in lines}

    for line in lines:
        try:
            form, tag = line.split(args.separator)
            if form:
                lemma = nefnir.lemmatize(form, tag)
                lines[line] = args.separator.join((form, tag, lemma))
        except ValueError:
            if line.strip():
                logger.warning('Ignoring line: {}'.format(line))

    # Stats
    time_elapsed = time.time() - time_start
    lines_per_second = num_lines / time_elapsed
    stats = "{:,} lines processed in {:.2f} s ({:,.1f} lines/s)".format(num_lines, time_elapsed, lines_per_second)
    logger.info(stats)

    # Write output
    logger.info("Writing output to {} ({})".format(args.output_file, args.to_encoding))

    with open(args.input_file, encoding=args.from_encoding) as f_in:
        with open(args.output_file, 'w', encoding=args.to_encoding) as f_out:
            for line in f_in:
                line = line.rstrip('\n')
                output = lines[line] or ''
                f_out.write(output + '\n')


if __name__ == '__main__':
    main()
