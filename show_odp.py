#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from optparse import OptionParser
from sys import exit, stdout
from pprint import pprint, pformat
import os.path
import re
import math

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
from tools.lpod.utils import _get_element_list , _get_element

# Import pango/cairo
import pango
import cairo
import pangocairo

__version__ = "0.1"
__elm_debug__ = False


text_i = 0
dpi = 96.0
cm = dpi / 2.54

def debug_level(element,inc_lvl,context):
		context['level'] += inc_lvl
		lvl = context['level']
		if (inc_lvl > 0 and __elm_debug__) :
			print "\t" * lvl + element.get_tagname()

def _get_pango_span ( text_prop):
	font_family = text_prop['fo:font-family'].strip("'")
	font_size = int(float(text_prop['fo:font-size'].rstrip('pt')) * pango.SCALE)
	font_style = text_prop['fo:font-style']
	font_weight=  text_prop['fo:font-weight']
	if text_prop.has_key('style:text-underline-style'):
		if text_prop['style:text-underline-style'] == 'none':
			font_underline = 'none'
		elif text_prop['style:text-underline-style'] == 'solid':
			font_underline = 'single'
		else :
			font_underline = 'single'
	return ( u'<span face="%s" size="%s" style="%s" weight="%s" underline="%s">' % ( font_family,font_size,font_style, font_weight , font_underline) )

def _create_frame_image(width,height,image):
	pass

def _draw_rectangle(rect , col , cr):
			cr.rel_line_to(rect[2],0)
			cr.rel_line_to(0,rect[3])
			cr.rel_line_to(-rect[2],0)
			cr.close_path()
		
			cr.set_source_rgba(col[0],col[1],col[2],0.3)
			cr.fill_preserve()
			cr.set_source_rgba(col[0],col[1],col[2],1.0)
			cr.stroke()
def _create_frame_textbox(width , height , texts):
		global text_i


		image_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(round(width * cm)), int(round(height * cm)) )
		cairo_context = cairo.Context(image_surface)
		cairo_context.set_miter_limit(cairo.LINE_JOIN_ROUND)
		cairo_context.set_line_cap(cairo.LINE_CAP_ROUND)
		cairo_fontmap = pangocairo.cairo_font_map_get_default()
		cairo_fontmap.set_resolution(dpi)
		cairo_context.move_to(0,0)
		cairo_context.set_line_width(1.0)

		pangocairo_context = pangocairo.CairoContext(cairo_context)
		pango_layout = pangocairo_context.create_layout()
		pango_layout.set_spacing(0)
		pango_layout.set_wrap(pango.WRAP_WORD) 

		bullet_layout = None
		bullet = None
		y_pos = 0.0
		for i in range(len(texts)):
			first_line = True
			font_outline = False
			text = ""
			p = texts[i]
			if p['paragraph-style'].has_key('fo:text-align'):
				text_align = p['paragraph-style']['fo:text-align']
			else :
				text_align = 'start'

			if text_align == 'start' :
				pango_layout.set_alignment(pango.ALIGN_LEFT)
			elif text_align == 'center':
				pango_layout.set_alignment(pango.ALIGN_CENTER)
			elif text_align == 'end':
				pango_layout.set_alignment(pango.ALIGN_RIGHT)
			for t in p['texts']:
				if t.has_key('text-style'):
					if t['text-style']['style:text-outline'] == 'true' : font_outline = True
					text += _get_pango_span(t['text-style']) + t['text-content'] + "</span>"
				else:
					text += t['text-content']
			if p.has_key('bullet'):
				bullet_layout = pangocairo_context.create_layout()
				bullet_layout.set_width(int(round(width * cm)) * pango.SCALE)
				bullet = p['bullet']
				bullet_span = _get_pango_span(bullet['text-style']) + bullet['text-content'] + '</span>'
				bullet_layout.set_markup(bullet_span)
				if bullet['list-style'].has_key('text:space-before'):
					space_before = float(bullet['list-style']['text:space-before'].rstrip('cm') )
					bullet['_space-before'] = space_before * cm
				else:
					bullet['_space-before'] = 0

				if bullet['list-style'].has_key('text:min-label-width'):
					label_width = float(bullet['list-style']['text:min-label-width'].rstrip('cm') )
					bullet['_label-width'] = label_width * cm
				else:
					bullet['_label-width'] = 0
					
				ink,logical = bullet_layout.get_pixel_extents()
				bullet['_width'] = logical[2]
				xstart = bullet['_label-width'] + bullet['_space-before']
				pango_layout.set_width(int(math.floor( (width * cm - xstart) * pango.SCALE) ) )
			else:
				pango_layout.set_width(int(math.floor( (width * cm) * pango.SCALE) ) )
				xstart = 0.0

			pango_layout.set_markup(text)
			iter = pango_layout.get_iter()
			lines_remains = True
			tmp_ypos = 0
			while lines_remains:
				ink_t , logical_t = iter.get_line_extents()
				ink = map(lambda x:x/pango.SCALE, ink_t)
				logical = map(lambda x:x/pango.SCALE, logical_t)
				line = iter.get_line()
				baseline = iter.get_baseline()

