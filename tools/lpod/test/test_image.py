# -*- coding: UTF-8 -*-
#
# Copyright (c) 2009 Ars Aperta, Itaapy, Pierlis, Talend.
#
# Authors: Romain Gauthier <romain@itaapy.com>
#          Hervé Cauwelier <herve@itaapy.com>
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

# Import from the Standard Library
from unittest import TestCase, main

# Import from lpod
from lpod.document import odf_get_document
from lpod.element import LAST_CHILD, NEXT_SIBLING
from lpod.frame import odf_create_frame
from lpod.image import odf_create_image


class TestImage(TestCase):

    def setUp(self):
        self.document = document = odf_get_document('samples/frame_image.odp')
        self.body = document.get_body()
        self.path = 'Pictures/10000000000001D40000003C8B3889D9.png'


    def test_create_image(self):
        image = odf_create_image(self.path)
        expected = '<draw:image xlink:href="%s"/>' % self.path
        self.assertEqual(image.serialize(), expected)


    def test_get_image_list(self):
        body = self.body
        result = body.get_image_list()
        self.assertEqual(len(result), 1)
        element = result[0]
        self.assertEqual(element.get_attribute('xlink:href'), self.path)


    def test_get_image_by_name(self):
        body = self.body
        element = body.get_image_by_name(u"Logo")
        # Searched by frame but got the inner image with no name
        self.assertEqual(element.get_attribute('xlink:href'), self.path)


    def test_get_image_by_position(self):
        body = self.body
        element = body.get_image_by_position(0)
        self.assertEqual(element.get_attribute('xlink:href'), self.path)


    def test_get_image_by_path(self):
        body = self.body
        element = body.get_image_by_path('.png')
        self.assertEqual(element.get_attribute('xlink:href'), self.path)


    def test_insert_image(self):
        body = self.body.clone()
        path = 'a/path'
        image = odf_create_image(path)
        frame = odf_create_frame(u"Image Frame", size=('0cm', '0cm'),
                                 style='Graphics')
        frame.append_element(image)
        body.get_frame_by_position(0).insert_element(frame, NEXT_SIBLING)
        element = body.get_image_by_name(u"Image Frame")
        self.assertEqual(element.get_attribute('xlink:href'), path)
        element = body.get_image_by_position(1)
        self.assertEqual(element.get_attribute('xlink:href'), path)



if __name__ == '__main__':
    main()
