#!/usr/bin/env python
"UpdateZip script to change zip files"

from __future__ import print_function
import zipfile
import re
import zlib
import sys
import os
import getopt
import random

__uz_aliases = { 'delete': 'D', 'remove': 'D', 'del': 'D', 'rm': 'D',
                 'replace': 'U','update': 'U',
                 'add': 'A','new': 'A',
                 'rename': 'M', 'move': 'M', 'ren': 'M', 'mv': 'M',
                 'regex': 'R' }
__uz_params  = { 'D': 1,
                 'U': 2,
                 'A': 1,
                 'M': 2,
                 'R': 3 }
__uz_help = { 'D': """Command: DELETE file

Removes the file from the zip. The file is a regex expression allowing you
remove multiple files or a file which might change.

Aliases: REMOVE DEL RM""",
              'U': """Command: UPDATE file newfile

Replaces a file with one from the OS. The name and path inside the zip remain
the same as the one replaced.

Aliases: REPLACE""",
             'A': """Command: ADD file [path]

Adds a file from the OS putting it in path inside the zip. If a path is
provided it will be placed inside the zip at that path. If not path is provided
and the path is relative then the relative path is used. Otherwise the file is
put in the root.

Aliases: NEW""",
              'M': """Command: RENAME file newname

Renames the file from the zip. The file is a regex expression allowing you
change multiple files or a file which might change. Changes the path as well.

Aliases: MOVE REN MV""",
              'R': """Command: REGEX file search replace [flags]

Performs a regular expression search replace on the file.

Flags
 M multiline search, dot (.) matches newline characters as well
 U unicode
 I case insensitive search""" }

def print_help (command = None):
    "Display the help file"
    command = "main" if not command else command.lower()
    print("Usage: UpdateZip.py [options] zipfiles\n")
    if command in __uz_aliases:
        print(__uz_help[__uz_aliases[command]])
    else:
        print("""Options
 -h --help   this help file, use -h command for help on individual commands
 -n --name   name of zip file (defaults to reading from stdin)
 -d --dest   destination path (defaults to the same as the input file)
 -c --cmd    command to run (quoted, eg -c 'ADD myfile')
 -f --file   read commands from given file instead of the command line
             commands are processed in the order they appear

Commands
 DELETE file
 UPDATE file newfile
 ADD    file [path]
 RENAME file newname
 REGEX  file search replace [flags]""")

def replfn ( matchobj ):
    "function used by re.sub"
    print("Replacing %s with %s" % (matchobj.group(0),replfn.replace))
    return replfn.replace

# line2argv is lifted directly from cmdIn
# https://github.com/trentm/cmdln/blob/master/lib/cmdln.py
# License: MIT - (c) 2012 Trent Mick, 2002-2009 ActiveState Software Inc.
def line2argv(line):
    "Parse the given line into an argument vector handling quoting and escaping"
    line = line.strip()
    argv = []
    state = "default"
    arg = None  # the current argument being parsed
    i = -1
    WHITESPACE = '\t\n\x0b\x0c\r '  # don't use string.whitespace (bug 81316)
    while 1:
        i += 1
        if i >= len(line): break
        ch = line[i]

        if ch == "\\" and i+1 < len(line):
            # escaped char always added to arg, regardless of state
            if arg is None: arg = ""
            if (sys.platform == "win32"
                or state in ("double-quoted", "single-quoted")
               ) and line[i+1] not in tuple('"\''):
                arg += ch
            i += 1
            arg += line[i]
            continue

        if state == "single-quoted":
            if ch == "'":
                state = "default"
            else:
                arg += ch
        elif state == "double-quoted":
            if ch == '"':
                state = "default"
            else:
                arg += ch
        elif state == "default":
            if ch == '"':
                if arg is None: arg = ""
                state = "double-quoted"
            elif ch == "'":
                if arg is None: arg = ""
                state = "single-quoted"
            elif ch in WHITESPACE:
                if arg is not None:
                    argv.append(arg)
                arg = None
            else:
                if arg is None: arg = ""
                arg += ch
    if arg is not None:
        argv.append(arg)
    if not sys.platform == "win32" and state != "default":
        raise ValueError("command line is not terminated: unfinished %s "
                         "segment" % state)
    return argv