#				cairo_context.move_to( xstart + logical[0] , y_pos + logical[1])
#				_draw_rectangle(logical,(1,0,0),cairo_context)
#				cairo_context.move_to( xstart + ink[0] - (ink[0] - logical[0])/2.0 , y_pos + ink[1])
#				_draw_rectangle(ink,(0,1,0),cairo_context)
				text_xpos = xstart + logical[0] + (logical[0] - ink[0])/2.0
				text_ypos = y_pos + baseline/pango.SCALE
				if bullet is not None and first_line:
					if text_align == 'start':
						bullet_ink,bullet_logic = bullet_layout.get_pixel_extents()
						bullet_xpos = bullet['_space-before']
						bullet_ypos = y_pos + (logical[3] - bullet_logic[3])/2.0

					elif text_align == 'center':
						bullet_ink,bullet_logic = bullet_layout.get_pixel_extents()
						bullet_xpos = text_xpos - bullet['_label-width']
						bullet_ypos = y_pos + (logical[3] - bullet_logic[3])/2.0
						
					elif text_align == 'end':
						bullet_ink,bullet_logic = bullet_layout.get_pixel_extents()
						bullet_xpos = text_xpos - bullet['_label-width']
						bullet_ypos = y_pos + (logical[3] - bullet_logic[3])/2.0

					cairo_context.move_to( bullet_xpos, bullet_ypos )
					cairo_context.set_source_rgb(0.0,0.0,0.0)
					pangocairo_context.show_layout(bullet_layout)

				cairo_context.move_to( text_xpos, text_ypos )
				if font_outline :
					pangocairo_context.layout_line_path(line)
					cairo_context.set_line_width(2.0)
					cairo_context.set_source_rgb(0.0,0.0,0.0)
					cairo_context.stroke_preserve()
					cairo_context.set_source_rgba(1.0,1.0,1.0,0.9)
					cairo_context.fill_preserve()
				else :
					pangocairo_context.layout_line_path(line)
					cairo_context.set_source_rgb(0.0,0.0,0.0)
					cairo_context.fill_preserve()
					
				first_line = False
				lines_remains = iter.next_line()
				tmp_ypos += logical[3]

			y_pos += tmp_ypos			

		image_surface.write_to_png("./tests/test_cairo/TEST_%s.png" % ("%04d" % text_i))
		text_i += 1

def _get_paragraph_style(element,context) :
	#FIXME
	pass

def _check_outline_style(style,context):
	result = None
	if re.match(r'^(.*-outline)[0-9]+$', style) is not None and context.has_key('list-level'):
		result = re.sub(r'^(.*-outline)[0-9]+$',r'\1',style)+'%d'%context['list-level']
		print "Outline style : %s -> %s" % (style,result)
	return result

