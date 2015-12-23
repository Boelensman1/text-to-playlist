#!/usr/bin/env python

"""
This script converts a .txt to a playlist
.txt must be formatted in the following way:
Songname
Artist
Album
Length in minutes:seconds

example:
Shoot to Thrill
AC/DC
Back in Black
5:18

Written in 2015 by Wigger Boelens wigger.boelens@gmail.com

To the extent possible under law, the author has dedicated all copyright and
related and neighboring rights to this software to the public domain worldwide.
This software is distributed without any warranty.

You should have received a copy of the CC0 Public Domain Dedication along with
this software. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
"""

import sys
import os
import itertools as it
import glob
import getopt
import re
from difflib import SequenceMatcher
from colors import red


def usage():
    """Show the user some help, is called by using --help."""
    print 'Usage: create_playlist.py [options]'
    print '-i --input    the input text file'
    print '-l --library  the library with the music files (required)'
    print "-o --output   the output m3u (optional, if omitted will"
    print "              print to console)"
    print '--help        shows this message'


def glob_escape(pathname):
    """Escape all special characters."""
    drive, pathname = os.path.splitdrive(pathname)
    magic_check = re.compile('([*?[])')
    pathname = magic_check.sub(r'[\1]', pathname)
    return drive + pathname


def glob_extentions(loc, *extentions):
    """glob with multiple filetypes"""
    loc = glob_escape(loc)
    res = it.chain.from_iterable(glob.iglob(loc + ext) for ext in extentions)
    return res


def similar(wanted, to_check):
    """check how similar two files are"""
    return SequenceMatcher(None, wanted, to_check).ratio()


def print_options(options, add_abort=False):
    """Print an option and its similarity"""
    for index, option in enumerate(options):
        if len(options) is 1:
            index_string = ''
        else:
            index_string = str(index + 1) + ")"
        similarity_string = '('+str(int(option['similarity']*100))+'%)'
        print index_string, option['dirname'], similarity_string
    if add_abort:
        print "A) Abort"


def get_from_multiplechoice(options, message_when_failing):
    """Show the options and let the user choose"""
    if len(options) is 0:
        print message_when_failing
        print "Aborting"
        sys.exit(1)
    if len(options) is 1:
        # check how certain we are
        if options[0]['similarity'] > 0.9:
            return options[0]['dirname']
        # no good enough match found, show the failing message
        print message_when_failing
        print ""  # create some space
        print "Is the following name correct?"
        print_options(options)
        answer = raw_input("Y/n: ")
        if answer == "" or answer.lower() == "y":
            return options[0]['dirname']
        if answer.lower() == "n":
            print "Aborting"
            sys.exit(1)
        # no option chosen, lets retry
        print red("No valid answer given")
        return get_from_multiplechoice(options, message_when_failing)

    # multiple possible options, display the message and give the options
    print ""  # create some space
    print message_when_failing
    print "Choose one of the following:"
    # sort the options
    options = sorted(options, key=lambda k: k['similarity'], reverse=True)
    print_options(options, True)
    answer = raw_input("Enter a number or press enter for the default (1): ")
    if answer.lower() == "a":
        print "Aborting"
        sys.exit(1)
    else:
        if not answer:
            answer = 1  # the default
        if not str(answer).isdigit():
            print red("Answer not recognized")
            return get_from_multiplechoice(options, message_when_failing)

        answer = int(answer)
        if len(options) > answer-1:
            return options[0]['dirname']
        else:
            print ""
            print 'Answer out of bounds'
            return get_from_multiplechoice(options, message_when_failing)


def get_artist_dir(artist, artists, artist_dirs):
    """Get the name of the directory of the artist"""
    options = []
    if artist not in artists:
        for dirname in artist_dirs:
            similarity = similar(artist, dirname)
            if artist == dirname:
                artists[artist] = dirname
                return artists

            similarity = similar(artist, dirname)
            if similarity > 0.5:
                options.append({'dirname': dirname, 'similarity': similarity})
    else:
        return artists
    message = 'Artist: ' + artist + ' no exact match found!'
    artists[artist] = get_from_multiplechoice(options, message)
    return artists


