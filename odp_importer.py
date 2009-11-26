#!BPY
"""
    Smooth Slides for Blender
    Copyright © 2009 Kevin Roy

    Smooth Slides for Blender is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

""" Registration info for Blender menus:
Name: 'OpenDocumentPresentation (.odp)'
Blender: 249
Group: 'Import'
Tip: 'OpenDocumentPresentation (*.odp)'
"""
__author__ = "Kevin (KiNiOu) ROY"
__url__ = ("blender", "kiniou", "Author's site, http://blog.knokorpo.fr")
__version__ = "0.1"

__bpydoc__ = """\
This script import document from an Open Document Presentation
    version 0.1:
    create slides and text automagically
"""

# TODO : find a way to load Blender python librairies without blender itself :)
# TODO : reorganize and split the file for each importer objects

import Blender
from Blender import Text3d, Mesh, Camera, Mathutils,sys as bsys , Material , Texture , Image as BImage
import bpy

import sys, zipfile
sys.path.append('.')

import codecs
import os
import math
import copy
import urllib
import PIL
from PIL import ImageFont,ImageFile,ImageDraw,Image

import StringIO

import gtk
import pango
import cairo
import pangocairo

import tempfile

# TODO : check if there is a newer odfpy lib (if there isn't contribute because these lib worth it)
from tools.odf.opendocument import load,OpenDocumentPresentation
from tools.odf import text,presentation,draw,style,office

global prog_options 

def log_debug(lines):
    if prog_options.verbose:
        lines = str(lines)
        lines = lines.split('\n')
        for line in lines :
            print 'DEBUG: %s' % line

# TODO : put HTMLColorToRGB function into a tools.py file

def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r/255.0, g/255.0, b/255.0)


class ODP_Element:
    level = 0

    def __init__(self) :
        self.namespace = 'element'
        self.name = self.namespace.upper()
        self.triggers = {'Text' : self.do_text}
        self.attr_transform = {}
        self.options = {}
        self.tags_ignored = {}
        self.blender_objects = {}
        self.text = None
        self.childs = {'internal' : [] , 'external' : [] }

    def parse_tree(self, element, level=0 , stop_level=0 , filter_tags = True):

        if ( (stop_level != None and level > stop_level) ) : return

        log_debug('%s %s >%s' %( '---+' * level , self.name , element.tagName) )
#        self.do_attributes(odp_element, level)
        if ( filter_tags and ( element.tagName in self.triggers.keys() ) ) : 
            method = self.triggers.get(element.tagName)
            if method : method(element = element)
        else :
            if (not self.tags_ignored.get('_triggers_') ) : self.tags_ignored['_triggers_'] = []
            self.tags_ignored['_triggers_'].append(element.tagName)

        if element.childNodes:
            for child in element.childNodes:
                self.parse_tree(child, level + 1 , stop_level , filter_tags)
#        else :
#            if (element.tagName == 'Text') :
#                self.text = str(element)
#                log_debug("%s TEXT  :\"%s\"" % ('---+' * level , element) )

    def do_text(self, element) :
        if (self.text == None) : self.text = []
        self.text.append("%s" % str(element))

    def do_attributes(self, element, level = 0 , set_options = True):
        indentation = ( '    ' * (level + 1) )
#        if (element != None) : log_debug("Doing attributes for element %s" % ( element.tagName) )
        if element.attributes != None:
            #log_debug("Element %s has attributes!" % ( element.tagName ) )
            for attkey in element.attributes.keys():
                attvalue = unicode(element.attributes[attkey]).encode('utf-8')
                log_debug( "%s[attr %s=%s]" % ( indentation , attkey , attvalue) )
                if (set_options) :
#                    if (attkey in self.attr_transform) : self.options[self.attr_transform[attkey]] = attvalue
                    if (attkey in self.attr_transform) : self.options[attkey] = attvalue
                    else :
                        if (not self.tags_ignored.get('_options_')) : self.tags_ignored['_options_'] = []
                        self.tags_ignored['_options_'].append(attkey)

    def debug_attributes(self, element, level = 0 , set_options = False):
        self.do_attributes(element, level , set_options)

    def do_nothing(self):
        return

    def apply(self, list , attribute_name) :
        noerror = True
        #att_name = self.namespace + ':' + attribute_name
        att_name = attribute_name
        if self.options.get(att_name) :
            att_value = self.options.get(att_name)
            element = None
            if ( list != None and list.get(att_value) ) :
                element = list.get(att_value)
                self.childs['external'].extend([element])
                #self.options.update(element.options)
                #self.childs.extend(element.childs)
                #self.blender_objects.update(element.blender_objects)
            else :
                noerror = False
        else :
            noerror = False

        for c in self.childs['internal'] :
            if (not c.apply(list,attribute_name)) :
                no_error = False

        return noerror

    def get_options(self, name , namespace = None) :
        if namespace == None : namespace = self.namespace
        options = None

        if (name != None) :
            options = self.options.get(namespace + ':' + name)

        return options

    def get_blender_object(self, name , namespace = None) :
        if namespace == None : namespace = self.namespace
        blender_object = None

        if (name != None) :
            blender_object = self.blender_objects.get(namespace + ':' + name)

        return blender_object


    def __str__( self ) :
        indent = " " * 4 * ODP_Element.level
        str = ""
        str += "%s| %s\n" % (indent , self.name)
        if ( len(self.tags_ignored) > 0) :
            str += "%s|  Tags ignored :\n" % (indent)
            for t_key in self.tags_ignored.keys():
                str += "%s|  %s : %s\n" % ( indent , t_key , self.tags_ignored[t_key] )
        str += "%s|  Attributes :\n" % (indent)
        for o_key in self.options.keys():
            str += "%s|  %s -> %s\n" % ( indent , o_key , self.options[o_key] )
        if (self.text != None) :
            str += '%s| TEXT = "%s"\n' % ( indent , self.text)
        str += '%s| B.O. = "%s"\n' % ( indent , self.blender_objects)
        str += "%s====\n" % (indent)

        ODP_Element.level += 1
        for child in self.childs['internal']:
            str += "%s" % (child)
        for child in self.childs['external']:
            str += "%s" % (child)
        ODP_Element.level -= 1

        return str

class BuildContext():
    
    def __init__(self):

        log_debug(' > Init building Context')

        # TODO : remove this variable when style will be handled
        
#        self.screen = { 'width' : 800, 'height' : 600 }

#        log_debug('\t > Building fonts list')

#        fontdesc = pango.FontDescription("Liberation Sans 10")
#        image_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,100,300)
#        cairo_context = cairo.Context(image_surface)
#        cairo_context.rectangle(0,0,100,300)
#        cairo_context.set_source_rgb(1,1,1)
#        cairo_context.fill()
#
#
#        pangocairo_context = pangocairo.CairoContext(cairo_context)
#        pangocairo_layout = pangocairo_context.create_layout()
#        pangocairo_layout.set_font_description(fontdesc)
#        pangocairo_layout.set_markup(""" Test Pango with Blender!!
#        Youyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouy
#ouyoyuouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyouyyuoyuyo
#sdvqsdfggqgergergzergzergzergezgzergzergzergergergzergaeghhthrtzthztzth
#zhrhzrhrthrhhrthrhrrzvzevatgbhrthhzrhrthrttr
#zrbhbrtbzbtrhzrhzrhrtbztbzbrtbzrtbzrbrtbrtbrtbtrtbzrvbrgfbrzbrtbrzbzrbrtbrtbrtbrzbzrbrtbrtbbrtbbzrtbrtzbzrbzrb
#        """)
#        pangocairo_layout.set_wrap(pango.WRAP_WORD) 
#        pangocairo_layout.set_width(100) 
#        cairo_context.set_source_rgb(0,0,0)
#        pangocairo_context.show_layout(pangocairo_layout)
#        cairo_context.show_page() 
#        image_surface.write_to_png('test.png')
#        self.font_list = {}


        self.blender = {}
        self.game = {}
        self.init_blender_file()
        self.images = None
        log_debug(' > End building Context')

    def init_blender_file(self):
        self.blender['scene'] = Blender.Scene.Get('Presentation')
        
        self.blender['render'] = self.blender['scene'].getRenderingContext()
        self.blender['render'].enableGameFrameExpose()

        self.blender['slides'] = Blender.Object.Get('Slides')

    def create_blender_text(self,name, color):
        print "creating text %s with color %s" % (repr(name) , repr(color))
       # b_material = Material.New("Mat_%s" % name)
       # b_material.rgbCol = [color[0] , color[1] , color[2] ]
       # b_material.setMode('Shadeless')
       # self.blender['text'] = Text3d.New("Text3d_%s" % name) #Create the Text3d object
       # self.blender['text'].setExtrudeDepth(0)    #Give some relief 
       # self.blender['text'].setDefaultResolution(1)
        
       # self.blender['text_object'] = self.blender['scene'].objects.new(self.blender['text'])
       # self.blender['text_material'] = b_material
       # self.blender['scene'].objects.unlink(self.blender['text_object'])
        
