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

def log_debug(line):
    if prog_options.verbose:
        print 'DEBUG:\t%s' % line

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

    def __init__(self) :
        self.namespace = 'element'
        self.name = self.namespace.upper()
        self.triggers = {}
        self.attr_transform = {}
        self.options = {}
        self.tags_ignored = ''
        self.blender_objects = {}
        self.text = None

    def parse_tree(self, element, level=0 , stop_level=0 , filter_tags = True):

        if ( (stop_level != None and level > stop_level) ) : return

        log_debug('%s %s >%s' %( '---+' * level , self.name , element.tagName) )
#        self.do_attributes(odp_element, level)
        if ( filter_tags and ( element.tagName in self.triggers.keys() ) ) : 
            method = self.triggers.get(element.tagName)
            if method : method(element = element)
        else :
            self.tags_ignored += element.tagName + ' '

        if element.childNodes:
            for child in element.childNodes:
                self.parse_tree(child, level + 1 , stop_level , filter_tags)
        else :
            if (element.tagName == 'Text') :
                log_debug("%s TEXT  :\"%s\"" % ('---+' * level , element) )

    def do_attributes(self, element, level = 0 , set_options = True):
        indentation = ( '    ' * (level + 1) )
        if (element != None) : log_debug("Doing attributes for element %s" % ( element.tagName) )
        if element.attributes != None:
            #log_debug("Element %s has attributes!" % ( element.tagName ) )
            for attkey in element.attributes.keys():
                attvalue = unicode(element.attributes[attkey]).encode('utf-8')
                log_debug( "%s[attr %s=%s]" % ( indentation , attkey , attvalue) )
                if (set_options) :
                    if (attkey in self.attr_transform) : self.options[self.attr_transform[attkey]] = attvalue
                    else :
                        if (not self.options.get('_useless_')) : self.options['_useless_'] = '' 
                        self.options['_useless_'] += attkey + ' '

    def debug_attributes(self, element, level = 0 , set_options = False):
        self.do_attributes(element, level , set_options)

    def do_nothing(self):
        return

    def apply(self, list , attribute_name) :
        noerror = True
        att_name = self.namespace + ':' + attribute_name
        if self.options.get(att_name) :
            att_value = self.options.get(att_name)
            element = None
            if (list != None and list.get(att_value) ) :
                element = list.get(att_value)
                self.options.update(element.options)
                self.blender_objects.update(element.blender_objects)
            else :
                noerror = False
        else :
            noerror = False

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

    def __str__(self) :
        return "%s %s" % (self.name , self.options)

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
#        log_debug("SLIDES > %s" % (self.blender['slides'].properties.keys()) )
#        log_debug("SLIDES > type %s" % ( type(self.blender['slides'].properties) ) )

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
        

#    # Font loading
#    def strip_fontconfig_family(self,family):
#        # remove alt name
#        n = family.find(',')
#        if n > 0:
#            family = family[:n]
#        family = family.replace("\\-", "-")
#        family = family.strip()
#        return family
#
#    def load_fonts(self):
#        cmd = "fc-list : file family style"
#        for l in os.popen(cmd).readlines() :
#            l = l.strip()
#            if l.find(':') < 0:
#                continue
#            file, family , style = l.split(':')
#            family = self.strip_fontconfig_family(family)
#            style = style.split('=')[-1].split(',')[0]
#            if style == 'Normal': style = 'Regular'
##            print family , style
#            if self.font_list.get(family,None) == None:
#                self.font_list[family] = {}
#            self.font_list[family][style]={'path':file}
#
#        for family,styles in self.font_list.iteritems():
#            for style , file in styles.iteritems():
#                blender_font = Text3d.Font.Load(file['path'])
#                file['blender'] = blender_font
#                #print file['blender']

class ODP_TextList(ODP_Element):
    def __init__( self, x_element) :
        ODP_Element.__init__(self) 
        self.namespace = 'text-list'
        self.name = self.namespace.upper()
        self.data = None