def _get_current_styles(element, context):
	doc_styles = context['styles']
	parent = element
	style_names = []

	#Get self and ancestors text style names
	while parent is not None:
		style_name = parent.get_text_style()
		if style_name is not None and style_name not in style_names:
			outline_checked = False
			outline = _check_outline_style(style_name,context)
			if outline is not None:
				style_name = outline
				outline_checked = True
			style = doc_styles[style_name]
			if (style.get_parent_style_name() is not None):
				new_list = []
				new_list.append(style_name)
				parent_style = style.get_parent_style_name()
				while parent_style is not None:
					if outline_checked is False:
						outline = _check_outline_style(parent_style,context)
						if outline is not None:
							parent_style = outline
							outline_checked = True
					new_list.append(parent_style)
					style = doc_styles[parent_style]
					parent_style = style.get_parent_style_name()
				
				style_names.extend(new_list)
			else:
				style_names.append(style_name)
		parent = parent.get_parent()

	style_names.append("standard")
	style_names.reverse()

	return style_names

def _get_list_style(style_names, context , level):
	any_style = ('(text:list-level-style-number'
                 '|text:list-level-style-bullet'
                 '|text:list-level-style-image)')
	doc_styles = context['styles']
	list_prop = None
	for s in style_names:
		style = doc_styles[s]
		level_style = _get_element(style,any_style,level=level)
		if level_style is not None:
			list_prop =  level_style

	result = {}
	if list_prop is not None:
		result['text:bullet-char'] = list_prop.get_attribute('text:bullet-char')
		level_props = list_prop.get_style_properties('list-level')
		if level_props is not None and len(level_props) > 0:
			result.update(level_props)
		text_props = list_prop.get_style_properties('text')
		if text_props is not None:
			result['fo:font-family'] = text_props['fo:font-family']
			result['fo:font-size'] = text_props['fo:font-size']
	return result
	

def _get_text_style ( style_names , context):
	result = {}
	text_prop = None
	doc_styles = context['styles']
	for s in style_names:
		style = doc_styles[s]
		text_prop = style.get_style_properties('text')
		if text_prop is not None:
			if text_prop.has_key('fo:font-size') and text_prop['fo:font-size'].endswith('%'):
					size = float(text_prop['fo:font-size'].rstrip('pt')) * ( float(text_prop['fo:font-size'].rstrip('%'))/100.0)
					result['fo:font-size']   = "%dpt" % size
			result.update(text_prop)
	return result

def _get_paragraph_style ( style_names , context):
	result = {}
	para_prop = None
	doc_styles = context['styles']
	for s in style_names :
		style = doc_styles[s]
		para_prop = style.get_style_properties('paragraph')
		if para_prop is not None:
			result.update(para_prop)
	return result

def _get_text_children(element):
	return element.xpath('*|text()')

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
		result = []

		height = float(self.get_attribute('svg:height').rstrip('cm'))
		width = float(self.get_attribute('svg:width').rstrip('cm'))
		x = float(self.get_attribute('svg:x').rstrip('cm'))
		y = float(self.get_attribute('svg:y').rstrip('cm'))
		
		for element in self.get_children():
			t = element.get_formatted_text(context)
			if t is not None:
				result.append(t)

		if len(result) > 0 : 
			_create_frame_textbox(width , height , result[0])
		debug_level(self,-1,context)
	
	def get_text_style(self):
		style_name = self.get_attribute("presentation:style-name")
		return style_name

class my_textbox(odf_element):
	def get_formatted_text(self, context):
		debug_level(self,1,context)
		result = []
		for element in self.get_children():
			t = element.get_formatted_text(context)
			if t is not None:
				result.extend(t)

		debug_level(self,-1,context)
		if len(result)>0:
			return result
		else:
			return None

	def get_text_style(self):
		return self.get_attribute('draw:text-style-name')

