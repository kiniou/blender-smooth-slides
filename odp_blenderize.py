#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os , os.path
sys.path.append(os.path.dirname(os.path.realpath( __file__ )))

# Python imports
from optparse import OptionParser
from sys import exit, stdout
from pprint import pprint, pformat
import re
import math
import tempfile
import StringIO


_third_party_modules = True

# pango/cairo imports
try:
	import pango
	import cairo
	import pangocairo
except:
	print "ERROR : pygtk modules are not installed"
	_third_party_modules = False

# PIL imports
try:
	import PIL
	from PIL import ImageFont,ImageFile,ImageDraw,Image
except:
	print "ERROR : Python Imaging Library is not installed"
	_third_party_modules = False

# blender imports
try:
	import Blender
	from Blender import Text3d, Mesh, Camera, Mathutils,sys as bsys , Material , Texture , Image as BImage
	import bpy
except:
	print "ERROR : You must run this script along with Blender"
	_third_party_modules = False

if not _third_party_modules :
	exit()

__version__ = "0.1"
__elm_debug__ = False

#Global variables
text_i = 0
dpi = 150.0
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
	else : font_underline = 'none'
	return ( u'<span face="%s" size="%s" style="%s" weight="%s" underline="%s">' % ( font_family,font_size,font_style, font_weight , font_underline) )

def _create_frame_image(width,height,image):
	global text_i

	image_buffer = StringIO.StringIO()
	pprint(image[0:50])
	image_buffer.write(image)
	image_buffer.flush()
	image_buffer.seek(0)
	result = {'name' : "FRAME_%04d" % text_i , 'buffer' : image_buffer}
	text_i += 1
	return result

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
			margin = {'left':0 , 'right':0 , 'top':0 , 'bottom':0}
			para_style = p['paragraph-style']

			if para_style.has_key('fo:margin-left'):
				margin['left'] = float(para_style['fo:margin-left'].rstrip('cm')) * cm
			if para_style.has_key('fo:margin-right'):
				margin['right'] = float(para_style['fo:margin-right'].rstrip('cm')) * cm
			if para_style.has_key('fo:margin-top'):
				margin['top'] = float(para_style['fo:margin-top'].rstrip('cm')) * cm
			if para_style.has_key('fo:margin-bottom'):
				margin['bottom'] = float(para_style['fo:margin-bottom'].rstrip('cm'))*cm

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
			if len(p['texts'])>0:
				for t in p['texts']:
					#pprint(t,depth=1)
					if type(t) is dict:					
						if t.has_key('text-style'):
							if t['text-style']['style:text-outline'] == 'true' : font_outline = True
							text += _get_pango_span(t['text-style']) + t['text-content'] + "</span>"
						else:
							text += _get_pango_span(p['text-style']) + t['text-content'] + "</span>"
					elif type(t) is unicode:
						text += _get_pango_span(p['text-style']) + t + "</span>"
			else:
				text = _get_pango_span(p['text-style']) + ' ' + "</span>"
			#pprint(text)
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

#				cairo_context.move_to( xstart + ink[0] - (ink[0] - logical[0])/2.0 , y_pos + ink[1])
#				_draw_rectangle(ink,(0,1,0),cairo_context)
#				cairo_context.move_to( xstart + logical[0] , y_pos + logical[1])
#				_draw_rectangle(logical,(1,0,0),cairo_context)
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
					cairo_context.set_source_rgba(1.0,1.0,1.0,1.0)
					cairo_context.fill()
				else :
					pangocairo_context.layout_line_path(line)
					cairo_context.set_source_rgb(0.0,0.0,0.0)
					cairo_context.fill()
					
				first_line = False
				lines_remains = iter.next_line()
				tmp_ypos += logical[3]

			y_pos += tmp_ypos + margin['bottom']
		image_buffer = StringIO.StringIO() 
#		image_surface.write_to_png("./tests/test_cairo/TEST_%s.png" % ("%04d" % text_i))
		image_surface.write_to_png(image_buffer)
		image_buffer.seek(0)
		result = {'name' : "FRAME_%04d" % text_i , 'buffer' : image_buffer} 
		text_i += 1
		return result

def _get_paragraph_style(element,context) :
	#FIXME
	pass

def _check_outline_style(style,context):
	result = None
	if re.match(r'^(.*-outline)[0-9]+$', style) is not None and context.has_key('list-level'):
		result = re.sub(r'^(.*-outline)[0-9]+$',r'\1',style)+'%d'%context['list-level']
#		print "Outline style : %s -> %s" % (style,result)
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


def _blenderification(document):
	bg_images=document['bg_images']
	current_page = {'b_name' : '' , 'b_object' : None}
	current_frame = None

	#Get the presentation Scene
	scene = Blender.Scene.Get('Presentation')
	slides = Blender.Object.Get('Slides')

	page_i = 0
	page_str = "Page_%%0%d" % len(str(len(document['pages'])))+"d"
	print page_str

	for page in document['pages']:
		#Build the current page
		page_i += 1
		print "Building ", page['page_name'] , "=>" , page_str % (page_i) ,'\n' , pformat(page['attributes'],depth=1), '\n' , pformat(page['content'],depth=1)
		page_position = {'x':0 , 'y':1 * page_i , 'z' : 0 }

		i_page_name = page_str % (page_i)
		page_width = float( page['attributes']['width'].replace('cm','') )
		page_height = float( page['attributes']['height'].replace('cm','') )
		ratio_x = page_width
		ratio_y = page_height
