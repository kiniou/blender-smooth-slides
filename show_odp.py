#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from optparse import OptionParser
from sys import exit, stdout
from pprint import pprint, pformat
import os.path

# Import from lpod
from tools.lpod.document import odf_document, odf_get_document
from tools.lpod.container import odf_container , odf_get_container
from tools.lpod.paragraph import odf_paragraph
from tools.lpod.span import odf_span
from tools.lpod.frame import odf_frame
from tools.lpod.draw_page import odf_draw_page
from tools.lpod.list import odf_list
from tools.lpod.element import odf_element, register_element_class, odf_text
from tools.lpod.style import odf_style


# Import pango/cairo
import pango
import cairo
import pangocairo

import math
__version__ = "0.1"
__elm_debug__ = False


text_i = 0
dpi = 300.0
cm = dpi / 2.54

def debug_level(element,inc_lvl,context):
		context['level'] += inc_lvl
		lvl = context['level']
		if (inc_lvl > 0 and __elm_debug__) :
			print "\t" * lvl + element.get_tagname()

def _create_frame_image(width , height , text):
		global text_i
		image_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(round(width * cm)), int(round(height * cm)) )
		#image_surface = cairo.SVGSurface("./tests/test_cairo/TEST_%s.svg"% ("%04d" % text_i), width * cm, height * cm)
		#image_surface = cairo.SVGSurface(None, width * cm, height * cm)
		
		cairo_context = cairo.Context(image_surface)

		pangocairo_context = pangocairo.CairoContext(cairo_context)
		pango_layout = pangocairo_context.create_layout()
#		pango_layout.set_indent(10)
		pango_layout.set_markup(text)
		layout_iter = pango_layout.get_iter()

		cairo_fontmap = pangocairo.cairo_font_map_get_default()
		cairo_fontmap.set_resolution(dpi)

#		pangocairo_layout.set_wrap(pango.WRAP_WORD) 
#		pango_layout.get_width()
#		pangocairo_context.update_layout(pangocairo_layout)
#		print "PLOP" , pangocairo_layout.get_width() , pangocairo_layout.get_size()
#		pangocairo_context.show_layout(pangocairo_layout)
#		print dir(image_surface)
#		pangocairo_context.show_layout(pangocairo_layout)
		cairo_context.set_miter_limit(cairo.LINE_JOIN_ROUND)
		cairo_context.set_line_cap(cairo.LINE_CAP_ROUND)
		
		cairo_context.set_line_width(2.0 * 3)
		pprint(pango_layout.get_pixel_extents())
		pangocairo_context.layout_path(pango_layout)
		stroke_extents = cairo_context.stroke_extents()
		print stroke_extents
#		while True:
#			#cairo_context.translate(10,0)
#			print "Layout " , layout_iter.get_layout_extents() 
#			print "Line " , layout_iter.get_line_extents() 
#			print "Run " , layout_iter.get_run_extents()
#			layout_iter.next_line()
#			if layout_iter.at_last_line() : break

		cairo_context.set_source_rgb(0.0,0.0,0.0)
		cairo_context.stroke_preserve()
		cairo_context.set_source_rgb(1.0,1.0,1.0)
		cairo_context.fill_preserve()
		print "PANGO LAYOUT TEST %04d : " % text_i , pango_layout.get_size() , pango_layout.get_pixel_size() , pango_layout.get_width()
		#cairo_context.show_page() 
		
#		img_buf = StringIO.StringIO()
#		image_surface.write_to_png(img_buf)
#		img_buf.seek(0)
		image_surface.write_to_png("./tests/test_cairo/TEST_%s.png" % ("%04d" % text_i))
		text_i += 1

def _get_paragraph_style(element,context) :
	#FIXME
	pass