class ODP_Text(ODP_Element):
    def __init__(self, x_element):
        ODP_Element.__init__(self) 
        self.namespace = 'text'
        self.name = self.namespace.upper()
        self.data = None

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,None)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp


class ODP_TextList(ODP_Element):
    def __init__( self, x_element) :
        ODP_Element.__init__(self) 
        self.namespace = 'text-list'
        self.name = self.namespace.upper()
        self.data = None
        
        self.triggers.update({
            'text:list' : self.do_attributes,
            'text:list-item' : self.do_textlistitem,
        })

        self.attr_transform = [
            'text:style-name',
        ]

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

    def do_textlistitem(self, element):
        self.childs['internal'].append(ODP_TextListItem(element))

class ODP_TextListItem(ODP_Element) :
    def __init__(self , x_element):
        ODP_Element.__init__(self)
        self.namespace = 'text-list-item'
        self.name = self.namespace.upper()
        self.data = None
        
        self.triggers.update({
            'text:p' : self.do_textp,
            'text:list' : self.do_textlist,
            'text:list-item' : self.do_attributes,
        })

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp
        
    def do_textp(self, element):
        self.childs['internal'].append( ODP_TextP(element) )

    def do_textlist(self, element):
        self.childs['internal'].append(ODP_TextList(element))

