#!BPY

""" Registration info for Blender menus:
Name: 'OpenDocumentPresentation (.odp)'
Blender: 250
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
import Blender
from Blender import Text3d, Mesh, Camera, Mathutils,sys as bsys , Material
import bpy

import codecs
import sys
import os
import math

import urllib

import ImageFont,ImageFile,ImageDraw,Image

from odf.opendocument import load,OpenDocumentPresentation
from odf import text,presentation,draw,style,office

from reportlab.platypus.flowables import Flowable, PTOContainer, KeepInFrame
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.frames import Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import *
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, FrameBreak , PageBreak , NextPageTemplate
from reportlab.pdfgen import canvas

from reportlab import rl_config
from reportlab.lib.enums import *
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

#rl_config.shapeChecking = 0
#rl_config.overlapAttachedSpace= 0


global_fonts = {}

class BuildContext():
    
    def __init__(self):

        # TODO : remove this variable when style will be handled
        self.doc = {}
        self.doc['current_page'] = 0
        self.doc['current_frame'] = 0
        self.doc['current_frame'] = 0
        self.doc['current_element'] = 0
        self.doc['current_element_type'] = ""
        self.doc['current_line'] = 0
        self.doc['current_text'] = 0
        
        self.screen = { 'width' : 800, 'height' : 600 }

        self.font_list = {}
        self.load_fonts()

        #FIXME : Crappy hack because I run out of time :'(
        global global_fonts 
        global_fonts= self.font_list.copy()

        self.blender = {}
        self.game = {}
        self.init_blender_file()

    def init_blender_file(self):
        self.blender['scene'] = Blender.Scene.GetCurrent()
        
        self.blender['render'] = self.blender['scene'].getRenderingContext()
        self.blender['render'].enableGameFrameExpose()

#        self.blender['camera'] = Camera.New('persp', 'CamViewer')
#        self.blender['camera'].setLens(3.06)
#        self.blender['camera_object'] = self.blender['scene'].objects.new(self.blender['camera'])
#        self.blender['camera_object'].setLocation(6.7, -2.22 , 1)
#        self.blender['scene'].objects.camera = self.blender['camera_object']

        self.blender['text'] = Text3d.New("tmp_text") #Create the Text3d object
        self.blender['text'].setExtrudeDepth(0)    #Give some relief 
        self.blender['text'].setDefaultResolution(4)
        self.blender['text'].setSpacing(0.92)
        
        self.blender['text_object'] = self.blender['scene'].objects.new(self.blender['text'])
        self.blender['scene'].objects.unlink(self.blender['text_object'])
#        print dir(self.blender['text'])
        self.ratio_x = float( self.screen['width'] / ( self.screen['width'] % self.screen['height'] ) )
        self.ratio_y = float( self.screen['height'] / ( self.screen['width'] % self.screen['height'] ) )

        coord = [ [self.ratio_x/2,0,self.ratio_y/2] , [self.ratio_x/2,0,-self.ratio_y/2] , [-self.ratio_x/2,0,-self.ratio_y/2] , [-self.ratio_x/2 , 0 , self.ratio_y/2] ]
        faces = [ [ 3 , 2 , 1 , 0] ]
        
        me = bpy.data.meshes.new('Page')

        me.verts.extend(coord)
        me.faces.extend(faces)

        self.blender['page'] = self.blender['scene'].objects.new(me)
        self.blender['scene'].objects.unlink(self.blender['page'])


        self.blender['slides'] = Blender.Object.Get('Slides')

    # Font loading
    def strip_fontconfig_family(self,family):
        # remove alt name
        n = family.find(',')
        if n > 0:
            family = family[:n]
        family = family.replace("\\-", "-")
        family = family.strip()
        return family

    def load_fonts(self):
        cmd = "fc-list : file family style"
        for l in os.popen(cmd).readlines() :
            l = l.strip()
            if l.find(':') < 0:
                continue
            file, family , style = l.split(':')
            family = self.strip_fontconfig_family(family)
            style = style.split('=')[-1]
            if self.font_list.get(family,None) == None:
                self.font_list[family] = {}
            self.font_list[family][style]={'path':file}

        for family,styles in self.font_list.iteritems():
            for style , file in styles.iteritems():
                blender_font = Text3d.Font.Load(file['path'])
                file['blender'] = blender_font
                #print file['blender']

class ODP_Text():
    
    def __init__( self, x_text ,doc , styles , x_parent) :

        self.attributes = x_text.attributes
        self.id = x_text.getAttribute('id')
        self.style_name = x_text.getAttribute( 'stylename' )
        self.type = None
        if self.style_name == None:
            self.style_name = x_parent.style_name
        #    print "Text Style = %s" % self.style_name
        #else:
        #    print "Text Style = %s , Parent Style = %s" % (self.style_name , x_parent.style_name)

            

        self.cond_style_name = x_text.getAttribute( 'condstylename' )
        self.class_names = x_text.getAttribute( 'classnames' )
        self.level = 1
        parent = x_text.parentNode

        while (parent.tagName != 'draw:text-box') :
            if ( parent.parentNode.tagName == 'text:list-item') :
                self.level += 1
            if ( parent.parentNode.tagName == 'text:list') :
                self.type = 'list'
            parent = parent.parentNode

        #FIXME : the text may be contained in another text element :/ ... Fu#!@&ing XML
        tmp_text = x_text
        while(tmp_text != None):
            if hasattr(tmp_text.firstChild,'data'):
                x_text = tmp_text.firstChild.data
                break
            tmp_text = tmp_text.firstChild

        if (tmp_text == None) : x_text = ''

        if (self.type == None):
            self.text = x_text
        elif (self.type == 'list'):
            #FIXME : replace bullet character from the corresponding style
            self.text = '- ' + x_text
#            print repr(self.text) , dir(self.text)

#        doc.getStyleByName(self.style_name).attributes
        
        s = styles['styles'][self.style_name]
        if s.attributes.has_key('style:parent-style-name') :
            s = styles['styles'][s.attributes['style:parent-style-name']]

        s_parent = styles['styles'][x_parent.style_name]
        if s_parent.attributes.has_key('style:parent-style-name') :
            s_parent = styles['styles'][s_parent.attributes['style:parent-style-name']]

        para_prop = None
        text_prop = None
#        print para_prop.attributes
        #text_prop = s.getElementsByType(style.TextProperties)
        for i_style in [s,s_parent]:
            i_walk = True
            i_element = i_style.firstChild
            while i_walk == True:
                #print dir(i_element)
                if i_element.tagName == 'style:text-properties':
                    text_prop = i_element
                if i_element.tagName == 'style:paragraph-properties':
                    para_prop = i_element
                
                if (i_element.nextSibling != None) :
                    i_element = i_element.nextSibling
                else :
                    i_walk = False

        self.font = {}
        if para_prop != None : 
            #print para_prop.attributes
            text_align = para_prop.attributes['fo:text-align']
            if text_align == 'start': self.font['text-align'] = Text3d.LEFT
            elif text_align == 'center': self.font['text-align'] = Text3d.MIDDLE
            elif text_align == 'end': self.font['text-align'] = Text3d.RIGHT
            else: self.font['text-align'] = Text3d.LEFT
            
            
        else:
            #print "No paragraph style"
            self.font['text-align'] = Text3d.LEFT

        if text_prop != None : 
            i_font_family = text_prop.attributes['fo:font-family']
            i_font_style = text_prop.attributes['fo:font-style']
            i_font_size = text_prop.attributes['fo:font-size']
            i_font_underline = text_prop.attributes['style:text-underline-style']
            i_font_weight = text_prop.attributes['fo:font-weight']

        else: 
            #print "No text style"
            i_font_family = 'Liberation Sans'
            i_font_style = 'normal'
            i_font_size = '12pt'
            i_font_underline = 'none'
            i_font_weight = 'normal'

        self.font['font-family'] = i_font_family.strip("'")

        if i_font_style == 'italic' :
            self.font['font-style'] = 'Italic'
        elif i_font_style == 'normal' :
            self.font['font-style'] = 'Regular'


        self.font['font-size'] = float(i_font_size.replace("pt",""))

        if i_font_underline != 'none':
            self.font['font-underline'] = True
        
        if i_font_weight != 'normal' :
            self.font['font-weight'] = 'Bold'
        else: 
            self.font['font-weight'] = 'Regular'

        i_real_style = [self.font['font-weight'] , self.font['font-style']]
        if (i_real_style[0] == i_real_style[1] ) : self.font['real-style'] = i_real_style[0]
        elif (i_real_style[0] == 'Regular') : self.font['real-style'] = i_real_style[1]
        elif (i_real_style[1] == 'Regular') : self.font['real-style'] = i_real_style[0]
        else :self.font['real-style'] = " ".join(i_real_style)

        print self.font
        #print ""

        self.paragraph = None

        styleSheet = getSampleStyleSheet()

        self.styleSheet = styleSheet['BodyText']

        self.styleSheet.fontSize = self.font['font-size']
        if self.font['text-align'] == Text3d.LEFT:
            self.styleSheet.alignment = TA_LEFT 
        elif self.font['text-align'] == Text3d.RIGHT:
            self.styleSheet.alignment = TA_RIGHT
        elif self.font['text-align'] == Text3d.MIDDLE:
            self.styleSheet.alignement = TA_CENTER


        pdfmetrics.registerFont(TTFont(self.font['font-family'],global_fonts[self.font['font-family']][self.font['real-style']]['path']))

        self.styleSheet.fontName = self.font['font-family']

    def create_rl_text(self , story):
        
        self.paragraph = Paragraph(self.text.encode('utf-8'),self.styleSheet)
        return self.paragraph

    def debug_rl_story(self):
        #print { 'width':self.paragraph.width/cm , 'height':self.paragraph.height/cm , 'text':self.paragraph.text}
        print self.paragraph._fixedWidth , self.paragraph._fixedHeight 
        lines = []
        for l in self.paragraph.blPara.lines:
            lines.append(" ".join(l[1]))
        
#        self.font['font-size'] = self.paragraph.blPara.fontSize

#        print self.font

        self.text = urllib.quote("\n".join(lines) )
#        print urllib.unquote(self.text)

    def build( self , build_context) :
        build_context.doc['current_line'] += 1
        build_context.doc['current_text'] += 1
        i_page = build_context.doc['current_page']
        i_frame = build_context.doc['current_frame']
        i_frame_layout = build_context.doc['frame_layout']
        i_element = build_context.doc['current_element']
        i_element_type = build_context.doc['current_element_type']
        i_line = build_context.doc['current_line']
        i_line_offset = build_context.doc['line_offset']
        i_text = build_context.doc['current_text']
        
        i_ratio_x = build_context.ratio_x
        i_ratio_y = build_context.ratio_y

        i_font_size = (self.font['font-size'] * 0.01)
        print i_font_size
        build_context.doc['line_offset'] += (i_font_size )
        i_name = "Text_%d" % ( i_text )
        #print self.text.data.encode('utf-8')
        #i_text = str(self.text.encode('utf-8'))

        #i_text = self.text.encode('utf-8')
        i_text = urllib.unquote(self.text)

        #Calculation of base coordinates for the text

#        if self.font['text-align'] == Text3d.LEFT : i_start_x = -i_ratio_x/2.0
#        elif self.font['text-align'] == Text3d.RIGHT : i_start_x = i_ratio_x/2.0
#        else : i_start_x = 0
#
        i_start_x = -i_ratio_x/2.0
        i_start_y = i_ratio_y/2.0
        
        i_frame_x = i_start_x + i_frame_layout['x']
        i_frame_y = i_start_y - i_frame_layout['y']

        i_position_z = i_frame_y - i_line_offset - i_font_size# - 0.2 * ( i_line )
        i_position_x = i_frame_x + 0.2 * ( self.level - 1 )
        i_position_y = -0.01 #0.95 * ( i_page )

#        i_image_font =  ImageFont.truetype(build_context.font_list[self.font['font-family']][self.font['real-style']]['path'] , size=int(self.font['font-size']) , encoding='unic')
#        img = Image.new('RGB' , size=i_image_font.getsize(i_text))
#        draw = ImageDraw.Draw(img)
#        draw.text((0,0),i_text,font=i_image_font)
#        img.save('%s.png' % i_name)
#        print i_image_font.getsize(i_text)

        b_material = Material.New("Mat_%s" % i_name)
        b_material.rgbCol = [0.5 , 0.5 , 0.5]
        b_material.setMode('Shadeless')
 
        b_text = build_context.blender['text']
        
        #print b_text.activeFrame , b_text.totalFrames
        b_text.frameWidth = i_frame_layout['w']
        b_text.frameHeight = i_font_size#i_frame_layout['h']
        b_text.frameX = 0.0
        b_text.frameY = 0.0 # i_line_offset - i_font_size

        b_text_object = build_context.blender['text_object']
        b_scene = build_context.blender['scene']
        #print ("%r" % (self.text.data), i_name, b_text.getSize())
        b_text.setText(i_text)   #Set the text for Text3d object
        b_text.setAlignment(self.font['text-align'])
        b_text.setSize(i_font_size)
        b_text.setFont(build_context.font_list[self.font['font-family']][self.font['real-style']]['blender'] ) #Set the font to Text3d object
        b_mesh = Mesh.New(i_name)
        
        b_mesh.getFromObject(b_text_object,0,0)
        b_mesh.materials += [b_material]       
#        b_object.setMaterials([b_material])

        b_object = b_scene.objects.new(b_mesh)
        b_scene.objects.new(b_text)

        b_object.RotX = math.pi/2        
        
        b_object.setLocation( i_position_x , i_position_y , i_position_z )

        b_object.makeDisplayList()

        build_context.blender['current_page_obj'].makeParent([b_object],0,0)

    def __str__( self ) :
        str = ""

        str+="                   |TEXT\n"
        str+="                   | classnames    : %s\n" % (self.class_names)
        str+="                   | condstylename : %s\n" % (self.cond_style_name)
        str+="                   | stylename     : %s\n" % (self.style_name)
        str+="                   | id            : %s\n" % (self.id)
        #str+="                   | text          : %s\n" % (unicode(self.text))
        str+="                   | text          : %s\n" % (self.text)
        str+="                   | attributes    : %s\n" % (self.attributes)
        str+="                   | level         : %s\n" % (self.level)
        str+="                   =====\n"
        
        return str

class ODP_TextBox() :
    def __init__( self , x_textbox , doc , styles , parent):
        self.texts = []
        self.style_name = parent.style_name 

        self.addTextsFrom( x_textbox , doc , styles)

        self.paragraphs = [] 

        
    def create_rl_paragraphs(self , story):
        
        for i_text in self.texts :
            self.paragraphs.append(i_text.create_rl_text(story))

        return self.paragraphs

    def debug_rl_story(self):
        for i_text in self.texts :
            i_text.debug_rl_story()

    def addTextsFrom( self, x_textbox , doc , styles) :

        i_texts = x_textbox.getElementsByType(text.P)
        for i_text in i_texts:
            self.texts.append( ODP_Text(i_text , doc , styles , self) )

#        i_walk = True
#        i_element = x_textbox.firstChild
#        while ( i_walk == True ) :
#
#            if ( i_element.tagName == 'text:p' ) :
#                self.texts.append( ODP_Text( i_element ) )
#
#            if ( i_element.nextSibling != None ) :
#                i_element = i_element.nextSibling
#            else :
#                i_walk = False

    def build( self , build_context) :
        build_context.doc['current_element'] += 1
        build_context.doc['current_element_type'] = "tb"
        build_context.doc['line_offset'] = 0
        for n,i_text in enumerate(self.texts) :
            #build_context['line-number'] += 1
            i_text.build( build_context )

    def __str__( self ) :
        str = ""
        str += "             |TEXTBOX\n"
        str += "             =====\n"
        for text in self.texts :
            str += "%s" % (text)
        return str

class ODP_Frame() :

    def __init__( self, x_frame , doc , styles) :
#        self.style_name = x_frame.getAttribute( 'stylename') 
#        print x_frame.attributes

        #FIXME : odfpy can't find presentation:style-name with getAttribute
        if x_frame.attributes.has_key('presentation:style-name'): self.style_name = x_frame.attributes['presentation:style-name']
        else : self.style_name = x_frame.attributes['draw:style-name']
        self.class_name = x_frame.getAttribute( 'class' )
        self.width = float(x_frame.getAttribute( 'width' ).replace('cm',''))
        self.height = float(x_frame.getAttribute( 'height' ).replace('cm',''))
        self.x = float(x_frame.getAttribute( 'x' ).replace('cm',''))
        self.y = float(x_frame.getAttribute( 'y' ).replace('cm',''))
        self.zindex = x_frame.getAttribute( 'zindex' )
        self.frame_elements = []
        
        self.attributes = x_frame.attributes

        st_attr = styles['styles'][self.style_name].attributes

        #if st_attr.has_key('style:parent-style-name') : str_attr

        self.addElementsFrom(x_frame , doc , styles)

        self.rl_flowables = []
        self.rl_frame = None
        self.rl_keepinframe = None

    def create_rl_frame( self, story , page):
        
        for i_element in self.frame_elements:
            if isinstance(i_element,ODP_TextBox):
                self.rl_flowables.extend(i_element.create_rl_paragraphs(story) )

#        self.rl_flowables.append(FrameBreak())
#        print self.rl_flowables


        if len(self.rl_flowables) : 
            self.rl_keepinframe = KeepInFrame(self.width * cm,self.height * cm,self.rl_flowables,mode='shrink')
            story.append(self.rl_keepinframe)
            story.append(FrameBreak())
            self.rl_frame = Frame(self.x * cm, page.page_height*cm - self.y*cm - self.height* cm, self.width*cm, self.height*cm, leftPadding=0, bottomPadding=0 , rightPadding=0, topPadding=0)
            self.rl_frame._oASpace
        else :
            self.rl_frame = None
        return self.rl_frame

    def debug_rl_story(self):
        for i_element in self.frame_elements:
            if isinstance(i_element,ODP_TextBox):
                i_element.debug_rl_story()


    def addElementsFrom( self , x_frame , doc , styles) :
        
        i_walk = True
        i_element = x_frame.firstChild
        while ( i_walk == True ) :
            
            if ( i_element.tagName == 'draw:text-box' ) :
                self.frame_elements.append( ODP_TextBox( i_element , doc , styles , self) )

#            if ( i_element.tagName == 'draw:image' ) :
#                self.elements.append( ODP_Image( i_element ) )

            if ( i_element.nextSibling != None ) :
                i_element = i_element.nextSibling
            else :
                i_walk = False

    def build( self , build_context) :
        build_context.doc['current_element'] = 0
        build_context.doc['current_element_type'] = "None"
        build_context.doc['current_frame'] += 1


        i_page_size = build_context.doc['page_size']
        #print i_page_size
        #FIXME : Rename ratio_x and ratio_y in b_page_width and b_page_height
        i_ratio_x = build_context.ratio_x
        i_ratio_y = build_context.ratio_y

        i_frame_layout = {}
        i_frame_layout['w'] = self.width / i_page_size['width'] * i_ratio_x
        i_frame_layout['h'] = self.height/ i_page_size['height'] * i_ratio_y
        i_frame_layout['x'] = self.x / i_page_size['width'] * i_ratio_x
        i_frame_layout['y'] = self.y / i_page_size['height'] * i_ratio_y
        build_context.doc['frame_layout'] = i_frame_layout
        
        for i_element in self.frame_elements:
            i_element.build(build_context)

    def __str__(self):
        str=""
        str+="         |FRAME\n"
        str+="         | stylename: %s\n" % (self.style_name)
        str+="         | class    : %s\n" % (self.class_name)
        str+="         | width    : %s\n" % (self.width)
        str+="         | height   : %s\n" % (self.height)
        str+="         | x        : %s\n" % (self.x)
        str+="         | y        : %s\n" % (self.y)
        str+="         | zindex   : %s\n" % (self.zindex)
# For debugging purpose only
        str+="         | attributes: %s\n" % (self.attributes)
        str+="         =====\n"

        for i in self.frame_elements :
            str += "%s" % (i)

        return str

class ODP_Page() :

    def __init__( self, x_page , doc , styles) :
        
        self.name = ""
        self.frames = []
        self.number = 0
        self.attributes = x_page.attributes

        self.name = x_page.getAttribute('name')
        self.masterpage = x_page.attributes['draw:master-page-name']
        
        #self.layout

        if (len(styles['masterpages']) > 0) :
            self.layout = styles['masterpages'][self.masterpage].attributes['style:page-layout-name']

        print self.layout

        if self.layout != None:
            prop = styles['pagelayouts'][self.layout].getElementsByType(style.PageLayoutProperties)[0]
            self.page_width = float(prop.attributes['fo:page-width'].replace('cm',''))
            self.page_height = float(prop.attributes['fo:page-height'].replace('cm',''))

        self.addFramesFrom(x_page , doc , styles)

        self.rl_frames = []
        self.rl_page = None

    def create_rl_page( self , story):

        for i_frame in self.frames:
            rl_frame = i_frame.create_rl_frame(story,self)
            if rl_frame!=None:
                self.rl_frames.append(rl_frame)

        self.rl_page = PageTemplate(self.name, self.rl_frames , pagesize=(self.page_width*cm,self.page_height*cm))

#        story.append(PageBreak)
        return self.rl_page

    def debug_rl_story(self):
        for i_frame in self.frames:
            i_frame.debug_rl_story()


    def addFramesFrom( self , x_page , doc , styles) :

        i_walk = True
        i_element = x_page.firstChild
        while ( i_walk == True ) :
            #print i_element.tagName
            if ( i_element.tagName == 'draw:frame' ) :
                #FIXME : get Frame order with PageLayout
                self.frames.append( ODP_Frame(i_element , doc , styles) )
            if ( i_element.nextSibling != None ):
                i_element = i_element.nextSibling
            else :
                i_walk = False

    def build( self , build_context) :
        build_context.doc['current_line'] = 0         
        build_context.doc['current_frame'] = 0
        build_context.doc['current_page'] += 1
        build_context.doc['page_size'] = { 'width' : self.page_width , 'height':self.page_height }

        b_scene = build_context.blender['scene']
        i_page = build_context.doc['current_page']
        i_name = "Page_%d" % ( build_context.doc['current_page'] )
        
        i_position_z = 0
        i_position_x = 0
        i_position_y = 0#1 * ( i_page )
        
        b_page = build_context.blender['page']
        b_mesh = Mesh.New(i_name)
        b_mesh.getFromObject(b_page,0,0)
        b_object = b_scene.objects.new(b_mesh) 
        b_object.setLocation( i_position_x , i_position_y , i_position_z )
        b_object.makeDisplayList() 
        
        build_context.blender['slides'].makeParent([b_object],0,0)
        build_context.blender['current_page_obj'] = b_object


        for i_frame in self.frames :
            i_frame.build(build_context)

    def __str__( self ) :
        str = ""
        str += "    |PAGE %s\n" % (self.name)
        str += "    | number %s\n" % (self.number)
        str += "    | attributes %s\n" % (self.attributes)
        str += "    =====\n"
        for frame in self.frames :
            str += "%s" % (frame)
        return str

class ODP_Presentation() :
    
    def __init__( self, x_presentation, doc , styles) :
        self.footer = ""
        self.time = ""
        self.pages = []
        
        self.footer = x_presentation.getElementsByType( presentation.FooterDecl)[0].firstChild
        self.time = x_presentation.getElementsByType( presentation.DateTimeDecl)[0].getAttribute( 'source' )

        self.layout = None
        self.page_width = 0
        self.page_height = 0
        
        
#        for i in doc.getElementsByType(style.MasterPage):
#            print i.qname[1]
#            print i.attributes
#            self.layout = i.attributes['style:page-layout-name']

#        if (len(styles['masterpages']) > 0) :
#            styles['masterpages']. 
#            self.layout = styles['masterpages'][0].attributes['style:page-layout-name']
#
#        if self.layout != None:
#            prop = styles['pagelayouts'][self.layout].getElementsByType(style.PageLayoutProperties)
#            self.page_width = j.attributes['fo:page-width']
#            self.page_height = j.attributes['fo:page-height']
#            for i in doc.getElementsByType(style.PageLayout):
                #print i.qname[1]
#                if ( i.attributes['style:name'] == self.layout) :
#                    print i.qname[1]
#                    print i.attributes
#                    for j in i.getElementsByType(style.PageLayoutProperties):
#                        print j.qname[1]
#                        print j.attributes
#                        self.page_width = j.attributes['fo:page-width']
#                        self.page_height = j.attributes['fo:page-height']
        
        self.addPagesFrom(x_presentation , doc , styles)

        self.rl_doc = None
        self.story = []
        self.rl_pages = []

        self.create_rl_doc()

    def create_rl_doc(self):

        for i_page in self.pages:
            self.rl_pages.append( i_page.create_rl_page(self.story) )

#        self.rl_doc = BaseDocTemplate("Test.pdf",
#            pageTemplates = self.rl_pages,
#            showBoundary = 1,
#            verbose = False
#            )

        self.rl_doc = BaseDocTemplate("Test.pdf",
            pageTemplates = self.rl_pages,
            showBoundary = 1,
            verbose = False
            )

        print self.story
        #self.rl_doc.multiBuild(self.story,canvasMaker=canvas.Canvas(bottomup=1))
        self.rl_doc.multiBuild(self.story)
        self.debug_rl_story()

    def debug_rl_story(self):
        for i_page in self.pages:
            i_page.debug_rl_story()

    def addPagesFrom( self, x_presentation , doc, styles) :
        
        i_walk = True
        i_element = x_presentation.firstChild
        i_page_number = 0
        while (i_walk == True):

            if ( i_element.tagName == 'presentation:footer-decl') :
                self.footer = i_element.firstChild
        
            if ( i_element.tagName == 'presentation:datetime-decl' ) :
                self.time = i_element.getAttribute('source')
            
            if ( i_element.tagName == 'draw:page') :
                i_page_number += 1
                self.pages.append( ODP_Page( i_element , doc , styles) )
                self.pages[-1].number = i_page_number

            if (i_element.nextSibling != None) :
                i_element = i_element.nextSibling
            else :
                i_walk = False
                
    def build( self , build_context) :
        for i_page in self.pages :
            i_page.build(build_context)
    #    print(build_context)



    def __str__(self):
        str = ""
        str += "|PRESENTATION\n"
        str += "| Footer is %s\n" % (self.footer)
        str += "| Time is %s\n" % (self.time)
        str += "| Page Width %s\n" % (self.page_width)
        str += "| Page Height %s\n" % (self.page_height)
        str += "=====\n"
        for p in self.pages:
            str += "%s\n" % p
        return str


if __name__ == '__main__':

    # TODO: Verify if script is installed in the plugins Blender directory

    odp_file = ''
#    template_file = ''
    

#    print Blender.mode
    if Blender.mode == 'background' or Blender.mode == 'interactive':
#        print sys.argv
        real_argv_index = sys.argv.index('--') + 1
        real_argv=sys.argv[real_argv_index:]
#        print real_argv

        from optparse import OptionParser
        usage = "usage: blender -b -P %prog -- [options] filename"
        prog = "odp_importer.py"
        parser = OptionParser(usage=usage,prog=prog)
        
        parser.add_option("-q", "--quiet",
                          action="store_false", dest="verbose", default=True,
                          help="don't print status messages to stdout")
#        parser.add_option("-t", "--template",
#                          dest="template", default="template_coverflow",
#                          help="specifies a Blender template [default = %default]")

        (options, args) = parser.parse_args(real_argv)
        print options , args

#        template_file = Blender.sys.expandpath("//blender_templates/%s.blend" % (options.template))

        if len(args) == 0:
            parser.print_help()
            parser.error("You must provide at least a filename")
        if len(args) > 1:
            parser.print_help()
            parser.error("You must provide JUST ONE filename")
        if Blender.sys.exists(args[0]) != 1:
            parser.print_help()
            parser.error("File '%s' does not exist or is not a file" % (args[0]))
#        if Blender.sys.exists(template_file) != 1:
#            parser.print_help()
#            parser.error("Template '%s' does not exist or is not a file" % (template_file) )
            
    odp_file = args[0]
#    Blender.Load(template_file)

    print odp_file    
#    print template_file
    doc = load(odp_file)
    print ("DEBUG opendocument import with Blender in %s mode" % (Blender.mode))

    styles = {}
    styles['masterpages'] = {}
    styles['pagelayouts'] = {}
    styles['styles'] = {}
    
    for i in doc.getElementsByType(style.Style) :
        styles['styles'][i.attributes['style:name']] = i

    for i in doc.getElementsByType(style.MasterPage) :
        styles['masterpages'][i.attributes['style:name']] = i
    
    for i in doc.getElementsByType(style.PageLayout) :
        styles['pagelayouts'][i.attributes['style:name']] = i

    

    build_context = BuildContext()
    op = ODP_Presentation(doc.presentation , doc , styles)
    print (unicode(op))
    op.build(build_context)

#    for i in doc.getElementsByType(style.MasterPage):
#        print i.qname[1]
#        print i.attributes
#    for i in doc.getElementsByType(style.PageLayout):
#        print i.qname[1]
#        print i.attributes
#        for j in i.getElementsByType(style.PageLayoutProperties):
#            print j.qname[1]
#            print j.attributes
    
    blender_file = Blender.sys.makename(odp_file,'.blend')
    Blender.Save(blender_file,1)
    print "Blender File created at '%s'" % (blender_file)

#Blender.Quit()
#for i in doc._extra:
#    print i.mediatype , i.filename , i.content


# Walking in the presentation
#        level = 0
#        element = presentation
#        parent = None
#
#        while ( element!=None and level == 0 ) or level > 0 :
#            
#            if ( element != None ) :
#                print "%s+-> %s" % ("    " * level , element.tagName )
#
#                if ( element.tagName == "presentation:footer-decl" ) : self.has_footer = True
#                if ( element.tagName == "presentation:date-time-decl") : self.has_time = True
#                if ( element.tagName == "draw:page"):
#                    self.pages.append( ODP_Page( element.getAttribute("name") ) )
#                
#                parent = element.parentNode
#
#                if ( element.hasChildNodes() ) :
#                    level += 1
#                    element = element.firstChild
#                else :
#                    if ( element.nextSibling != None ) :
#                        element = element.nextSibling
#                    else :
#                        level -= 1
#                        element = parent.nextSibling
#            else :
#                level -= 1
#                parent = parent.parentNode
#                element = parent.nextSibling
