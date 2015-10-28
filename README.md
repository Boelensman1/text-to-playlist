# text-to-playlist
A simple python script I wrote for converting a txt file to a m3u playlist. You can for example copy the html of a playlist from http://plex.tv and modify it using something like vim or sublime to match the template.

Then, if your music library is organized in the way this script expects (an iTunes library for example is) you can use the script to create a playlist that you can import in your favorite media player.

While doing this the script will ask you a question when it is not sure of something.

## Formatting of your library file
For the script to work your library should be organized in the following way: Artist / Album / Song.

If your music library is organized in a different way (but somewhat close) it should not be too difficult to change the script, the applicable lines are 150 and 175.

## Formatting of the .txt file
The text must be formatted in the following way:
```
Songname
Artist
Album
Length in minutes:seconds
whiteline
```

For example:
```
Shoot to Thrill
AC/DC
Back in Black
5:18
```

The last line of whitespace is significant. Every entry should have 4 lines.

## Usage
```
create_playlist.py [options]
-i --input    the input text file
-l --library  the library with the music files (required)
-o --output   the output m3u (optional, if omitted will
              print to console)
--help        shows this message
```

## Example
An example playlist has been added if you want to test the script, it can be found under example-files. Don't judge me on the choice of music, I have not made nor listened to it.

To convert this playlist you would use the following command:
```
./create_playlist.py -i ./example-files/playlist.txt -l /Volumes/Music -o playlist.m3u
```
