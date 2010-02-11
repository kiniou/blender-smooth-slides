#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from optparse import OptionParser
from sys import exit, stdout

# Import from lpod
from tools.lpod.document import odf_document, odf_get_document
from tools.lpod.container import odf_container , odf_get_container
from tools.lpod.paragraph import odf_paragraph
from tools.lpod.frame import odf_frame
from tools.lpod.draw_page import odf_draw_page
from tools.lpod.list import odf_list
from tools.lpod.element import odf_element, register_element_class
__version__ = "0.1"


def test_document(document) :
	content = document.get_body()

	pages = content.get_draw_page_list()
	styles = document.get_style_list()
	for s in styles:
		if (isinstance(s,intern.lpod.style.odf_style) ) :
			print s.get_style_name() , s.get_style_family() , s.get_tagname()
			print s.get_parent().get_tagname()
	
	for page_idx , page in enumerate(pages):
		print page_idx , page.get_page_name()
		frames = page.get_frame_list()
		for frame_idx,frame in enumerate(frames):
			print "Frame", frame_idx
			attr = frame.get_attributes()
			print attr
			keys = attr.keys()
			#style_name = frame.get_attribute("presentation:style-name")
			#print document.get_style(family='presentation' , name_or_element='presentation:'+style_name)
			print "---------"
		print "*********"


def debug_level(element,inc_lvl,context):
		context['level'] += inc_lvl
		lvl = context['level']
		if (inc_lvl > 0) :
			print "\t" * lvl + element.get_tagname()
	

class my_document (odf_document) :

	def get_formatted_text(self):
		type = self.get_type()
		if type not in ('presentation'):
			raise NotImplementedError, ('Type of document "%s" not supported yet' % type)

		body = self.get_body()
		context = {'document': self , 'level' : 0 }
		result = []
		for element in body.get_children():
			if (element.get_tagname() in ["draw:page"]) :
				result.append(element.get_formatted_text(context))
		return result
			
class my_page(odf_draw_page):
	def get_formatted_text(self, context):
		debug_level(self,1,context)

		page_name = self.get_page_name()
		page = {page_name : []}
		for element in self.get_children():
			page[page_name].append(element.get_formatted_text(context) )

		debug_level(self,-1,context)
		return page

class my_frame(odf_frame):
	def get_formatted_text(self, context):
		debug_level(self,1,context)
		result = []
		for element in self.get_children():
			result.append(element.get_formatted_text(context) )

		debug_level(self,-1,context)
		return result

class my_textbox(odf_element):
	def get_formatted_text(self, context):
		debug_level(self,1,context)
		result = []
		for element in self.get_children():
			result.append(element.get_formatted_text(context) )

		debug_level(self,-1,context)
		return result

class my_image(odf_element):
	def get_formatted_text(self, context):
		debug_level(self,1,context)
		result = [self.get_attribute('xlink:href')]
		return result		

class my_paragraph(odf_paragraph):
	def get_formatted_text(self, context):
		debug_level(self,-1,context)

		text = self.get_text(False)
		if text:
			result = [text]
		else:
			result = []
		for element in self.get_children() :
			result.append(element.get_formatted_text(context))

		debug_level(self,1,context)
		return result 



class my_list(odf_list):
	def get_formatted_text(self,context):
		debug_level(self,1,context)
		result = []
		for list_item in self.get_element_list("text:list-item"):
			for children in list_item.get_children():
				result.append(children.get_formatted_text(context))
		debug_level(self,-1,context)
		return result


#class my_list_item(odf_list_item

register_element_class('text:p', my_paragraph)
register_element_class('text:span', my_paragraph)
register_element_class('text:list', my_list)
register_element_class('draw:text-box', my_textbox)
register_element_class('draw:page', my_page)
register_element_class('draw:frame', my_frame)
register_element_class('draw:image', my_image)
#register_element_class('text:list-item', my_list_item)

if __name__ == "__main__" :
	usage = "%prog <file>"
	description = "a little test with lpOD to parse ODP files"
	parser = OptionParser (usage , version = __version__ , description = description)

	options , args = parser.parse_args()

	if(len(args) != 1):
		parser.print_help()
		exit(1)
	container = odf_get_container(args[0])
	document = my_document(container)
	
	result = document.get_formatted_text()
	for r in result:
		print r
	
