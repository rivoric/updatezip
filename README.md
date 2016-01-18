UpdateZip
---------

The inspiration for this utility came when I needed to programatically change environment variables inside a jar file
(which is just a zip file with a different name).
Over time additional requests came in and this is an attempt to properly flesh out that functional requirement.
The functionality is provided by a series of commands that tell the script what to do.

The commands currently supported are
- DELETE file
- UPDATE file newfile
- ADD    file [path]
- RENAME file newname
- REGEX  file search replace [flags]

For simple manipulations, a single command can be provided at the command line.
For more powerful changes a script can to specified which list each command on a seperate line.

For usage, please see the in-built help.