def _get_style_properties(element,context,prop_name):
	doc_styles = context['styles']

	parent = element
	#get the element tag_name
	parent_tag = parent.get_tagname()
	print "Get '%s' style for element '%s' :" % (prop_name , parent_tag)

	#rewind parent objects to get all styles
	style_names = []

	debug_parent = [] 
	while parent is not None:
		style_name = parent.get_text_style()
		if style_name is not None and style_name not in style_names:
			style_names.append(style_name)
		debug_parent[0:0] = ["[%s %s]" %(parent.get_tagname() , style_name)]
		parent = parent.get_parent()

	style = doc_styles["standard"]
	style_prop = style.get_style_properties(prop_name)

#	print '>>'.join(debug_parent)
	print "tag" , repr(parent_tag) , "styles", pformat(repr(style_names))
	style_names.reverse()

	for s in style_names:
		style = doc_styles[s]

		if style.get_parent_style_name() is not None:
			p = style.get_style_properties(prop_name)
			if p is not None: 
				style_prop.update(p)
			while style.get_parent_style_name() is not None:
				style = doc_styles[style.get_parent_style_name()]
				p = style.get_style_properties(prop_name)
				if p is not None:
					style_prop.update(p)
		else:
			p = style.get_style_properties(prop_name)
			if p is not None:
				style_prop.update(p)
		
		#text_prop.update(props)

#	pprint(style_prop)

	return _get_text_style(style_prop)

def _get_style_list(level)



def _get_pango_span ( text_prop):
	font_family = text_prop['fo:font-family'].strip("'")
	font_size = int(float(text_prop['fo:font-size'].rstrip('pt')) * 1000.0)
	font_style = text_prop['fo:font-style']
	font_weight=  text_prop['fo:font-weight']
	return ( u'<span face="%s" size="%s" style="%s" weight="%s">' % ( font_family,font_size,font_style, font_weight ) )

def _get_text_style ( text_prop):
	style = {}
	style['font-family'] = text_prop['fo:font-family'].strip("'")
	style['font-size']   = text_prop['fo:font-size'].rstrip('pt')
	style['font-style']  = text_prop['fo:font-style']
	style['font-weight'] = text_prop['fo:font-weight']
	style['text-outline'] = True if text_prop['style:text-outline'] == 'true' else False
	return style

def _get_paragraph_style(paragraph_prop):
	return None

def _get_text_children(element):
	return element.xpath('*|text()')

def _get_pango_text(element , context):
	document = context['document']
	result = context['result']
	styles = context['styles']
	objects = element.xpath('*|text()')
	text_prop = None
	for obj in objects:
		if type(obj) is odf_text:
			print 
			print "TEXT : %s" , obj , obj.get_parent()
			text_prop = _get_style_properties(obj.get_parent(),context,'text')
			result.append(obj)
		else:
			tag = obj.get_tagname()
			# Good tags with text
			if tag == 'text:p':
				print "Looking into text:p"
				_get_pango_text(obj, context)
				result.append(u'\n')
			# Try to convert some styles in rst_mode
			elif tag == 'text:span':
				print "Looking into text:span"
				_get_pango_text(obj, context)
		

class my_document (odf_document) :

	def get_formatted_text(self):
		type = self.get_type()
		if type not in ('presentation'):
			raise NotImplementedError, ('Type of document "%s" not supported yet' % type)

		body = self.get_body()
		style_list = self.get_style_list()
		styles = {}
		for s in style_list:
			styles[s.get_style_name()] = s
		context = {'document': self , 'styles' : styles , 'level' : 0 ,'rst_mode':False , 'master-page' : None}
		result = []


		for element in body.get_children():
			if (element.get_tagname() in ["draw:page"]) :
				result.append(element.get_formatted_text(context))

	#	print pformat(styles)

		return result
			
class my_page(odf_draw_page):
	def get_formatted_text(self, context):
		debug_level(self,1,context)

		page_name = self.get_page_name()
		page = {page_name : {}}
		style_name = self.get_attribute("draw:style-name")
		master_page = self.get_attribute("draw:master-page-name")


		mp = document.get_style("master-page" , master_page)
		master_dp  = document.get_style("drawing-page",mp.get_attribute("draw:style-name"))
		default_dp = document.get_style("drawing-page",style_name)
		background = document.get_style("presentation",master_page+"-background")
		
		page_attr = {'name':page_name , 'width':0 , 'height':0 , 'background':None , 'background-type':None}
		context['master-page'] = master_page
		for element in self.get_children():
			tag = element.get_tagname()
			if(tag not in page[page_name]) : page[page_name][tag] = []
			e = element.get_formatted_text(context)
			if e is not None : page[page_name][tag].append(e)

		debug_level(self,-1,context)
		return page