def compile_command(command):
    """command is a list of words passed in either from the command line argument or a file
so ren file newname would be ['ren','file','newname']"""
    compiled  = list()
    itemsused = 0

    c = command[0].lower()
    if c in __uz_aliases and len(command) > __uz_params[__uz_aliases[c]]:
        c1 = __uz_aliases[c]
        compiled.append(c1)
        if c1 == 'R': # Regex command
            compiled.append(re.compile(command[1]))
            compiled.append(command[2])
            compiled.append(command[3])
            itemsused = 4
        elif c1 == 'A': # Add command
            compiled.append(command[1])
            compiled.append(None) # TODO: allow overriding of name
            itemsused = 2
        elif c1 == 'D': # Delete command
            compiled.append(re.compile(command[1]))
            itemsused = 2
        elif c1 == 'U': # Update command
            compiled.append(re.compile(command[1]))
            compiled.append(command[2])
            itemsused = 3
        elif c1 == 'M': # Rename (move) command
            compiled.append(re.compile(command[1]))
            compiled.append(command[2])
            itemsused = 3

    return compiled , itemsused

def process_file (filename):
    "read in a file and process each command"
    commands = list()
    with open(filename) as commandsfile:
        for command in commandsfile:
            commands.append(compile_command(line2argv(command)))
    return commands

def process_zips ( jarfiles , commands , outfile = None ):
    """jarfiles  list of jar file to process
commands  regular expression for match files in the jar to
outfile   new filename path"""
    for jarfilename in jarfiles:
        if os.path.exists(jarfilename):
            print("Processing %s" % (jarfilename))
            newjar = outfile if outfile else jarfilename + str(random.random())
            jarin  = zipfile.ZipFile(jarfilename)
            jarout = zipfile.ZipFile(newjar,"w",zipfile.ZIP_DEFLATED)

            # process delete and regex commands
            for jfile in jarin.namelist():
                data = jarin.read(jfile)
                for command in commands:
                    if command[0] == 'A':
                        # Add files handled at end
                        continue
                    if command[1].match(jfile):
                        # execute command
                        if command[0] == 'D':
                            print("Deleting file %s from archive" % (jfile))
                            data = None
                        elif command[0] == 'R':
                            print("Running regex s&r on file %s" % (jfile))
                            replfn.replace = command[3]
                            data = re.sub(command[2],replfn,data)
                        elif command[0] == 'M':
                            print("Renaming %s to %s" % (jfile,command[2]))
                            jfile = command[2]
                        elif command[0] == 'U':
                            if os.path.isfile(command[2]):
                                print("Updating %s with %s" % (jfile,command[2]))
                                jarout.write(command[2],jfile)
                                data = None
                            else:
                                print("Unable to update %s - file %s not found" % (jfile,command[2]))
                if data:
                    jarout.writestr(jfile,data)

            # process add commands
            for command in commands:
                if command[0] == 'A':
                    if os.path.isfile(command[1]):
                        print("Adding file %s" % (command[1]))
                        jarout.write(command[1],command[2])

            jarout.close()
            jarin.close()
            if not outfile:
                os.remove(jarfilename)
                os.rename(newjar,jarfilename)
        else:
            print("Unable to find %s" % (jarfilename))

def main (inargs):
    filename = None
    newdest  = None
    commands = list()

    try:
        opts, args = getopt.getopt(inargs,"?hd:f:n:c:",["help","dest=","file=","name=","cmd="])
    except getopt.GetoptError:
        print_help()
        sys.exit()

    for opt, arg in opts:
        if opt in ("-h", "--help", "-?"):
            print_help(None if not args else args[0])
            sys.exit()
        elif opt in ("-n", "--name"):
            filename = arg
        elif opt in ("-c", "--cmd"):
            commands = [ compile_command(line2argv(arg)) ]
        elif opt in ("-d", "--dest"):
            newdest = arg
            if os.sep == arg[-len(os.sep):]:  # dest should be a dir
                if not os.path.isdir(arg):    # need to create the directory
                    os.mkdir(arg)
        elif opt in ("-f", "--file"):
            commands = process_file(arg)

    if commands:
        used = 0
    else:
        compiled , used  = compile_command(args)
        print(compiled)
        print(used)
        if compiled:
            commands.append(compiled)

    if filename: # -n --name argument passed
        process_zips([ filename ],commands,newdest)
    else: # use the rest of the command line
        process_zips(args[used:],commands,newdest)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print_help()

# EoF: updatezip.py
