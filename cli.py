#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on

import readline
import os, sys
import json
import os.path
import subprocess
import traceback

from xmlrpclib    import ServerProxy, DateTime
from ConfigParser import ConfigParser
from optparse     import OptionParser
from datetime     import datetime
from getpass      import getuser
from cmd import Cmd

# First of all, let's do some option parsing, shall we?

parser = OptionParser(
    usage="""Usage: %prog [options] [<method> [<args...>]]

Each method argument has the form:
    [<data type: bool|int|float|string|json>:]value

If you do not specify a data type, string will be assumed, otherwise
`value' will be converted to the given type first. The bool conversion
interprets each of 'True', 'true', '1', 'Yes', 'yes' as True, everything
else as False. For the JSON parsing to work, the argument must be passed
as one single argument, including all spaces and special characters needed.

Example:
    int:4 float:3.5 string:oh:hai foobar bool:yes 'json:{ "a": "test" }'

In order to get a list of the available methods, run:
    %prog system.listMethods
"""
)

parser.add_option( "-v", "--verbose",
    help="Verbose output of messages.",
    action="store_true", default=False
    )

parser.add_option( "-c", "--command",
    help="A command to execute. The argument to this option will be parsed "
         "like a command line typed in the shell. If this option is used, all "
         "positional arguments on the shell will be ignored.",
    default=""
    )

parser.add_option( "-C", "--connect",
    help="An URL to connect to.",
    default="http://localhost:31234/"
    )

parser.add_option( "-u", "--uidcheck",
    help="If not logged in as root, make sure the current user is a superuser "
         "before doing anything.",
    action="store_true", default=False
    )

parser.add_option( "-o", "--outformat",
    help="Output format. Default is JSON if interactive, shell otherwise.",
    default=None
    )

parser.add_option( "-f", "--outfield",
    help="Output the given field only. You can query nested fields by specifying "
         "them in a dotted notation, e.g. 'fs.stat.free'.",
    default=None
    )

parser.add_option( "-e", "--encoding",
    help="Character set arguments are encoded in. Default: Read from LANG env "
         "variable with fallback to UTF-8.",
    default=None
    )

options, progargs = parser.parse_args()

conf = ConfigParser()
confs = conf.read(["/etc/openattic-cli.conf", os.path.expanduser("~/.openattic-cli.conf")])

if sys.stdout.isatty():
    print >> sys.stderr, "Initialized config from %s" % ', '.join(confs)

for key in options.__dict__:
    if getattr(options, key) == parser.defaults[key] and conf.has_option("options", key):
        setattr(options, key, conf.get("options", key))

# Make sure we have an encoding defined
if options.encoding is None:
    try:
        locale = os.environ['LANG']
        _, options.encoding = locale.split('.')
    except (KeyError, ValueError):
        options.encoding = "UTF-8"

# See if there's a hosts section that re-defines our connstring
if conf.has_section("hosts") and conf.has_option("hosts", options.connect):
    options.connect = conf.get("hosts", options.connect)

# Try to connect to the given server.
if options.verbose:
    print >> sys.stderr, "Connecting..."

server = ServerProxy(options.connect, allow_none=True)
try:
    server.ping()
except Exception, e:
    sys.exit("Could not connect to the server: " + unicode(e))

# Retrieve hostname from the server
hostname = server.hostname()


if options.uidcheck and os.geteuid() != 0:
    user = server.auth.User.filter({"username": getuser()})
    if len(user) != 1 or not user[0]['is_superuser']:
        sys.exit("Access denied, sorry mate.")


# Check if using colors on stdout is sensible
if sys.stdout.isatty():
    # Readline escape: \001 = Beginning of non-printable character section, \002 = end
    # \033 = ESC
    HOSTCOLOR = '\001\033[1;32m\002'
    SECTCOLOR = '\001\033[1;34m\002'
    CLRCOLOR  = '\001\033[0m\002'
else:
    HOSTCOLOR = SECTCOLOR = CLRCOLOR = ""

def hostcolorize(text):
    return HOSTCOLOR + text + CLRCOLOR

def sectcolorize(text):
    return SECTCOLOR + text + CLRCOLOR