class my_image(odf_element):
	def get_formatted_text(self, context):
		doc = context['document']
		debug_level(self,1,context)
		result = self.get_attribute('xlink:href')
		debug_level(self,-1,context)
		return None

class my_paragraph(odf_paragraph):
	def get_formatted_text(self, context):
		debug_level(self,-1,context)

		styles = _get_current_styles(self,context)
		paragraph = {}
		paragraph['paragraph-style'] = _get_paragraph_style(styles,context)
		paragraph['texts'] = []
		for children in _get_text_children(self) :
			if type(children) is not odf_text:
				t = children.get_formatted_text(context)
				if t is not None:
					paragraph['texts'].append(t)
			else:
				text = {}
				bullet = {}
				text['text-style'] = _get_text_style(styles,context)
				if context.has_key("list-level") : 
					bullet['text-style'] = _get_text_style(styles,context)
					list_style = _get_list_style(styles,context,context['list-level'])
					bullet['list-style'] = list_style
					if list_style.has_key('fo:font-size') and list_style['fo:font-size'].endswith('%'):
						old_size = float(bullet['text-style']['fo:font-size'].rstrip('pt'))
						lst_size = float(list_style['fo:font-size'].rstrip('%'))/100.0
						new_size = old_size * lst_size
						bullet['text-style']['fo:font-size']   = "%dpt" % new_size
						bullet['text-style']['fo:font-size_old'] = "%dpt" % old_size
					if list_style.has_key('fo:font-family'):
						bullet['text-style']['fo:font-family_old'] = bullet['text-style']['fo:font-family']
						bullet['text-style']['fo:font-family'] = list_style['fo:font-family']

					bullet['text-content'] = "%s " % ( list_style['text:bullet-char'])
#					s = "%s%s %s" % ('\t'*(context['list-level']-1) , list_style['text:bullet-char'] , children)
					
				text['text-content'] = children
				paragraph['texts'].append(text)
				if len(bullet) > 0:
					paragraph['bullet'] = bullet
		
		debug_level(self,1,context)
		return [paragraph]

class my_span(odf_span):
	def get_formatted_text(self,context):
		debug_level(self,-1,context)
		styles = _get_current_styles(self,context)
		text = {}
		for children in _get_text_children(self) :
			if type(children) is not odf_text:
				children.get_formatted_text(context)
			else :
				text['text-style'] = _get_text_style(styles,context)
				text['text-content'] = children
		debug_level(self,1,context)
		if len(text) > 0:
			return text
		else:
			return None
		

class my_list(odf_list):
	def get_formatted_text(self, context):
		debug_level(self,-1,context)
		if not context.has_key('list-level') : context['list-level'] = 0
		context['list-level'] += 1
		result = []
		for children in _get_text_children(self) :
			if type(children) is not odf_text:
				r = children.get_formatted_text(context)
				if r is not None:
					result.extend(r)
			else :
				print "LIST '%-20s' : %s" % (self.get_tagname(),children)
		context['list-level'] -= 1
		if context['list-level'] == 0 :
			del context['list-level']
		debug_level(self,1,context)
		if len(result) > 0:
			return result
		else :
			return None

class my_list_item(odf_element):
	def get_formatted_text(self,context):
		debug_level(self,-1,context)
		result = []
		for children in _get_text_children(self) :
			if type(children) is not odf_text:
				r = children.get_formatted_text(context)
				if r is not None:
					result.extend(r)
			else :
				print "LIST-ITEM '-%20s' : %s" % (self.get_tagname(),children) , list_style
		debug_level(self,1,context)
		if len(result) > 0:
			return result
		else :
			return None

class my_line_break(odf_element):
	def get_formatted_text(self,context):
		text = {}
		text['text-content'] = u"\n"
		return text

register_element_class('text:p', my_paragraph)
register_element_class('text:span', my_span)
register_element_class('text:line-break', my_line_break)
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
	
