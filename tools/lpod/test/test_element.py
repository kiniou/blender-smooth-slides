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
from re import compile

# Import from lpod
from lpod.container import odf_get_container
from lpod.element import odf_create_element, odf_element
from lpod.element import FIRST_CHILD, NEXT_SIBLING, PREV_SIBLING
from lpod.xmlpart import odf_xmlpart


class CreateElementTestCase(TestCase):

    def test_simple(self):
        data = '<p>Template Element</p>'
        element = odf_create_element(data)
        self.assertEqual(element.serialize(), data)


    def test_namespace(self):
        data = '<text:p>Template Element</text:p>'
        element = odf_create_element(data)
        self.assertEqual(element.serialize(), data)



class ElementTestCase(TestCase):

    def setUp(self):
        container = odf_get_container('samples/example.odt')
        self.container = container
        self.content_part = content_part = odf_xmlpart('content', container)
        self.paragraph_element = content_part.get_element('//text:p[1]')
        self.annotation_element = (
                content_part.get_element('//office:annotation[1]'))


    def tearDown(self):
        del self.annotation_element
        del self.paragraph_element
        del self.content_part
        del self.container


    def test_bad_python_element(self):
        self.assertRaises(TypeError, odf_element, '<text:p/>')


    def test_get_element_list(self):
        content_part = self.content_part
        elements = content_part.get_element_list('//text:p')
        # The annotation paragraph is counted
        self.assertEqual(len(elements), 8)


    def test_get_name(self):
        element = self.paragraph_element
        self.assertEqual(element.get_tagname(), 'text:p')


    def test_clone(self):
        element = self.paragraph_element
        copy = element.clone()
        self.assertNotEqual(id(element), id(copy))
        self.assertEqual(element.get_text(), copy.get_text())


    def test_delete(self):
        element = odf_create_element('<a><b/></a>')
        child = element.get_element('//b')
        element.delete_element(child)
        self.assertEqual(element.serialize(), '<a/>')



class ElementAttributeTestCase(TestCase):

    special_text = 'using < & " characters'


    def setUp(self):
        container = odf_get_container('samples/example.odt')
        self.container = container
        content_part = odf_xmlpart('content', container)
        self.paragraph_element = content_part.get_element('//text:p[1]')


    def test_get_attributes(self):
        element = self.paragraph_element
        attributes = element.get_attributes()
        excepted = {'text:style-name': "Text_20_body"}
        self.assertEqual(attributes, excepted)


    def test_get_attribute(self):
        element = self.paragraph_element
        unknown = element.get_attribute('style-name')
        self.assertEqual(unknown, None)


    def test_get_attribute_namespace(self):
        element = self.paragraph_element
        text = element.get_attribute('text:style-name')
        self.assert_(isinstance(text, unicode))
        self.assertEqual(text, "Text_20_body")


    # XXX The same than test_get_attribute?
    def test_get_attribute_none(self):
        element = self.paragraph_element
        dummy = element.get_attribute('and_now_for_sth_completely_different')
        self.assertEqual(dummy, None)


    def test_set_attribute(self):
        element = self.paragraph_element
        element.set_attribute('test', "a value")
        self.assertEqual(element.get_attribute('test'), "a value")
        element.del_attribute('test')


    def test_set_attribute_namespace(self):
        element = self.paragraph_element
        element.set_attribute('text:style-name', "Note")
        self.assertEqual(element.get_attribute('text:style-name'), "Note")
        element.del_attribute('text:style-name')


    def test_set_attribute_special(self):
        element = self.paragraph_element
        element.set_attribute('test', self.special_text)
        self.assertEqual(element.get_attribute('test'), self.special_text)
        element.del_attribute('test')


    def test_del_attribute(self):
        element = self.paragraph_element
        element.set_attribute('test', "test")
        element.del_attribute('test')
        self.assertEqual(element.get_attribute('test'), None)


    def test_del_attribute_namespace(self):
        element = self.paragraph_element
        element.set_attribute('text:style-name', "Note")
        element.del_attribute('text:style-name')
        self.assertEqual(element.get_attribute('text:style-name'), None)



