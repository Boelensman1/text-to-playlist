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
from colors import red, yellow, blue, magenta


def usage():
    """Show the user some help, is called by using --help."""
    print 'Usage: create_playlist.py [options]'
    print '-i --input    the input text file'
    print '-l --library  the library with the music files (required)'
    print "-o --output   the output m3u (optional, if omitted will"
    print "              default to inputfilename+.m3u)"
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


def abort():
    """Something went horribly wrong, abort everything"""
    print red("Aborting!")
    sys.exit(1)


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


def search_through_all_files():
    """Search through the list of files for a song directly"""
    print 'search here!'
    abort()


def retry_manual_input():
    """Retry a search with manual input"""
    print blue("Retrying with manual input")
    answer = raw_input("New name to search for: ")

    if answer == '':
        print red('Please give an input')
        return retry_manual_input()

    print "Retrying search..."
    return ['Manual', answer]


def get_from_onechoice(options, message_when_failing):
    """Ask when we only have one options"""
    # check how certain we are
    if options[0]['similarity'] > 0.9:
        return [True, options[0]['dirname']]
    # no good enough match found, show the failing message
    print ""  # create some space
    print yellow(message_when_failing)
    print "Is the following name correct?"
    print_options(options)
    answer = raw_input("Y/n/a/s/l: ")
    if answer == "" or answer.lower() == "y":
        print magenta("Option " + options[0]['dirname'] + " chosen")
        return [True, options[0]['dirname']]
    if answer.lower() == "l":
        # search through all filenames
        return search_through_all_files()
    if answer.lower() == "s":
        # manual input
        return retry_manual_input()
    if answer.lower() == "n" or answer.lower() == "a":
        abort()
    # no option chosen, lets retry
    print red("No valid answer given")
    return get_from_onechoice(options, message_when_failing)


def get_from_multiplechoice(options, message_when_failing):
    """display the message and give the options"""
    print ""  # create some space
    print yellow(message_when_failing)
    print "Choose one of the following:"
    # sort the options
    options = sorted(options, key=lambda k: k['similarity'], reverse=True)
    print_options(options, True)
    answer = raw_input("Enter a number or press enter for the default (1): ")
    if answer.lower() == "a":
        abort()
    else:
        if not answer:
            answer = 1  # the default
        if not str(answer).isdigit():
            print red("Answer not recognized")
            return get_from_multiplechoice(options, message_when_failing)

        answer = int(answer)
        if len(options) > answer-1:
            print magenta("Option " + options[0]['dirname'] + " chosen")
            return [True, options[0]['dirname']]
        else:
            print 'Answer out of bounds'
            return get_from_multiplechoice(options, message_when_failing)


def get_from_question(options, message_when_failing):
    """Show the options and let the user choose"""
    if len(options) is 0:
        print red(message_when_failing)
        answer = raw_input("Choose option (S/l/a): ")
        if answer.lower() == "a":
            abort()
        elif answer.lower() == "s" or answer == '':
            return retry_manual_input()
        elif answer.lower() == "l":
            return search_through_all_files()
    if len(options) is 1:
        return get_from_onechoice(options, message_when_failing)

    # multiple possible options
    return get_from_multiplechoice(options, message_when_failing)


def get_artist_dir(search_string, artists, artist_dirs, song):
    """Get the name of the directory of the artist"""
    artist = song['artist']
    options = []
    if artist not in artists:
        for dirname in artist_dirs:
            similarity = similar(search_string, dirname)
            if search_string == dirname:
                artists[artist] = dirname
                return artists

            similarity = similar(search_string, dirname)
            if similarity > 0.5:
                options.append({'dirname': dirname, 'similarity': similarity})
    else:
        return artists
    message = 'Artist: ' + artist + ' no exact match found!'
    if search_string != artist:
        message += "\n"+'Searched for ' + search_string

    result = get_from_question(options, message)

    # check if found
    if result[0] is True:
        artists[artist] = result[1]
    elif result[0] is 'Manual':
        return get_artist_dir(result[1], artists, artist_dirs, song)

    return artists


def get_album_dir(search_string, albums, song, location):
    """Get the name of the directory of the album"""

    artist = song['artist']
    album = song['album']

    options = []

    if artist not in albums:
        albums[artist] = {}

    album_dirs = next(os.walk(location))[1]
    if artist not in albums or album not in albums[artist]:
        for dirname in album_dirs:
            if search_string == dirname:
                albums[artist][album] = dirname
                return albums
            similarity = similar(search_string, dirname)
            if similarity > 0.5:
                options.append({'dirname': dirname, 'similarity': similarity})
    else:
        return albums
    message = 'Album: ' + album + ' - ' + artist + " no exact match found!\n"
    message += 'Searched in: ' + location
    if search_string != album:
        message += "\n"+'Searched for ' + search_string

    result = get_from_question(options, message)
    # check if found
    if result[0] is True:
        albums[artist][album] = result[1]
        return albums
    elif result[0] is 'Manual':
        return get_album_dir(result[1], albums, song, location)


def get_song_path(search_string, song, location):
    """Get the location of the song"""

    artist = song['album']
    album = song['album']
    song_name = song['name']

    song_files = glob_extentions(location, "*.m4a", "*.mp3")
    regex = re.compile(ur'\d{1,3} ')
    options = []
    filename_to_path = {}
    for path in song_files:
        filename = path.replace(location, "")
        filename = os.path.splitext(filename)[0]
        filename = re.sub(regex, "", filename)
        filename_to_path[filename] = path

        if search_string == filename:
            return path

        similarity = similar(search_string, filename)
        if similarity > 0.4:
            options.append({'dirname': filename, 'similarity': similarity})
    message = 'Song: ' + song_name + ' - ' + album + ' - ' + artist
    message += " no exact match found!\n"
    message += 'Searched in: ' + location
    if search_string != song_name:
        message += "\n"+'Searched for ' + search_string

    result = get_from_question(options, message)
    # check if found
    if result[0] is True:
        return result[1]
    elif result[0] is 'Manual':
        return get_song_path(result[1], song, location)


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
        print song
        artists = get_artist_dir(song['artist'], artists, artist_dirs, song)
        artist_dir = artists[song['artist']]

        # we found the artist folder, now lets look for the album
        location = library + '/' + artist_dir
        albums = get_album_dir(song['album'], albums, song, location)
        album_dir = albums[song['artist']][song['album']]

        # we found the album folder, now lets look for the song
        location = location + "/" + album_dir + "/"
        song_path = get_song_path(song['name'], song, location)
        print song_path

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
    with open(output_filename, 'w') as file_:
        file_.write(output)

    return 1


def check_options(opts):
    """check all options"""
    output_filename = None
    input_filename = None
    library = None
    for opt, val in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)
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
        sys.exit(2)

    if not os.path.isfile(input_filename):
        print "input file is not found"
        usage()
        sys.exit(3)

    if not os.path.isdir(library):
        print "library is not found"
        usage()
        sys.exit(4)

    if output_filename is None:
        root = os.path.basename(input_filename)
        output_filename = root + '.m3u'

    if os.path.isfile(output_filename):
        print 'File', '"'+output_filename+'"', 'exists, overwrite?'
        answer = raw_input("Y/n ")
        if answer != '' and answer.lower() != 'y':
            print 'Aborting!'
            sys.exit(5)

    return (input_filename, output_filename, library)


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

    (input_filename, output_filename, library) = check_options(opts)

    return create_playlist(input_filename, output_filename, library)


if __name__ == "__main__":
    sys.exit(main())