def get_album_dir(album, artist, albums, location):
    """Get the name of the directory of the album"""
    options = []
    location = location + "/" + artist

    if artist not in albums:
        albums[artist] = {}

    album_dirs = next(os.walk(location))[1]
    if artist not in albums or album not in albums[artist]:
        for dirname in album_dirs:
            if album == dirname:
                albums[artist][album] = dirname
                return albums
            similarity = similar(album, dirname)
            if similarity > 0.5:
                options.append({'dirname': dirname, 'similarity': similarity})
    else:
        return albums
    message = 'Album: ' + album + ' - ' + artist + " no exact match found!\n"
    message += 'Searched in: ' + location

    albums[artist][album] = get_from_multiplechoice(options, message)
    return albums


def get_song_path(song, artist, album, location):
    """Get the location of the song"""
    location = location + "/" + artist + "/" + album + "/"
    song_files = glob_extentions(location, "*.m4a", "*.mp3")
    regex = re.compile(ur'\d{1,3} ')
    options = []
    filename_to_path = {}
    for path in song_files:
        filename = path.replace(location, "")
        filename = os.path.splitext(filename)[0]
        filename = re.sub(regex, "", filename)
        filename_to_path[filename] = path

        if song == filename:
            return path

        similarity = similar(song, filename)
        if similarity > 0.4:
            options.append({'dirname': filename, 'similarity': similarity})
    message = 'Song: ' + song + ' - ' + album + ' - ' + artist
    message += " no exact match found!\n"
    message += 'Searched in: ' + location
    filename = get_from_multiplechoice(options, message)
    return filename_to_path[filename]


def process_content(content, library):
    """Process the text to transform it into a playlist"""
    songs = []
    count = 0
    for line in content:
        # first line is artist name
        if count is 0:
            song = {}
            song['name'] = line.rstrip()
        if count is 1:
            song['artist'] = line.rstrip()
        if count is 2:
            song['album'] = line.rstrip()
        if count is 3:
            line = line.split(':')
            line = int(line[0])*60 + int(line[1])
            song['duration'] = str(line)
        if count is 4:
            songs.append(song)
            count = -1
        count += 1

    # ok, lets start looking for the files
    # we compile a list of all artist folders
    artists = {}
    albums = {}
    output = "#EXTM3U\n"

    artist_dirs = next(os.walk(library))[1]

    for song in songs:
        artists = get_artist_dir(song['artist'], artists, artist_dirs)
        artist_dir = artists[song['artist']]

        # we found the artist folder, now lets look for the album
        albums = get_album_dir(song['album'], artist_dir, albums, library)
        album_dir = albums[artist_dir][song['album']]

        # we found the album folder, now lets look for the song
        song_path = get_song_path(song['name'], artist_dir, album_dir, library)

        # ok, now do the output, start with the info
        output += "#EXTINF:" + song['duration'] + ","
        output += song['album'] + " - "
        output += song['artist'] + "\n"

        # and then the path
        output += song_path + "\n"

    return output


def create_playlist(input_filename, output_filename, library):
    """The function that actually creates the playlist"""
    # start by reading the file
    with open(input_filename) as file_handle:
        content = file_handle.readlines()

    # now process the file
    output = process_content(content, library)

    # write the output to a file
    if output_filename is None:
        print "\n"
        print "------OUTPUT------"
        print output
        return 0

    with open(output_filename, 'w') as file_:
        file_.write(output)

    return 1


def main(argv=None):
    """the main function that handles the arguments"""
    if argv is None:
        argv = sys.argv

    try:
        arglist = ["help", "input=", "output=", "library="]
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:l:", arglist)
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
    library = None
    for opt, val in opts:
        if opt in ("-h", "--help"):
            usage()
            return 1
        elif opt in ("-i", "--input"):
            input_filename = val
        elif opt in ("-o", "--output"):
            output_filename = val
        elif opt in ("-l", "--library"):
            library = os.path.normpath(val)
        else:
            assert False, "unhandled option"

    if input_filename is None or library is None:
        print "Missing argument"
        usage()
        return 2

    if not os.path.isfile(input_filename):
        print "input file is not found"
        usage()
        return 3

    if not os.path.isdir(library):
        print "library is not found"
        usage()
        return 3

    return create_playlist(input_filename, output_filename, library)


if __name__ == "__main__":
    sys.exit(main())