class ElementTextTestCase(TestCase):

    special_text = 'using < & " characters'


    def setUp(self):
        container = odf_get_container('samples/example.odt')
        self.container = container
        content_part = odf_xmlpart('content', container)
        self.annotation_element = (
                content_part.get_element('//office:annotation[1]'))
        self.paragraph_element = content_part.get_element('//text:p[1]')


    def test_get_text(self):
        element = self.paragraph_element
        text = element.get_text()
        self.assertEqual(text, u"This is the first paragraph.")


    def test_set_text(self):
        element = self.paragraph_element
        old_text = element.get_text()
        new_text = u'A test'
        element.set_text(new_text)
        self.assertEqual(element.get_text(), new_text)
        element.set_text(old_text)
        self.assertEqual(element.get_text(), old_text)


    def test_set_text_special(self):
        element = self.paragraph_element
        old_text = element.get_text()
        element.set_text(self.special_text)
        self.assertEqual(element.get_text(), self.special_text)
        element.set_text(old_text)


    def test_get_text_content(self):
        element = self.annotation_element
        text = element.get_text_content()
        self.assertEqual(text, u"This is an annotation.")


    def test_set_text_content(self):
        element = self.annotation_element
        old_text = element.get_text_content()
        text = u"Have a break"
        element.set_text_content(text)
        self.assertEqual(element.get_text_content(), text)
        element.set_text_content(old_text)
        self.assertEqual(element.get_text_content(), old_text)



class ElementTraverseTestCase(TestCase):

    def setUp(self):
        container = odf_get_container('samples/example.odt')
        self.container = container
        self.content_part = content_part = odf_xmlpart('content', container)
        self.annotation_element = (
                content_part.get_element('//office:annotation[1]'))
        self.paragraph_element = content_part.get_element('//text:p[1]')


    def test_get_parent(self):
        paragraph = self.paragraph_element
        parent = paragraph.get_parent()
        self.assertEqual(parent.get_tagname(), 'text:section')


    def test_get_parent_root(self):
        content = self.content_part
        root = content.get_root()
        parent = root.get_parent()
        self.assertEqual(parent, None)


    def test_insert_element_first_child(self):
        element = odf_create_element('<root><a/></root>')
        child = odf_create_element('<b/>')
        element.insert_element(child, FIRST_CHILD)
        self.assertEqual(element.serialize(), '<root><b/><a/></root>')


    def test_insert_element_last_child(self):
        element = odf_create_element('<root><a/></root>')
        child = odf_create_element('<b/>')
        element.append_element(child)
        self.assertEqual(element.serialize(), '<root><a/><b/></root>')


    def test_insert_element_next_sibling(self):
        root = odf_create_element('<root><a/><b/></root>')
        element = root.get_element_list('//a')[0]
        sibling = odf_create_element('<c/>')
        element.insert_element(sibling, NEXT_SIBLING)
        self.assertEqual(root.serialize(), '<root><a/><c/><b/></root>')


    def test_insert_element_prev_sibling(self):
        root = odf_create_element('<root><a/><b/></root>')
        element = root.get_element_list('//a')[0]
        sibling = odf_create_element('<c/>')
        element.insert_element(sibling, PREV_SIBLING)
        self.assertEqual(root.serialize(), '<root><c/><a/><b/></root>')


    def test_insert_element_bad_element(self):
        element = odf_create_element('<a/>')
        self.assertRaises(AttributeError, element.insert_element, '<b/>',
                          FIRST_CHILD)


    def test_insert_element_bad_position(self):
        element = odf_create_element('<a/>')
        child = odf_create_element('<b/>')
        self.assertRaises(ValueError, element.insert_element, child, 999)


    def test_get_children(self):
        element = self.annotation_element
        children = element.get_children()
        self.assertEqual(len(children), 4)
        child = children[0]
        self.assertEqual(child.get_tagname(), 'dc:creator')
        child = children[-1]
        self.assertEqual(child.get_tagname(), 'text:p')


    def test_append_element(self):
        element = odf_create_element("<root/>")
        element.append_element(u"f")
        element.append_element(u"oo1")
        element.append_element(odf_create_element("<a/>"))
        element.append_element(u"f")
        element.append_element(u"oo2")
        self.assertEqual(element.serialize(), "<root>foo1<a/>foo2</root>")