# Output formatters that turn whatever the server returns into useful shell output
def out_shell(something):
    lines = []
    if isinstance(something, list):
        for item in something:
            lines.append(unicode(item))
    elif isinstance(something, dict):
        for key in something:
            lines.append("%s='%s'" % (key, something[key]))
    else:
        lines.append(unicode(something))
    return "\n".join(lines)

def json_format(something):
    if isinstance(something, DateTime):
        # This is a DateTime object from xmlrpclib. Convert to a standard datetime.
        something = datetime( *something.timetuple()[:6] )
    if hasattr(something, 'isoformat'):
        return something.isoformat()
    return json.dumps(something)

formatters = {
    'json':  lambda something: json.dumps(something, indent=4, default=json_format),
    'shell': out_shell
    }



# Argument line parser
def shlox( line, escape='\\', comment='#', sep=(' ', '\t', '\r', '\n' ) ):
    """ State machine that parses stuff like bash does, with the additional benefit of also
        being able to parse JSON for more complex arguments.
    """
    ST_NORMAL, ST_ESCAPE, ST_SINGLE_QUOTED, ST_DOUBLE_QUOTED, ST_DOUBLE_ESCAPE, ST_JSON_DICT, ST_JSON_LIST = range(7)

    state = ST_NORMAL
    bracelevel = 0

    word  = ''
    empty = True

    for char in line:
        if   state == ST_NORMAL:
            if   char == escape:
                state = ST_ESCAPE
            elif char == '"':
                empty = False
                state = ST_DOUBLE_QUOTED
            elif char == "'":
                empty = False
                state = ST_SINGLE_QUOTED
            elif char == '{' and empty:
                empty = False
                state = ST_JSON_DICT
                bracelevel = 0
                word += char
            elif char == '[' and empty:
                empty = False
                state = ST_JSON_LIST
                bracelevel = 0
                word += char
            elif char == comment:
                if empty:
                    raise StopIteration
                else:
                    word += char
            elif char in sep:
                if not empty:
                    yield word
                    empty = True
                    word  = ''
            else:
                empty = False
                word += char

        elif state == ST_ESCAPE:
            word += char
            state = ST_NORMAL

        elif state == ST_SINGLE_QUOTED:
            if   char == "'":
                state = ST_NORMAL
            else:
                word += char

        elif state == ST_DOUBLE_QUOTED:
            if   char == escape:
                state = ST_DOUBLE_ESCAPE
            elif char == '"':
                state = ST_NORMAL
            else:
                word += char

        elif state == ST_DOUBLE_ESCAPE:
            if   char in ( escape, comment, '"', "'" ) + sep:
                word += char
            else:
                word += '\\' + char
            state = ST_DOUBLE_QUOTED

        elif state == ST_JSON_DICT:
            word += char
            if char == '{':
                bracelevel += 1
            elif char == '}':
                if bracelevel > 0:
                    bracelevel -= 1
                else:
                    yield json.loads(word)
                    empty = True
                    word  = ''
                    state = ST_NORMAL

        elif state == ST_JSON_LIST:
            word += char
            if char == '[':
                bracelevel += 1
            elif char == ']':
                if bracelevel > 0:
                    bracelevel -= 1
                else:
                    yield json.loads(word)
                    empty = True
                    word  = ''
                    state = ST_NORMAL

    if state != ST_NORMAL:
        raise ValueError( "Unclosed quote or \\ at end of line." )

    elif not empty:
        yield word




def clean_args(args):
    """ Clean the arguments that have been passed to us on the shell, by converting
        them to the correct data type and making sure they are decoded correctly.
    """
    cleanargs = []
    for param in args:
        if isinstance( param, (list, dict) ):
            cleanargs.append(param)
            continue
        try:
            argtype, argval = param.split(':', 1)
        except ValueError:
            cleanargs.append( param.decode(options.encoding) )
        else:
            cleanval = {
                'bool':   lambda val: val in ('True', 'true', '1', 'Yes', 'yes'),
                'int':    int,
                'float':  float,
                'string': str,
                'json':   json.loads,
                }[ argtype ]( argval )

            if argtype == 'string':
                cleanval = cleanval.decode(options.encoding)
            cleanargs.append(cleanval)
    return cleanargs