#    def do_textlistitem(self, element):
#        self.debug_attributes(element)
#        self.childs.append(ODP_TextListItem(element))

class ODP_TextSpan(ODP_Element):
    def __init__( self, x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'text-span'
        self.name = self.namespace.upper()
        self.data = None
        
        self.triggers.update({
            'text:span' : self.do_attributes,
        })

        self.attr_transform = [
            'text:style-name',
        ]

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp
   

class ODP_TextP(ODP_Element):
    
    def __init__( self, x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'text-p'
        self.name = self.namespace.upper()
        self.data = None
        
        self.triggers.update({
            'text:p' : self.do_attributes,
            'text:span' : self.do_textspan,
        })

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

    def do_textspan(self, element):
        self.childs['internal'].append( ODP_TextSpan(element) )

    def build( self , build_context) :
        self.do_nothing()


class ODP_TextBox(ODP_Element) :
    textbox_counter = 0

    def __init__( self , x_element):
        ODP_Element.__init__(self)
        self.namespace = 'text-box'
        self.name = self.namespace.upper()
        self.data = None

        self.__class__.textbox_counter += 1
        self.options.update( {self.namespace + ':number' : self.__class__.textbox_counter} )
        
        self.triggers.update({
            'draw:text-box' : self.do_attributes,
            'text:p' : self.do_textp,
            'text:list' : self.do_textlist,
        })

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp
       
    def do_textp(self, element):
        self.childs['internal'].append( ODP_TextP(element) )

    def do_textlist(self, element):
        self.childs['internal'].append( ODP_TextList(element) )
 
    def build( self , build_context) :
        self.do_nothing()


class ODP_Frame(ODP_Element) :
    frame_counter = 0    
    maxchilds = 0

    def __init__(self,x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'frame'
        self.name = self.namespace.upper()
        self.data = None

        self.attr_transform = [
            'svg:x',
            'svg:y',
            'svg:width',
            'svg:height',
            'draw:layer',
            'presentation:class',
            'presentation:style-name',
            'draw:id',
            'presentation:user-transformed',
        ]

        self.triggers.update({
            'draw:frame' : self.do_attributes,
            'draw:text-box' : self.do_textbox,
            'draw:image' : self.do_image,
        })

        self.__class__.frame_counter += 1
        self.options.update( {self.namespace + ':number' : self.__class__.frame_counter} )
        
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

        if (len(self.childs['internal']) > self.__class__.maxchilds ) : self.__class__.maxchilds = len(self.childs['internal'])

    def do_textbox(self,element) :
        self.childs['internal'].append( ODP_TextBox(element) )

    def do_image(self,element):
        self.childs['internal'].append( ODP_Image(element) )

    def build(self, build_context):
        for i in self.childs:
            i.build(build_context)



class ODP_Image(ODP_Element):
    image_counter = 0

    def __init__(self , x_element):
        ODP_Element.__init__(self)

        self.namespace = 'image'
        self.name = self.namespace.upper()
        self.data = None

        self.attr_transform = [
            'draw:name',
            'xlink:href',
            'xlink:show',
            'xlink:type',
        ]

        self.triggers.update({
            'draw:image' : self.do_attributes,
            'draw:fill-image' : self.do_attributes,
            'text:p' : self.do_textp,
        })

        self.__class__.image_counter += 1
        self.options.update({self.namespace + ':name' : ''})
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,None)

        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

        if (self.options[self.namespace + ':name'] == '') : self.options.update( {self.namespace + ':name' : "Pict_%04d" % self.__class__.image_counter } )


    def do_textp(self, element):
        self.childs['internal'].append( ODP_TextP(element) )

    def apply_pictures(self , pictures = {}) :
        if (len(pictures)>0) :
            picto =  pictures.get(self.options['xlink:href'] )
            if (picto) :
                self.data = {}
                self.data['file'] = picto[0]
                self.data['data'] = picto[1]
                self.data['type'] = picto[2]

    def build(self, build_context):
        build_ok = True
        if self.data != None :
            log_debug(' > Building image "%s"' % self.get_options('name'))
            img_io = StringIO.StringIO(self.data['data'])
            img = PIL.Image.open(img_io)
            ratio = (float(img.size[0]) / float(img.size[1]))

            #Resize the image if width or height are greater than 256
            if (img.size[0] > 256 ):
                img = img.resize((256 , int(256 / ratio)) , PIL.Image.BICUBIC)
            elif (img.size[1] > 256) :
                img = img.resize((int(256 * ratio) , 256) , PIL.Image.BICUBIC)

            tmpfile = tempfile.NamedTemporaryFile(suffix="BSM.png",delete=False)
 
            #Save the final image temporary
            img.save(tmpfile , 'PNG')
            tmpfile.flush()
            tmpfile.close()
            
            b_image = Blender.Image.Load("%s" % tmpfile.name)
            log_debug("Packing Image")
            b_image.setName(self.get_options('name'))
            b_image.pack()
            #b_image.setFilename(self.get_options('name'))

            #Remove temporary image file
            os.remove(tmpfile.name)
            

            log_debug("   PIL : name %s" % self.get_options('name') )
            log_debug("   PIL : mode = %s" % (img.mode) )
            log_debug("   PIL : format = %s" % (img.format) )
            log_debug("   PIL : size = %s " % (repr(img.size)) )
            log_debug("   PIL : ratio = %s " % (float(img.size[0]) / float(img.size[1])) )
            pil_data = img.getdata()

            b_texture = Blender.Texture.New(self.get_options('name'))
            b_texture.setImage(b_image)
            b_material = Blender.Material.New(self.get_options('name'))
            b_material.setTexture(0, b_texture , Blender.Texture.TexCo.UV , Blender.Texture.MapTo.COL)
            if (img.mode == 'RGBA') :
                b_material.mode |= Blender.Material.Modes.ZTRANSP
            blender_objects = {
                self.namespace + ':material' : b_material,
                self.namespace + ':texture' : b_texture,
                self.namespace + ':image' : b_image,
            }
            self.blender_objects.update( blender_objects )
        else : 
            build_ok = False

        return build_ok 
        

class ODP_PresentationPageLayout(ODP_Element) :
    def __init__(self , x_element):
        ODP_Element.__init__(self)
        self.namespace = 'presentation-page-layout'
        self.name = self.namespace.upper()
        self.triggers.update({
            'style:presentation-page-layout' : self.do_attributes,
        })

        self.attr_transform = [
            'style:name',
        ]
#        self.options.update({self.namespace + ':name' : ''})
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,None)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

class ODP_Style(ODP_Element):
    def __init__(self, x_element) :
        ODP_Element.__init__(self)
        
        self.namespace = 'style'
        self.name = self.namespace.upper()
        self.attr_transform = [
            'style:name',
            'style:family',
            'style:parent-style-name',
        ]

        self.drawing_page_properties = None
        self.graphic_properties = None
        self.text_properties = None
        self.paragraph_properties = None

        self.triggers.update({
            'style:style' : self.do_attributes,
            'style:drawing-page-properties' : self.do_drawing_page_properties,
            'style:graphic-properties' : self.do_graphic_properties,
            'style:text-properties' : self.do_text_properties,
            'style:paragraph-properties' : self.do_paragraph_properties,
        })
        self.options.update({self.namespace + ':name' : ''} )
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

    def do_paragraph_properties(self, element):
        self.childs['internal'].append( ODP_ParagraphProperties(element) )

    def do_drawing_page_properties(self, element):
        self.childs['internal'].append( ODP_DrawingPageProperties(element) )

    def do_graphic_properties(self, element):
        self.childs['internal'].append( ODP_GraphicProperties(element) )

    def do_text_properties(self, element):
        self.childs['internal'].append( ODP_TextProperties(element) )

    def merge_style( self, style_list) :
        parent_style_name = self.options.get('style:parent-style-name')
        if (parent_style_name ):
            parent_style = style_list.get(parent_style_name)
            if (parent_style) :
                for parent_prop in parent_style.childs['internal'] :
                    update = False
                    for prop in self.childs['internal'] :
                        if prop.namespace == parent_prop.namespace :
                            update = True
                            new_options = {}
                            new_options.update(parent_prop.options)
                            new_options.update(prop.options)
                            prop.options = new_options

                    if update == False :
                        self.childs['internal'].append(parent_prop)
                        

class ODP_ParagraphProperties( ODP_Element ):
    def __init__(self, x_element):
        ODP_Element.__init__(self)
        self.namespace = 'paragraph-properties'
        self.name = self.namespace.upper()
        self.triggers.update({
            'style:paragraph-properties' : self.do_attributes,
        })

        self.attr_transform = [
            'fo:margin-top',
            'fo:margin-right',
            'fo:margin-bottom', 
            'fo:margin-left',
            'fo:text-indent',
        ]

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False

        self.parse_tree(x_element,0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

class ODP_GraphicProperties(ODP_Element):
    def __init__(self, x_element):
        ODP_Element.__init__(self)
        self.namespace = 'graphic-properties'
        self.name = self.namespace.upper()

        self.triggers.update({
            'style:graphic-properties' : self.do_attributes,
        })


        self.attr_transform = [
            'draw:fill-image-name',
            'style:repeat',
            'draw:fill-image-width',
            'draw:fill-image-height',
            'draw:fill',
            'draw:background-size',
        ]
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False

        self.parse_tree(x_element,0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

class ODP_TextProperties(ODP_Element):
    def __init__(self, x_element):
        ODP_Element.__init__(self)
        self.namespace = 'text-properties'
        self.name = self.namespace.upper()

        self.triggers.update({
            'style:text-properties' : self.do_attributes,
        })

        self.attr_transform = [
            'fo:font-family',
            'fo:font-weight',
            'fo:font-style',
            'fo:font-size',
            'style:font-weight-complex',
            'style:font-family-generic',
            'style:text-underline-style',
            'style:text-underline-color',
            'style:text-underline-width',
            'style:use-window-font-color',
            'fo:text-shadow',
            'style:font-relief',
        ]

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False

        self.parse_tree(x_element,0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp
        

class ODP_DrawingPageProperties(ODP_Element) :

    def __init__(self, x_element):
        ODP_Element.__init__(self)

        self.namespace = 'drawing-page-properties'
        self.name = self.namespace.upper()

        self.triggers.update({
            'style:drawing-page-properties' : self.do_attributes,
        })
        self.attr_transform = [
            'draw:fill-image-name',
            'style:repeat',
            'draw:fill-image-width',
            'draw:fill-image-height',
            'draw:fill',
            'draw:background-size',
        ]

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False

        self.parse_tree(x_element,0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

class ODP_MasterPage(ODP_Element) :
    def __init__(self, x_element) :
        ODP_Element.__init__(self)

        self.namespace = 'masterpage'
        self.name = self.namespace.upper()
        self.attr_transform = [
            'style:name',
            'style:page-layout-name',
            'draw:style-name',
        ]
        self.triggers.update({
            'style:master-page' : self.do_attributes,
        })

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False

        self.parse_tree(x_element,0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp



class ODP_PageLayout(ODP_Element) :
    def __init__(self, x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'pagelayout'
        self.name = self.namespace.upper()
        self.attr_transform = [
            'style:name',
            'fo:margin-top',
            'fo:margin-left',
            'fo:margin-bottom',
            'fo:margin-right',
            'fo:page-width',
            'fo:page-height',
            'style:print-orientation',
        ]

        self.triggers.update({
            'style:page-layout-properties' : self.do_attributes,
            'style:page-layout' : self.do_attributes,
        })
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element,0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

    def do_page_layout_properties(self , element) :
        self.childs['internal'].append( ODP_PageLayoutProperties(element) )

class ODP_PageLayoutProperties( ODP_Element ) :
    def __init__(self, x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'page-layout-properties'
        self.name = self.namespace.upper()
        self.attr_transform = [
        ]

        self.triggers.update({
            'style:page-layout-properties' : self.do_attributes,
        })
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element,0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

class ODP_Page(ODP_Element) :

    page_counter = 0

    def __init__( self, x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'page'
        self.name = self.namespace.upper()
        self.attr_transform = [
            'draw:name',
            'presentation:use-footer-name',
            'presentation:use-date-time-name',
            'presentation:presentation-page-layout-name',
            'draw:master-page-name',
            'draw:style-name',
        ]
        self.__class__.page_counter+=1

        self.options.update( { self.namespace + ':number' : self.page_counter } )

        self.triggers.update({
            'draw:page' : self.do_attributes,
            'draw:frame' : self.do_frame,
        })
        
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element , 1 , 2)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

    def do_frame(self,element):
        self.childs['internal'].append( ODP_Frame(element) )

    def build( self , build_context) :
        b_scene = build_context.blender['scene']
        
        i_current_page_number = self.get_options('number')
        len_pagenum = len("%s" % self.__class__.page_counter)
        i_name = ("Page_%0"+str(len_pagenum)+"d") % ( i_current_page_number )
        
        i_position = { 
            'x':0 , 
            'y':1 * ( i_current_page_number ) , 
            'z':0 
        }
        
        ratio_x = float( self.options['fo:page-width'].replace('cm','') )
        ratio_y = float( self.options['fo:page-height'].replace('cm','') )
        coord = [ [ratio_x/2,0,ratio_y/2] , [ratio_x/2,0,-ratio_y/2] , [-ratio_x/2,0,-ratio_y/2] , [-ratio_x/2 , 0 , ratio_y/2] ]
        faces = [ [ 3 , 2 , 1 , 0] ]

        me = bpy.data.meshes.new(i_name)

        me.verts.extend(coord)
        me.faces.extend(faces)
        uv = ( Mathutils.Vector([1,0]) , Mathutils.Vector([1,1]) , Mathutils.Vector([0,1]) , Mathutils.Vector([0,0]) )
        for i in me.faces:
            i.uv = uv

        b_material = self.get_blender_object('material' , 'image')
        me.materials = [b_material]

        b_page = build_context.blender['scene'].objects.new(me)

        b_page.setLocation( i_position['x'] , i_position['y'] , i_position['z'] )
        b_page.makeDisplayList() 
        
        build_context.blender['slides'].makeParent([b_page],0,0)

        for frame in self.childs['internal']:
            frame.build(build_context)


class ODP_Presentation(ODP_Element) :
    
    def __init__( self, x_document , build_context) :
        ODP_Element.__init__(self)
        self.namespace = 'presentation'
        self.name = self.namespace.upper()
        
        self.fillimages = {}
        for i in x_document.getElementsByType(draw.FillImage):
            img = ODP_Image(i)
            img.apply_pictures(x_document.Pictures)
            if (img.build(build_context)) :
                log_debug(img.blender_objects)
            log_debug(img)
            self.fillimages[img.options['draw:name']] = img 

        self.images = {}
        for i in x_document.getElementsByType(draw.Image):
            img = ODP_Image(i)
            img.apply_pictures(x_document.Pictures)
            if (img.build(build_context)) :
                log_debug(img.blender_objects)
            log_debug(img)
            self.images[img.options['image:name']] = img 

#        self.presentationpagelayouts = {}
#        for i in x_document.getElementsByType(style.PresentationPageLayout) :
#            ppl = ODP_PresentationPageLayout(i)
#            log_debug(ppl)
#            self.presentationpagelayouts[ppl.options['style:name']] = ppl

        self.styles = {}
        for i in x_document.getElementsByType(style.Style):
            s = ODP_Style(i)
            s.apply(self.fillimages , 'draw:fill-image-name')
            #log_debug(s)
            self.styles[s.options['style:name']] = s

        for i in self.styles.keys() :
            #print "PLOP" , i,type(i),type(self.styles[i])
            self.styles[i].merge_style(self.styles)
            log_debug(self.styles[i])

        self.pagelayouts = {} 
        for i in x_document.getElementsByType(style.PageLayout) :
            pl = ODP_PageLayout(i)
            log_debug(pl)
            self.pagelayouts[pl.options['style:name']] = pl

        self.masterpages = {}
        for i in x_document.getElementsByType(style.MasterPage) :
            mp = ODP_MasterPage(i)
            mp.apply(self.pagelayouts, 'style:page-layout-name')
            mp.apply(self.styles , 'draw:style-name')
            log_debug(mp)
            self.masterpages[mp.options['style:name']] = mp

        self.pages = []
        for i in x_document.getElementsByType(draw.Page):
            p = ODP_Page(i)
            p.apply(self.masterpages , 'draw:master-page-name')
            log_debug(p)
            self.pages.append(p)

        build_context.images = self.images

#        log_debug('MAXIMUM CHILDS PER FRAME : %d' % ( ODP_Frame.maxchilds ) )

    def build( self , build_context ) :

        for i_page in self.pages :
            i_page.build(build_context)

    def __str__(self):
        str = ""
        str += "|PRESENTATION\n"
        str += "=====\n"

        for p in self.pages:
            str += "%s\n" % p
        return str



if __name__ == '__main__':

    # TODO : Verify if script is installed in the plugins Blender directory

    odp_file = ''

    if Blender.mode == 'background' or Blender.mode == 'interactive':
        real_argv_index = sys.argv.index('--') + 1
        real_argv=sys.argv[real_argv_index:]

        from optparse import OptionParser
        prog_usage = "usage: blender -b -P %prog -- [options] filename"
        prog_name = "odp_importer.py"
        parser = OptionParser(usage=prog_usage,prog=prog_name)

        # TODO : add --text3d option to transform texts in images or 3D text ( may speed up things on eeepc )
        # TODO : think about other options (animations speed , slideshow automatic ... may change along themes )
        
        parser.add_option("-q", "--quiet",
                          action="store_false", dest="verbose", default=True,
                          help="don't print status messages to stdout")

        (prog_options, prog_args) = parser.parse_args(real_argv)
        print prog_options , prog_args


        if len(prog_args) == 0:
            parser.print_help()
            parser.error("You must provide at least a filename")
        if len(prog_args) > 1:
            parser.print_help()
            parser.error("You must provide JUST ONE filename")
        if Blender.sys.exists(prog_args[0]) != 1:
            parser.print_help()
            parser.error("File '%s' does not exist or is not a file" % (prog_args[0]))
            
    odp_file = prog_args[0]

    print odp_file    

    doc = load(odp_file)

    log_debug("opendocument import with Blender in %s mode" % (Blender.mode) )


    #Initialization of fonts & others things
    build_context = BuildContext()

    #Parse ODP file
    op = ODP_Presentation(doc, build_context)
    op.build(build_context)

    #Convert and build the new blender presentation
    #op.build(build_context)

    #Save the blender presentation
    blender_file = Blender.sys.makename(odp_file,'.blend')
    Blender.PackAll()
    Blender.Save(blender_file,1)
    print "Blender File created at '%s'" % (blender_file)

