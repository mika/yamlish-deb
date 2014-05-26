# -*- coding: utf-8 -*-
#Copyright (C) 2012 Red Hat, Inc.
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
"""
Easy YAML serialisation compatible with TAP format.

Port of `Data::YAML Perl module <https://github.com/AndyA/Data--YAML>`,
satisfying all its tests, intended to be used for support of
`TAP <http://testanything.org/>` data format. Port of the original
documentation follows.

The syntax accepted by this module is a subset of `YAML <http://yaml.org>`.

===========
YAML syntax
===========

Although YAML appears to be a simple language, the entire YAML
specification is huge. This module implements a small subset of the
complete syntax trading completeness for compactness and simplicity.
This restricted syntax is known (to me at least) as 'YAMLish'.

These examples demonstrates the full range of supported syntax.

All YAML documents must begin with '---' and end with a line
containing '...'.

::

    --- Simple scalar
    ...

Unprintable characters are represented using standard escapes in double
quoted strings.

::

    --- "\\t\\x01\\x02\\n"
    ...

Array and hashes are represented thusly

::

    ---
      - "This"
      - "is"
      - "an"
      - "array"
    ...

    ---
      This: is
      a: hash
    ...

Structures may nest arbitrarily

::

    ---
      -
        name: 'Hash one'
        value: 1
      -
        name: 'Hash two'
        value: 2
    ...

Undef is a tilde

::

    --- ~
    ...

====
Uses
====

This module may be used any time you need to freeze and thaw Python
data structures into a human readable format. The output from
`yamlish.dump()` should be readable by any YAML parser.

The original Perl module was originally written to allow machine-readable
diagnostic information to be passed from test scripts to
the Perl module `TAP::Harness`. That means that if you're writing
a testing system that needs to output TAP version 13 or later
syntax you might find this module useful.

Read more about TAP and YAMLish on `<http://testanything.org/wiki>`

"""
from __future__ import absolute_import, print_function, unicode_literals
import logging
import yaml

__docformat__ = 'reStructuredText'
__version__ = "0.10"
__author__ = u"Matěj Cepl <mcepl_at_redhat_dot_com>"

class _YamlishLoader(yaml.loader.SafeLoader):
    """
    Remove a datetime resolving.

    YAMLish returns unchanged string.
    """
    def __init__(self, stream):
        yaml.loader.SafeLoader.__init__(self, stream)

    @classmethod
    def remove_implicit_resolver(cls, tag):
        """
        Remove an implicit resolver from a Loader class identified by its tag.
        """
        if not 'yaml_implicit_resolvers' in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()
        for key in cls.yaml_implicit_resolvers:
            resolvers_set = cls.yaml_implicit_resolvers[key]
            for idx in range(len(resolvers_set)):
                if resolvers_set[idx][0] == tag:
                    del resolvers_set[idx]
            if len(resolvers_set) == 0:
                del cls.yaml_implicit_resolvers[key]

_YamlishLoader.remove_implicit_resolver(u'tag:yaml.org,2002:timestamp')

class _YamlishDumper(yaml.dumper.SafeDumper):
    pass

def str_representer_compact_multiline(dumper, data):
    style = None
    if '\n' in data:
        style = '|'
    if isinstance(data, str):
        data = data.decode('utf-8') # assumes all your strings are UTF-8 encoded
    tag = u'tag:yaml.org,2002:str'
    return dumper.represent_scalar(tag, data, style)

yaml.add_representer(str, str_representer_compact_multiline,
                     Dumper=_YamlishDumper)
yaml.add_representer(unicode, str_representer_compact_multiline,
                     Dumper=_YamlishDumper)

def load(source):
    """
    Return object loaded from a YAML document in source.

    Source is either a representation of the YAML document itself
    or any document providing an iterator (that includes file, list, and
    many others).
    """
    out = None
    logging.debug("inobj:\n%s", source)
    if isinstance(source, (str, unicode)):
        out = yaml.load(source, Loader=_YamlishLoader)
        logging.debug("out (string) = %s", out)
    elif hasattr(source, "__iter__"):
        inobj = ""
        for line in source:
            inobj += line + '\n'
        out = load(inobj)
        logging.debug("out (iter) = %s", out)
    return out

def dump(source, destination):
    """
    Store source in destination file.

    Destination is either a file object or a string with a filename.
    """
    if isinstance(destination, (str, unicode)):
        with open(destination, "w") as outf:
            dump(source, outf)
    elif hasattr(destination, "fileno"):
        yaml.dump(source, destination, encoding="utf-8",
                  default_flow_style=False, canonical=False,
                  Dumper=_YamlishDumper)
    else:
        raise NameError

def dumps(source):
    """
    Return YAMLish string from given source.
    """
    return yaml.dump(source, encoding="utf-8",
                     explicit_start=True, explicit_end=True,
                     default_flow_style=False, default_style=False,
                     canonical=False, Dumper=_YamlishDumper)
