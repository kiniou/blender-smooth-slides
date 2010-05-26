#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright (c) 2009 Ars Aperta, Itaapy, Pierlis, Talend.
#
# Authors: Hervé Cauwelier <herve@itaapy.com>
#          Romain Gauthier <romain@itaapy.com>
#
# This file is part of Lpod (see: http://lpod-project.org).
# Lpod is free software; you can redistribute it and/or modify it under
# the terms of either:
#
# a) the GNU General Public License as published by the Free Software
#    Foundation, either version 3 of the License, or (at your option)
#    any later version.
#    Lpod is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU General Public License
#    along with Lpod.  If not, see <http://www.gnu.org/licenses/>.
#
# b) the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
#

# Import from the standard library
from optparse import OptionParser
from sys import exit, stdout

# Import from lpod
from lpod import __version__
from lpod.document import odf_get_document


def show_styles(document, automatic=True, common=True, properties=False):
    """Show the different styles of a document and their properties.
    """
    output = document.show_styles(automatic=automatic, common=common,
            properties=properties)
    # Print the styles
    encoding = stdout.encoding if stdout.encoding is not None else 'utf-8'
    stdout.write(output.encode(encoding))
    stdout.flush()



def delete_styles(document, pretty=True):
    n = document.delete_styles()
    document.save(pretty=pretty)
    print n, "styles removed (0 error, 0 warning)."



def merge_styles(document, from_file, pretty=True):
    source = odf_get_document(from_file)
    document.delete_styles()
    document.merge_styles_from(source)
    document.save(pretty=pretty)
    print "Done (0 error, 0 warning)."



if  __name__ == '__main__':
    # Options initialisation
    usage = '%prog <file>'
    description = 'A command line interface to manipulate styles of ' \
                  'OpenDocument files.'
    parser = OptionParser(usage, version=__version__,
            description=description)
    # --automatic
    parser.add_option('-a', '--automatic', dest='automatic',
            action='store_true', default=False,
            help="show automatic styles only")
    # --common
    parser.add_option('-c', '--common', dest='common', action='store_true',
            default=False, help="show common styles only")
    # --properties
    parser.add_option('-p', '--properties', dest='properties',
            action='store_true', help="show properties of styles")
    # --delete
    parser.add_option('-d', '--delete', dest='delete',
            action='store_true', help="delete all styles (except default)")
    # --merge
    help = ('copy styles from FILE to <file>. Any style with the same name '
            'will be replaced.')
    parser.add_option('-m', '--merge-styles-from', dest='merge',
            action='store', metavar='FILE', help=help)
    # Parse options
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        exit(1)
    document = odf_get_document(args[0])
    if options.delete:
        delete_styles(document)
    elif options.merge:
        merge_styles(document, options.merge)
    else:
        automatic = options.automatic
        common = options.common
        if not automatic ^ common:
            automatic, common = True, True
        show_styles(document, automatic=automatic, common=common,
                properties=options.properties)