#		print ratio_x , ratio_y
		coord = [ [ratio_x/2,0,ratio_y/2] , [ratio_x/2,0,-ratio_y/2] , [-ratio_x/2,0,-ratio_y/2] , [-ratio_x/2 , 0 , ratio_y/2] ]
		faces = [ [ 3 , 2 , 1 , 0] ]

		me = bpy.data.meshes.new(i_page_name)

		me.verts.extend(coord)
		me.faces.extend(faces)
		uv = ( Mathutils.Vector([1,0]) , Mathutils.Vector([1,1]) , Mathutils.Vector([0,1]) , Mathutils.Vector([0,0]) )
		for i in me.faces:
			i.uv = uv
		bg_image_name = page['attributes']['background']
		if bg_image_name is not None:
			if bg_images[bg_image_name].has_key('material') is not True:
				bg_image_data = bg_images[bg_image_name]['data']
				bg_images[bg_image_name]['material'] = _create_materials(bg_image_data , bg_image_name, use_alpha = False)
			me.materials = [ bg_images[bg_image_name]['material'] ]

		b_page = scene.objects.new(me)
		b_page.setLocation( page_position['x'] , page_position['y'] , page_position['z'] )
		b_page.makeDisplayList() 
		
		slides.makeParent([b_page],0,0)

		if page['content'].has_key('draw:frame'):
			#Build frames in the current page
			i_frame = 0
			for frame in page['content']['draw:frame']:
				i_frame += 1
				#print pformat(frame,depth=1)
				image = None
				frame_pos = {}
				
				if frame['content']['type'] == 'draw:text-box':
					image = _create_frame_textbox(frame['attributes']['width'] , frame['attributes']['height'] , frame['content']['content'])
				elif frame['content']['type'] == 'draw:image':
					image = _create_frame_image(frame['attributes']['width'] , frame['attributes']['height'] , frame['content']['content'])

				if image is not None:	
					name = image['name']
					pil_img = image['buffer']
					b_material = _create_materials(pil_img , name)
					ratio_x = frame['attributes']['width']
					ratio_y = frame['attributes']['height']
					pos_x = frame['attributes']['x']
					pos_y = frame['attributes']['y'] + ratio_y
#					coord = [ [ratio_x/2,0,ratio_y/2] , [ratio_x/2,0,-ratio_y/2] , [-ratio_x/2,0,-ratio_y/2] , [-ratio_x/2 , 0 , ratio_y/2] ]
					coord = [ [ratio_x,0,ratio_y] , [ratio_x,0,0] , [0,0,0] , [0 , 0 , ratio_y] ]
					faces = [ [ 3 , 2 , 1 , 0] ]

					me = bpy.data.meshes.new(name)

					me.verts.extend(coord)
					me.faces.extend(faces)
					uv = ( Mathutils.Vector([1,0]) , Mathutils.Vector([1,1]) , Mathutils.Vector([0,1]) , Mathutils.Vector([0,0]) )
					for i in me.faces:
						i.uv = uv

					me.materials = [b_material]
					b_frame = scene.objects.new(me)
					b_frame.setLocation( page_position['x'] - (page_width/2.0) + pos_x, page_position['y'] - (0.01 * i_frame) , page_position['z'] + (page_height/2.0) - pos_y )
					b_frame.makeDisplayList() 
					b_page.makeParent([b_frame],0,0)
		

def _create_materials(pil_img , name , use_alpha = True):
		img = PIL.Image.open(pil_img)
		tmpfile = tempfile.NamedTemporaryFile(suffix="BSS.png",delete=False)

		#Save the final image temporary
		img.save(tmpfile , 'PNG')
		tmpfile.flush()
		tmpfile.close()

		b_image = Blender.Image.Load("%s" % tmpfile.name)
		b_image.setName(name)
		b_image.pack()

		b_texture = Blender.Texture.New(name)
		b_texture.setImage(b_image)
		b_texture.setExtend('ClipCube')
		#pprint(Blender.Texture.ImageFlags)
		#pprint(Blender.Texture.ExtendModes)
		b_texture.setImageFlags('UseAlpha','MipMap')
		b_material = Blender.Material.New(name)
		b_material.setTexture(0, b_texture , Blender.Texture.TexCo.UV , Blender.Texture.MapTo.COL)
		if (use_alpha and img.mode == 'RGBA') :
			b_material.mode |= Blender.Material.Modes.ZTRANSP
		os.remove(tmpfile.name)
		return b_material

if __name__ == "__main__" :

	usage = "blender -b <template>.blend -P odp_importer.py -- <file>"
	description = "a little test with lpOD to parse ODP files"
	parser = OptionParser (usage , version = __version__ , description = description)

	print sys.argv
	
	if Blender.mode == 'background' or Blender.mode == 'interactive':
		try:
			script_args_index = sys.argv.index('--')
			if ( len(sys.argv[script_args_index])>1):
				real_argv = sys.argv[ (script_args_index + 1):]
			else:
				real_argv = []
		except:
			parser.error("script arguments start after blender arguments with '--'")


	options , args = parser.parse_args(real_argv)
#	options , args = parser.parse_args()

#	print real_argv,pformat(options),pformat(args)
	if(len(args) != 1):
		parser.error("You must provide ONE filename")
	if os.path.exists(args[0]) != 1:
		parser.error("File '%s' does not exist or is not a file" % (args[0]))

#	container = odf_get_container(args[0])
#	document = my_document(container)
	
#	result = document.get_formatted_text()


	import pickle
	output = open(args[0], 'r')
	result = pickle.load(output)
	output.close()
	_blenderification(result)
	blender_file = Blender.sys.makename(args[0],'.blend')
	Blender.PackAll()
	Blender.Save(blender_file,1)
	print "Blender File created at '%s'" % (blender_file)