class my_frame(odf_frame):
	def get_formatted_text(self, context):
		debug_level(self,1,context)
#		result = []
		context['result'] = []

		#print "FRAME:" , pformat(self.get_attributes())
		height = float(self.get_attribute('svg:height').rstrip('cm'))
		width = float(self.get_attribute('svg:width').rstrip('cm'))
		x = float(self.get_attribute('svg:x').rstrip('cm'))
		y = float(self.get_attribute('svg:y').rstrip('cm'))
		
		for element in self.get_children():
#			result.append(element.get_formatted_text(context))
			element.get_formatted_text(context)
		result = context['result']	

#		if len(result) > 0 : 
			#print "TOTO"
#			_create_frame_image(width , height , result[0])
		debug_level(self,-1,context)
		if len(result) > 0 : 
			pprint(result)
			return result
		else : 
			return None
	
	def get_text_style(self):
		style_name = self.get_attribute("presentation:style-name")
		return style_name

class my_textbox(odf_element):
	def get_formatted_text(self, context):
		debug_level(self,1,context)
		context['list-level'] = 0
		for element in self.get_children():
			element.get_formatted_text(context)
		debug_level(self,-1,context)

	def get_text_style(self):
		return self.get_attribute('draw:text-style-name')

class my_image(odf_element):
	def get_formatted_text(self, context):
		doc = context['document']
		debug_level(self,1,context)
		context['result'].append(self.get_attribute('xlink:href'))

class my_paragraph(odf_paragraph):
	def get_formatted_text(self, context):
		debug_level(self,-1,context)
		for children in _get_text_children(self) :
			if type(children) is not odf_text:
				children.get_formatted_text(context)
			else:
				print "MYPARAGRAPH '%-20s' : %s" % (self.get_tagname(),children) 
				text_prop = _get_style_properties(self,context , 'text')
				print pformat(text_prop)
#				print "DEBUG PARENT" , children.xpath('parent').get_tagname()

		debug_level(self,1,context)

class my_span(odf_span):
	def get_formatted_text(self,context):
		debug_level(self,-1,context)
		for children in _get_text_children(self) :
			if type(children) is not odf_text:
				children.get_formatted_text(context)
			else :
				print "MYSPAN '%-20s' : %s" % (self.get_tagname(),children)
				text_prop = _get_style_properties(self,context , 'text')
				print pformat(text_prop)

		debug_level(self,1,context)
		

class my_list(odf_list):
	def get_formatted_text(self, context):
		debug_level(self,-1,context)
		context['list-level'] += 1
#		text_prop = _get_style_properties(self, context, 'list')
#		pprint(text_prop)
		for children in _get_text_children(self) :
			if type(children) is not odf_text:
				children.get_formatted_text(context)
			else :
				print "TEXT '%-20s' : %s" % (self.get_tagname(),children)
		context['list-level'] -= 1
		debug_level(self,1,context)

class my_list_item(odf_element):
	def get_formatted_text(self,context):
		debug_level(self,-1,context)
		for children in _get_text_children(self) :
			if type(children) is not odf_text:
				children.get_formatted_text(context)
			else :
				print "TEXT '-%20s' : %s" % (self.get_tagname(),children)
		debug_level(self,1,context)
		
register_element_class('text:p', my_paragraph)
register_element_class('text:span', my_span)
register_element_class('text:list', my_list)
register_element_class('text:list-item', my_list_item)
register_element_class('draw:text-box', my_textbox)
register_element_class('draw:page', my_page)
register_element_class('draw:frame', my_frame)
register_element_class('draw:image', my_image)

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
#	for r in result: pprint(r)

#	elements = document.get_styled_elements()
#	for e in elements:
#		print e.get_tagname()
	