#        self.options.update( {self.namespace + ':name' : ''} )
        
        self.triggers = {
            'text:list' : self.do_attributes,
        }

        self.list = []

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = True
        self.parse_tree(x_element, 0,None)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp
        

class ODP_TextSpan(ODP_Element):
    def __init__( self, x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'text-p'
        self.name = self.namespace.upper()
        self.data = None
#        self.options.update( {self.namespace + ':name' : ''} )
        
        self.triggers = {
            'text:span' : self.do_attributes,
        }

        self.list = []

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = True
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp
   
    def __str__(self):
        str = ""
        str += "                    | %s\n" % self.name
        if (self.text != None) :
            str+="                   | %s\n" % (self.text)
        str += "                    ===="
        return str

class ODP_TextP(ODP_Element):
    
    def __init__( self, x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'text-p'
        self.name = self.namespace.upper()
        self.data = None
#        self.options.update( {self.namespace + ':name' : ''} )
        
        self.triggers = {
            'text:p' : self.do_attributes,
            'text:span' : self.do_textspan,
        }

        self.list = []

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = True
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

    def do_textspan(self, element):
        self.list.append( ODP_TextSpan(element) )

    def build( self , build_context) :
        self.do_nothing()

    def __str__( self ) :
        str = ""

        str+="                   |%s\n" % (self.name)
        if (self.text != None) :
            str+="                   | %s\n" % (self.text)
        str+="                   =====\n"
        
        return str

class ODP_TextBox(ODP_Element) :
    textbox_counter = 0

    def __init__( self , x_element):
        ODP_Element.__init__(self)
        self.namespace = 'text-box'
        self.name = self.namespace.upper()
        self.data = None

        self.__class__.textbox_counter += 1
        self.options.update( {self.namespace + ':number' : self.__class__.textbox_counter} )
        
        self.triggers = {
            'draw:text-box' : self.do_attributes,
            'text:p' : self.do_textp,
            'text:list' : self.do_textlist,
        }

        self.texts = []

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = True
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp
       
    def do_textp(self, element):
        self.texts.append( ODP_TextP(element) )

    def do_textlist(self, element):
        self.texts.append( ODP_TextList(element) )
 
    def build( self , build_context) :
        self.do_nothing()

    def __str__( self ) :
        str = ""
        str += "             |TEXTBOX\n"
        str += "             =====\n"
        for text in self.texts :
            str += "%s" % (text)
        return str

class ODP_Frame(ODP_Element) :
    frame_counter = 0    

    def __init__(self,x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'frame'
        self.name = self.namespace.upper()
        self.data = None

        self.frame_elements = []

        self.attr_transform = {
            'svg:x' : self.namespace + ':x',
            'svg:y' : self.namespace + ':y',
            'svg:width' : self.namespace + ':width',
            'svg:height' : self.namespace + ':height',
            'draw:layer' : self.namespace + ':layer',
            'presentation:class' : self.namespace + ':pr-class',
            'presentation:style-name' : self.namespace + ':pr-style',
            'draw:id' : self.namespace + ':id',
            'presentation:user-transformed' : self.namespace + 'user-transformed',
            
        }
        self.triggers = {
            'draw:frame' : self.do_attributes,
            'draw:text-box' : self.do_textbox,
            'draw:image' : self.do_image,
        }

        self.__class__.frame_counter += 1
        self.options.update( {self.namespace + ':number' : self.__class__.frame_counter} )
        
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = True
        self.parse_tree(x_element, 0,1)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

    def do_textbox(self,element) :
        self.frame_elements.append( ODP_TextBox(element) )

    def do_image(self,element):
        self.do_nothing()

    def build(self, build_context):
        for i in self.frame_elements:
            i.build(build_context)

    def __str__(self):
        str=""
        str+="         |FRAME \n"
        str+="         =====\n"

        for i in self.frame_elements :
            str += "%s" % i

        return str

class ODP_Image(ODP_Element):
    image_counter = 0

    def __init__(self , x_element):
        ODP_Element.__init__(self)

        self.namespace = 'image'
        self.name = self.namespace.upper()
        self.data = None

        self.attr_transform = {
            'draw:name'     : self.namespace + ':name',
            'xlink:href'    : self.namespace + ':href',
            'xlink:show'    : self.namespace + ':show',
            'xlink:type'    : self.namespace + ':type',
        }
        self.triggers = {
            'draw:image' : self.do_attributes,
            'draw:fill-image' : self.do_attributes,
            'text:p' : self.debug_attributes,
        }

        self.__class__.image_counter += 1
        self.options.update({self.namespace + ':name' : ''})
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,None)

        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

        if (self.options[self.namespace + ':name'] == '') : self.options.update( {self.namespace + ':name' : "Picture_%04d" % self.__class__.image_counter } )


    def apply_pictures(self , pictures = {}) :
        if (len(pictures)>0) :
            picto =  pictures.get(self.get_options('href') )
            if (picto) :
                self.data = {}
#                print type(picto) , len(picto)
                self.data['file'] = picto[0]
#                print 'file %s ' % self.data['file']
                self.data['data'] = picto[1]
#                print 'data %s ' % self.data['data'][0:20]
                self.data['type'] = picto[2]
#                print 'type %s ' % self.data['type'][0:20]

    def build(self, build_context):
        build_ok = True
        if self.data != None :
            log_debug(' > Building image "%s"' % self.get_options('name'))
            img_io = StringIO.StringIO(self.data['data'])
            img = PIL.Image.open(img_io)
            ratio = (float(img.size[0]) / float(img.size[1]))

#            #Resize the image if width or height are greater than 256
            if (img.size[0] > 256 ):
                img = img.resize((256 , int(256 / ratio)) , PIL.Image.BICUBIC)
            elif (img.size[1] > 256) :
                img = img.resize((int(256 * ratio) , 256) , PIL.Image.BICUBIC)

            tmpfile = tempfile.NamedTemporaryFile(suffix="BSM.png",delete=False)
#            print dir(tmpfile) , tmpfile.name
 
            #Save the final image temporary
            img.save(tmpfile , 'PNG')
            tmpfile.flush()
            tmpfile.close()
            
            b_image = Blender.Image.Load("%s" % tmpfile.name)
            log_debug("Packing Image")
            b_image.setName(self.get_options('name'))
            b_image.pack()
            #b_image.setFilename(self.get_options('name'))

#            os.remove(tmpfile.name)
            

            log_debug("   PIL : name %s" % self.get_options('name') )
            log_debug("   PIL : mode = %s" % (img.mode) )
            log_debug("   PIL : format = %s" % (img.format) )
            log_debug("   PIL : size = %s " % (repr(img.size)) )
            log_debug("   PIL : ratio = %s " % (float(img.size[0]) / float(img.size[1])) )
            pil_data = img.getdata()

#            for i in range(0,len(pil_data)):
#                x = i % img.size[0]
#                y = i / img.size[0]
#                print blender_obj.getPixelI(x,y)

            b_texture = Blender.Texture.New(self.get_options('name'))
            b_texture.setImage(b_image)
            b_material = Blender.Material.New(self.get_options('name'))
            b_material.setTexture(0, b_texture , Blender.Texture.TexCo.UV , Blender.Texture.MapTo.COL)
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
        self.namespace = 'presentationpagelayout'
        self.name = self.namespace.upper()
        self.attr_transform = {
        }
        self.triggers = {
            'style:presentation-page-layout' : self.debug_attributes,
            'presentation:placeholder' : self.debug_attributes,
        }

        self.options.update({self.namespace + ':name' : ''})
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
        self.attr_transform = {
            'style:name' : self.namespace+':name',
            'style:family' : self.namespace + ':family',
            'draw:fill-image-name' : self.namespace + ':fillimage',
        }
        self.triggers = {
            'style:style' : self.do_attributes,
            'style:drawing-page-properties' : self.do_attributes,
            #'style:graphic-properties' : self.do_attributes,
        }
        self.options.update({self.namespace + ':name' : ''} )
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element, 0,None)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp


class ODP_MasterPage(ODP_Element) :
    def __init__(self, x_element) :
        ODP_Element.__init__(self)

        self.namespace = 'masterpage'
        self.name = self.namespace.upper()
        self.attr_transform = {
            'style:name'                : self.namespace + ':name',
            'style:page-layout-name'    : self.namespace + ':pagelayout',
            'draw:style-name'           : self.namespace + ':style',
        }
        self.triggers = {
            'style:master-page' : self.do_attributes,
            'draw:frame' : self.debug_attributes,
        }

        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False

        self.parse_tree(x_element,0,0)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp



class ODP_PageLayout(ODP_Element) :
    def __init__(self, x_element) :
        ODP_Element.__init__(self)
        self.namespace = 'pagelayout'
        self.name = self.namespace.upper()
        self.attr_transform = {
            'style:name'                : self.namespace + ':name',
            'fo:margin-top'             : self.namespace + ':margin-top',
            'fo:margin-left'            : self.namespace + ':margin-left',
            'fo:margin-bottom'          : self.namespace + ':margin-bottom',
            'fo:margin-right'           : self.namespace + ':margin-right',
            'fo:page-width'             : self.namespace + ':width',
            'fo:page-height'            : self.namespace + ':height',
            'style:print-orientation'   : self.namespace + ':orientation',
        }

        self.triggers = {
            'style:page-layout-properties' : self.do_attributes,
            'style:page-layout' : self.do_attributes,
        }
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
        self.attr_transform = {
            'draw:name' : self.namespace + ':name',
            'presentation:use-footer-name' : self.namespace + ':usefooter',
            'presentation:use-date-time-name' : self.namespace + ':usedatetime',
#            'presentation:presentation-page-layout-name' : 'page:presentationpagelayout',
            'draw:master-page-name' : self.namespace + ':masterpage',
            'draw:style-name' : self.namespace + ':style',
        }
        self.__class__.page_counter+=1
        self.frames = []

        self.options.update( { self.namespace + ':number' : self.page_counter } )

        self.triggers = {
            'draw:page' : self.do_attributes,
            'draw:frame' : self.do_frame,
        }
        
        global prog_options
        verbose_tmp = prog_options.verbose
        prog_options.verbose = False
        self.parse_tree(x_element , 1 , 2)
        log_debug('attributes %s' % (self.options) )
        prog_options.verbose = verbose_tmp

    def do_frame(self,element):
        self.frames.append( ODP_Frame(element) )
#        self.do_nothing()

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
        ratio_x = float( self.get_options('width' , 'pagelayout').replace('cm','') )
        ratio_y = float( self.get_options('height' , 'pagelayout').replace('cm',''))
        coord = [ [ratio_x/2,0,ratio_y/2] , [ratio_x/2,0,-ratio_y/2] , [-ratio_x/2,0,-ratio_y/2] , [-ratio_x/2 , 0 , ratio_y/2] ]
        faces = [ [ 3 , 2 , 1 , 0] ]

        me = bpy.data.meshes.new(i_name)
        #print me

        me.verts.extend(coord)
        me.faces.extend(faces)
        uv = ( Mathutils.Vector([1,0]) , Mathutils.Vector([1,1]) , Mathutils.Vector([0,1]) , Mathutils.Vector([0,0]) )
        for i in me.faces:
            i.uv = uv

        b_material = self.get_blender_object('material' , 'image')
        me.materials = [b_material]

        b_page = build_context.blender['scene'].objects.new(me)

        

        #build_context.create_blender_page(build_context.doc['page_size']['width'] , build_context.doc['page_size']['height'],i_name , self.bg_data, self.bg_name)
        #b_page = build_context.blender['page']

        b_page.setLocation( i_position['x'] , i_position['y'] , i_position['z'] )
        b_page.makeDisplayList() 
        
        build_context.blender['slides'].makeParent([b_page],0,0)
        #build_context.blender['current_page_obj'] = b_page

        for i_frame in self.frames :
            i_frame.build(build_context)

    def __str__( self ) :
        str = ""
        str += "\t|PAGE\n"
        for o_key in self.options.keys():
            str += "\t| %-15s -> %s\n" % (o_key , self.options[o_key])
        str += "\t=====\n"
        for frame in self.frames :
            str += "%s" % (frame)
        return str


        

class ODP_Presentation(ODP_Element) :
    
    def __init__( self, x_document , build_context) :
        ODP_Element.__init__(self)
        self.namespace = 'presentation'
        self.name = self.namespace.upper()
        
        self.triggers = {
            'presentation:footer-decl'          : self.do_footer,
            'presentation:date-time-decl'       : self.do_datetime,
            'presentation:settings'             : self.do_settings,
        }

        self.pages = []
        self.page_current_number = 0
        
        self.footer = {}
        self.datetime = {}
        self.styles = {}

#        for i in x_document.Pictures.keys() :
#            print i

        self.fillimages = {}
        for i in x_document.getElementsByType(draw.FillImage):
            img = ODP_Image(i)
            img.apply_pictures(x_document.Pictures)
            if (img.build(build_context)) :
                log_debug(img.blender_objects)
            log_debug(img)
            self.fillimages[img.options['image:name']] = img 

        self.images = {}
        for i in x_document.getElementsByType(draw.Image):
            img = ODP_Image(i)
            img.apply_pictures(x_document.Pictures)
            if (img.build(build_context)) :
                log_debug(img.blender_objects)
            log_debug(img)
            self.images[img.options['image:name']] = img 

        self.presentationpagelayouts = {}
        for i in x_document.getElementsByType(style.PresentationPageLayout) :
            ppl = ODP_PresentationPageLayout(i)
            self.presentationpagelayouts[ppl.options['presentationpagelayout:name']] = ppl

        self.styles = {}
        for i in x_document.getElementsByType(style.Style):
            s = ODP_Style(i)
            if (s.apply(self.fillimages , 'fillimage')) :
                log_debug(s)
            self.styles[s.options['style:name']] = s

        self.pagelayouts = {} 
        for i in x_document.getElementsByType(style.PageLayout) :
            pl = ODP_PageLayout(i)
            self.pagelayouts[pl.options['pagelayout:name']] = pl

        self.masterpages = {}
        for i in x_document.getElementsByType(style.MasterPage) :
            mp = ODP_MasterPage(i)
            if mp.apply(self.pagelayouts, 'pagelayout') and mp.apply(self.styles , 'style') :
                log_debug(mp)
            self.masterpages[mp.options['masterpage:name']] = mp
        

        self.pages = []
        
        for i in x_document.getElementsByType(draw.Page):
            p = ODP_Page(i)
            if p.apply(self.masterpages , 'masterpage') :
                log_debug(p)
            self.pages.append(p)

        build_context.images = self.images
        
    def do_page(self, element):
        options = {'page:number':self.page_current_number}
        args = {'x_options' : options, 'x_styles' : self.styles}
        self.pages.append( ODP_Page(element,**args ) )
        self.page_current_number += 1

    def do_datetime(self, element):
        self.do_nothing()

    def do_footer(self,element):

        log_debug('doing a FOOTER element')
        if element.attributes != None:
            for attkey in element.attributes.keys():
                log_debug('\t' + str(attkey) + '=' + unicode(element.attributes[attkey]).encode('utf-8'))
        if element.childNodes:
            for e in element.childNodes:
                log_debug('\tFooter element : %s' % (e.tagName))
                if (e.tagName == 'Text') : log_debug('\t\tFooter Text : %s' % (e))

    def do_settings(self, element):
        log_debug('doing a SETTINGS element')

        if element.attributes != None:
            for attkey in element.attributes.keys():
                log_debug('\t' + str(attkey) + '=' + unicode(element.attributes[attkey]).encode('utf-8'))
        

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

