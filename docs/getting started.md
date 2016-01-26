Installation
------------

There is just a single script which just relies of the standard Python library,
hence no requirements.txt file. The script works on both Linux/Unix, MacOS and
Windows machines.

If you copy the script to a folder in your path your can run it with
updatezip.py

If you want to include the functionality in your own Python program simply copy
to the same directory as your Python program and include the command
import updatezip

Options
-------

-h --help   this help file, use -h command for help on individual commands

-n --name   name of zip file (defaults to reading from stdin)

-d --dest   destination path (defaults to the same as the input file)

-c --cmd    command to run (quoted, eg -c 'ADD myfile')

-f --file   read commands from given file instead of the command line
            commands are processed in the order they appear

Commands
--------

DELETE file

UPDATE file newfile

ADD    file [path]

RENAME file newname

REGEX  file search replace [flags]

Unfortunately the optional parameters, [path] in ADD and [flags] in REGEX are
not implemented yet