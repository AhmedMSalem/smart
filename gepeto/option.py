#
# Copyright (c) 2004 Conectiva, Inc.
#
# Written by Gustavo Niemeyer <niemeyer@conectiva.com>
#
# This file is part of Gepeto.
#
# Gepeto is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Gepeto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gepeto; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
from gepeto import Error
import optparse
import textwrap
import sys, os

__all__ = ["OptionParser", "OptionValueError", "append_all"]

OptionValueError = optparse.OptionValueError

class HelpFormatter(optparse.HelpFormatter):

    def __init__(self):
        optparse.HelpFormatter.__init__(self, 2, 24, 79, 1)

    def format_usage(self, usage):
        return "Usage: %s\n" % usage

    def format_heading(self, heading):
        return "\n%*s%s:\n" % (self.current_indent, "", heading.capitalize())

    def format_description(self, description):
        return description.strip()

    def format_option(self, option):
        help = option.help
        if help:
            option.help = help.capitalize()
        result = optparse.HelpFormatter.format_option(self, option)
        option.help = help
        return result

class OptionParser(optparse.OptionParser):

    def __init__(self, usage=None, help=None, examples=None, **kwargs):
        if not "formatter" in kwargs:
            kwargs["formatter"] = HelpFormatter()
        optparse.OptionParser.__init__(self, usage, **kwargs)
        self._override_help = help
        self._examples = examples

    def format_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        if self._override_help:
            result = self._override_help.strip()
            result += "\n"
        else:
            result = optparse.OptionParser.format_help(self, formatter)
            result = result.strip()
            result += "\n"
            if self._examples:
                result += formatter.format_heading("examples")
                formatter.indent()
                for line in self._examples.strip().splitlines():
                    result += " "*formatter.current_indent
                    result += line+"\n"
                formatter.dedent()
        result += "\n"
        return result

    def error(self, msg):
        raise Error, msg

def append_all(option, opt, value, parser):
    if option.dest is None:
        option.dest = opt
        while option.dest[0] == "-":
            option.dest = option.dest[1:]
    dest = option.dest.replace("-", "_")
    lst = getattr(parser.values, dest)
    if type(lst) is not list:
        lst = []
        setattr(parser.values, dest, lst)
    rargs = parser.rargs
    while rargs and rargs[0] and rargs[0][0] != "-":
        lst.append(parser.rargs.pop(0))


# vim:et:ts=4:sw=4