def call(sectname, cmd, args):
    """ Handle a command which needs to be mapped to an XMLRPC function call. """
    if sectname:
        handler = getattr( server, sectname )
        fullname = '%s.%s' % (sectname, cmd)
    else:
        handler  = server
        fullname = cmd
    func = getattr( handler, cmd )

    argspec = server.get_function_args( fullname )
    args = clean_args(args)

    if( len(args) != len(argspec) ):
        print "Usage: %s %s" % ( fullname, ' '.join([('<%s>' % a) for a in argspec]) )
    else:
        try:
            result = func(*args)
            if options.outfield:
                for field in options.outfield.split('.'):
                    result = result[field]
            formatted = formatters[options.outformat](result)
            print formatted.encode(options.encoding)
        except Exception, e:
            print >> sys.stderr, "Error processing the command:", unicode(type(e)), unicode(e)
            if options.verbose:
                traceback.print_exc()


def call_argstr(sectname, cmd, argstr):
    """ Parse the given argstr into a list, then call() the method given in cmd. """
    stripped = argstr.strip()
    if stripped:
        try:
            parsed = list(shlox(stripped))
        except Exception, e:
            print >> sys.stderr, "Error when parsing command line:", unicode(e)
            if options.verbose:
                traceback.print_exc()
        else:
            return call(sectname, cmd, parsed)
    else:
        return call(sectname, cmd, [])


if options.command:
    progargs = list(shlox(options.command))

if progargs:
    # handle the command given on the shell and exit.
    if not options.outformat:
        options.outformat = "shell"
    parts = progargs[0].rsplit('.', 1)
    if len(parts) == 2:
        section, cmd = parts
    else:
        section = ""
        cmd = parts[0]
    if parts[0] == "system":
        if parts[1] == "listMethods":
            formatted = formatters[options.outformat]( server.system.listMethods() )
        elif parts[1] == "methodHelp":
            formatted = formatters[options.outformat]( server.system.methodHelp(*clean_args(progargs[1:])) )
        elif parts[1] == "methodSignature":
            formatted = formatters[options.outformat]( server.system.methodSignature(*clean_args(progargs[1:])) )
        else:
            sys.exit("Command 'system'.'%s' is not defined." % parts[1])
        print formatted.encode(options.encoding)
    else:
        call(section, cmd, progargs[1:])

