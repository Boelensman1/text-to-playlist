#!/usr/bin/env python

"""
This script converts a plex playlist .html to a .txt that text-to-playlist can
read and process.

Written in 2015 by Wigger Boelens wigger.boelens@gmail.com

To the extent possible under law, the author has dedicated all copyright and
related and neighboring rights to this software to the public domain worldwide.
This software is distributed without any warranty.

You should have received a copy of the CC0 Public Domain Dedication along with
this software. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
"""

import sys
import os
import getopt
from HTMLParser import HTMLParser


def usage():
    """Show the user some help, is called by using --help."""
    print 'Usage: create_playlist.py [options]'
    print '-i --input    the input html file'
    print "-o --output   the output txt (optional, if omitted will"
    print "              create next to existing file)"
    print '--help        shows this message'


class ParsePlexHTML(HTMLParser):
    """Parses the plex html"""
    next_data_is = False
    result = []
    subresult = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'div' or tag == 'span':
            for name, value in attrs:
                if name == 'class':
                    if value.startswith('media-duration'):
                        self.next_data_is = 'duration'
                    elif value.startswith('media-secondary-subtitle'):
                        self.next_data_is = 'album'
                    elif value.startswith('media-primary-subtitle'):
                        self.next_data_is = 'artist'
                    elif value.startswith('media-title'):
                        self.next_data_is = 'song'
                break

    def handle_endtag(self, tag):
        self.next_data_is = False

    def handle_data(self, data):
        if self.next_data_is:
            self.subresult[self.next_data_is] = data
            if len(self.subresult) is 4:
                # got all data!
                self.result.append(self.subresult)
                self.subresult = {}


def plext_to_txt(input_filename, output_filename):
    """The function that processes the html"""
    # start by reading the file
    with open(input_filename) as file_handle:
        content = file_handle.readlines()

    parser = ParsePlexHTML()
    parser.feed(''.join(content))

    with open(output_filename, 'w') as file_handle:
        for data in parser.result:
            file_handle.write(data['song'] + '\n')
            file_handle.write(data['artist'] + '\n')
            file_handle.write(data['album'] + '\n')
            file_handle.write(data['duration'] + '\n')
            file_handle.write('\n')

    print 'File', '"'+output_filename+'"', 'written!'
    return 1


def main(argv=None):
    """the main function that handles the arguments"""
    if argv is None:
        argv = sys.argv

    try:
        arglist = ["help", "input=", "output="]
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", arglist)
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    if len(args) > 0:
        print "option(s)", args, "not recognized"
        usage()
        return 2

    output_filename = None
    input_filename = None
    for opt, val in opts:
        if opt in ("-h", "--help"):
            usage()
            return 1
        elif opt in ("-i", "--input"):
            input_filename = val
        elif opt in ("-o", "--output"):
            output_filename = val
        else:
            assert False, "unhandled option"

    if input_filename is None:
        print "Missing argument"
        usage()
        return 2

    if not os.path.isfile(input_filename):
        print "input file is not found"
        usage()
        return 3

    if output_filename is None:
        root = os.path.basename(input_filename)
        output_filename = root + '.txt'

    if os.path.isfile(output_filename):
        print 'File', '"'+output_filename+'"', 'exists, overwrite?'
        answer = raw_input("Y/n ")
        if answer != '' and answer.lower() != 'y':
            print 'Aborting!'
            return 0

    return plext_to_txt(input_filename, output_filename)


if __name__ == "__main__":
    sys.exit(main())