class SearchTestCase(TestCase):

    def setUp(self):
        self.container = odf_get_container('samples/span_style.odt')
        self.content = odf_xmlpart('content', self.container)
        self.paragraph = self.content.get_element('//text:p')
        self.span = self.paragraph.get_element('//text:span')


    def test_search_paragraph(self):
        """Search text in a paragraph.
        """
        pos = self.paragraph.search(u'ère')
        return self.assertEqual(pos, 4)


    def test_match_span(self):
        """Search text in a span.
        """
        pos = self.span.search(u'moust')
        return self.assertEqual(pos, 0)


    def test_match_inner_span(self):
        """Search text in a span from the parent paragraph.
        """
        pos = self.paragraph.search(u'roug')
        return self.assertEqual(pos, 29)


    def test_simple_regex(self):
        """Search a simple regex.
        """
        pos = self.paragraph.search(u'che roug')
        return self.assertEqual(pos, 25)


    def test_intermediate_regex(self):
        """Search an intermediate regex.
        """
        pos = self.paragraph.search(u'moustache (blanche|rouge)')
        return self.assertEqual(pos, 19)


    def test_complex_regex(self):
        """Search a complex regex.
        """
        # The (?<=...) part is pointless as we don't try to get groups from
        # a MatchObject. However, it's a valid regex expression.
        pos = self.paragraph.search(ur'(?<=m)(ou)\w+(che) (blan\2|r\1ge)')
        return self.assertEqual(pos, 20)


    def test_compiled_regex(self):
        """Search with a compiled pattern.
        """
        pattern = compile(ur'moustache')
        pos = self.paragraph.search(pattern)
        return self.assertEqual(pos, 19)


    def test_failing_match(self):
        """Test a regex that doesn't match.
        """
        pos = self.paragraph.search(u'Le Père moustache')
        return self.assert_(pos is None)



class MatchTestCase(TestCase):

    def setUp(self):
        self.container = odf_get_container('samples/span_style.odt')
        self.content = odf_xmlpart('content', self.container)
        self.paragraph = self.content.get_element('//text:p')
        self.span = self.paragraph.get_element('//text:span')


    def test_match_paragraph(self):
        """Match text in a paragraph.
        """
        match = self.paragraph.match(u'ère')
        return self.assertTrue(match)


    def test_match_span(self):
        """Match text in a span.
        """
        match = self.span.match(u'moust')
        return self.assertTrue(match)


    def test_match_inner_span(self):
        """Match text in a span from the parent paragraph.
        """
        match = self.paragraph.match(u'roug')
        return self.assertTrue(match)


    def test_simple_regex(self):
        """Match a simple regex.
        """
        match = self.paragraph.match(u'che roug')
        return self.assertTrue(match)


    def test_intermediate_regex(self):
        """Match an intermediate regex.
        """
        match = self.paragraph.match(u'moustache (blanche|rouge)')
        return self.assertTrue(match)


    def test_complex_regex(self):
        """Match a complex regex.
        """
        # The (?<=...) part is pointless as we don't try to get groups from
        # a MatchObject. However, it's a valid regex expression.
        match = self.paragraph.match(ur'(?<=m)(ou)\w+(che) (blan\2|r\1ge)')
        return self.assertTrue(match)


    def test_compiled_regex(self):
        """Match with a compiled pattern.
        """
        pattern = compile(ur'moustache')
        match = self.paragraph.match(pattern)
        return self.assertTrue(match)


    def test_failing_match(self):
        """Test a regex that doesn't match.
        """
        match = self.paragraph.match(u'Le Père moustache')
        return self.assertFalse(match)



class ReplaceTestCase(TestCase):

    def setUp(self):
        self.container = odf_get_container('samples/span_style.odt')
        self.content = odf_xmlpart('content', self.container)
        self.paragraph = self.content.get_element('//text:p')
        self.span = self.paragraph.get_element('//text:span')


    def test_count(self):
        paragraph = self.paragraph
        expected = paragraph.serialize()
        count = paragraph.replace(u"ou")
        self.assertEqual(count, 2)
        # Ensure the orignal was not altered
        self.assertEqual(paragraph.serialize(), expected)


    def test_replace(self):
        paragraph = self.paragraph
        clone = paragraph.clone()
        count =  clone.replace(u"moustache", u"barbe")
        self.assertEqual(count, 1)
        expected = u"Le Père Noël a une barbe rouge."
        self.assertEqual(clone.get_text(recursive=True), expected)
        # Ensure the orignal was not altered
        self.assertNotEqual(clone.serialize(), paragraph.serialize())


    def test_across_span(self):
        paragraph = self.paragraph
        count = paragraph.replace(u"moustache rouge")
        self.assertEqual(count, 0)


    def test_missing(self):
        paragraph = self.paragraph
        count = paragraph.replace(u"barbe")
        self.assertEqual(count, 0)


class XmlNamespaceTestCase(TestCase):
    """We must be able to use the API with unknown prefix/namespace"""



if __name__ == '__main__':
    main()