else:
    # No command given → interactive mode.

    if not options.outformat:
        options.outformat = "json"

    # Load command history, if possible
    if sys.stdin.isatty() and "HOME" in os.environ and os.environ["HOME"]:
        try:
            readline.read_history_file( os.path.join( os.environ["HOME"], '.oacli_history' ) )
        except Exception, e:
            print >> sys.stderr, "Error loading the history file:", unicode(e)
            if options.verbose:
                traceback.print_exc()



    class BaseCommand(Cmd, object):
        """ Implements basic functions of each shell section. """

        def _shellcmd(self, cmd, argstr):
            """ Run a system shell command, passing all signals to it that are received. """
            stripped = argstr.strip()
            if stripped:
                try:
                    args = [cmd] + list(shlox(stripped))
                except Exception, e:
                    print >> sys.stderr, "Error when parsing command line:", unicode(e)
                    if options.verbose:
                        traceback.print_exc()
            else:
                args = [cmd]

            if options.verbose:
                print " ".join(args)
            from signal import signal, SIGTERM, SIGINT, SIG_DFL, default_int_handler

            proc = subprocess.Popen(args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

            def fwdsigterm(signum, frame):
                proc.send_signal(SIGTERM)
                signal(SIGTERM, fwdsigterm)

            signal(SIGTERM, fwdsigterm)
            signal(SIGINT, fwdsigterm)
            proc.wait()
            signal(SIGTERM, SIG_DFL)
            signal(SIGINT, default_int_handler)
            return proc.returncode

        def help_syntax(self):
            print  ("""Syntax in this shell:\n"""
                    """\n"""
                    """ command [arguments ...]\n"""
                    """\n"""
                    """Arguments may be enclosed in double or single quotes in order to keep\n"""
                    """white space, whereas in double quotes, the quotes themselves can be added\n"""
                    """by escaping them. So, "hello \\"friend\\"" will be parsed to 'hello "friend"',\n"""
                    """while 'hello \\'friend\\'' is a syntax error.\n"""
                    """\n"""
                    """In cases where lists or dictionaries need to be passed, enter them\n"""
                    """as JSON like so:\n"""
                    """ command some "other args" {"key": "value", 13: 37}\n"""
                    """ command some "other args" ["value", 1, 2, 3]\n"""
                    """\n"""
                    """Beware though that JSON does not support strings enclosed in single quotes.\n"""
                    """\n"""
                    """The shell is organized in sections, each section containing a distinct set\n"""
                    """of commands. The ``help'' command will list commands that exist in each\n"""
                    """section, and if called with a command name as its first argument, it displays\n"""
                    """some information about that command.\n"""
                    """\n"""
                    """If you enter a partial command name, pressing the tab key will auto-complete\n"""
                    """the command name if possible. Pressing it twice will show available options.\n"""
                    """\n"""
                    """To leave a section, you can either use the exit command, or hit ^d. To quit\n"""
                    """the shell altogether, do the same on the root section (#).\n""")

        def do_end(self, args):
            """ Leave this section (or the shell altogether if in the highest section). """
            # see postcmd()
            pass

        def do_exit(self, args):
            """ Quit the shell. """
            print "Bye."
            sys.exit(0)

        def precmd(self, line):
            """ If the line starts with a comment, ignore it. """
            if line.strip().startswith('#'):
                return ''
            if line == "EOF":
                return "exit"
            if line == "..":
                return "end"
            return line

        def emptyline(self):
            # srsly what the fuck - by default, Cmd repeats the last command if the line is empty...
            pass

        def postcmd(self, stop, line):
            """ Check if the last command was an exit command. If so exit, otherwise add it to the history. """
            if line in ("end", "EOF"):
                return True
            #if line:
                #readline.add_history(line)
            return False

        def enter_subsection(self, name, args):
            """ Check if we have an attribute named subsection_<name>, and if so,
                execute it as a subshell.
            """
            subsect = getattr(self, 'subsection_'+name, None)()
            if subsect is not None:
                if args:
                    return subsect.onecmd(args)
                while True:
                    try:
                        subsect.cmdloop()
                    except KeyboardInterrupt:
                        # Eat this exception. I want to be able to hit ^c to cancel typing stuff, so just...
                        print '^C' # and restart the shell.
                    else:
                        # Subshell terminated normally, so break the while loop.
                        break


    # You are SO gonna hate me. If you don't already. Brace yourself, lots'a closures ahead.

    def buildCallFunction(cmd, prevparts):
        """ Create a wrapper function around call_argstr(). Prevparts contains
            the section names, cmd is the command name, args will be passed at runtime.
        """
        def do_cmd(self, args):
            return call_argstr( '.'.join(prevparts), cmd, args )
        do_cmd.__name__ = 'do_'+cmd
        return do_cmd

    def buildHelpFunction(cmd, prevparts):
        """ Create a function that prints help text for the given command by
            requesting the Docstring of the exported function from the server.
        """
        fullname = '.'.join(prevparts + [cmd])
        def help_cmd(self):
            argspec = server.get_function_args( fullname )
            print server.system.methodHelp( fullname )
            print "Usage: %s %s" % ( fullname, ' '.join([('<%s>' % a) for a in argspec]) )
        help_cmd.__name__ = 'help_'+cmd
        return help_cmd


    def buildSubSectionWrapper(name, prevparts):
        """ Create a wrapper function around enter_subsection to change the shell in foreground. """
        def do_cmd(self, args):
            return self.enter_subsection(name, args)
        do_cmd.__name__ = 'do_'+name
        do_cmd.__doc__  = ("Enter section '%s'." % '.'.join(prevparts + [name]))
        return do_cmd


    def buildShellSection(name, prevparts, methods):
        """ Creates a BaseCommand sub*class* that implements a shell section.

            The methods dict specified what commands are to exist here. Non-empty values
            mean subsections, empty values mean commands.
        """
        attrs = {
            'prompt': "%s:%s> " % ( hostcolorize(hostname), sectcolorize('.'.join(prevparts)) ),
            }
        for cmd in methods:
            if methods[cmd]: # value is non-empty → section
                attrs['subsection_'+cmd] = buildShellSection(cmd, prevparts+[cmd], methods[cmd])
                attrs['do_'+cmd]   = buildSubSectionWrapper(cmd, prevparts)
            else:            # value is empty → command
                attrs['do_'+cmd]   = buildCallFunction(cmd, prevparts)
                attrs['help_'+cmd] = buildHelpFunction(cmd, prevparts)

        return type('Cmd'+name, (BaseCommand, ), attrs)


    # Build a method tree structure to build the shell from. The structure looks like:
    # { 'lvm': { 'LogicalVolume': { 'add': {},
    #                               'get': {} },
    #            'VolumeGroup': { 'add': {},
    #                             'get': {} } },
    #   'nfs': { 'Export': { 'add': {},
    #                        'get': {} } }
    # }
    # That is, each key with a non-empty value will become a section, others will be commands.
    methods = {}
    for method in server.system.listMethods():
        container = methods
        for part in method.split('.'):
            if part not in container:
                container[part] = {}
            container = container[part]

    if options.verbose:
        print >> sys.stderr, "Building shell..."

    MainSection = buildShellSection("main", [], methods)

    class ShellMain(MainSection):
        """ The actual main section of the shell. Inherits generated stuff from MainSection. """
        prompt = "%s:%s> " % ( hostcolorize(hostname), sectcolorize('#') )

        def do_shell( self, args ):
            """ Enter section 'shell'. """
            return self.enter_subsection("shell")

        class subsection_shell(BaseCommand):
            """ The 'shell' subsection handler. """
            prompt = "%s:%s> " % ( hostcolorize(hostname), sectcolorize('shell') )

            def do_outformat(self, args):
                """ Display and switch the output format of the running shell. """
                args = args.strip()
                if not args:
                    print options.outformat
                elif args in formatters:
                    options.outformat = args
                else:
                    print >> sys.stderr, ("Invalid arguments, must be one of '%s'." % "', '".join(formatters.keys()))

            def do_verbose(self, args):
                args = args.strip()
                if not args:
                    print options.verbose
                else:
                    options.verbose = (args.lower() == "true")

            def do_history(self, args):
                """ Display the command history. """
                for i in range(readline.get_current_history_length()):
                    print readline.get_history_item(i)

            def do_clear_history(self, args):
                """ Clears the command history (warning: no confirmation or backup!). """
                readline.clear_history()

            def do_man(self, args):
                """ The 'man' shell command. """
                return self._shellcmd('man', args)

            def do_cat(self, args):
                """ The 'cat' shell command. """
                return self._shellcmd('cat', args)

            def do_bash(self, args):
                """ Start a bash shell. (Staff and root only.) """
                if os.geteuid() != 0:
                    user = server.auth.User.filter({"username": getuser()})
                    if len(user) != 1 or not user[0]['is_staff']:
                        print >> sys.stderr, "Access denied, sorry mate."
                        return
                return self._shellcmd("bash", args)

        class subsection_system(BaseCommand):
            """ The "system" section handler.

                The automatically generated system section causes the server proxy to fail somehow.
            """
            prompt = "%s:%s> " % ( hostcolorize(hostname), sectcolorize('system') )
            def do_listMethods(self, args):
                print formatters[options.outformat]( server.system.listMethods() )

            def do_methodHelp(self, args):
                print formatters[options.outformat]( server.system.methodHelp( args.strip() ) )

            def do_methodSignature(self, args):
                print formatters[options.outformat]( server.system.methodSignature( args.strip() ) )

    main = ShellMain()

    while True:
        try:
            main.cmdloop()
        except KeyboardInterrupt:
            # Eat this exception. I want to be able to hit ^c to cancel typing stuff, so just...
            print '^C' # and restart the shell.
        else:
            # Subshell terminated normally, so break the while loop.
            break

    # Write the history file, if possible
    if sys.stdin.isatty() and "HOME" in os.environ and os.environ["HOME"]:
        try:
            readline.write_history_file( os.path.join( os.environ["HOME"], '.oacli_history' ) )
        except Exception, e:
            print >> sys.stderr, "Error writing the history file:", unicode(e)
            if options.verbose:
                traceback.print_exc()
