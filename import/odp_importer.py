#!BPY

""" Registration info for Blender menus:
Name: 'OpenDocumentPresentation (.odp)'
Blender: 248
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
from Blender import Text3d, Mesh, Camera

import codecs
import sys
import os


from odf.opendocument import load,OpenDocumentPresentation
from odf import text,presentation,draw,style


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
        
        self.screen = { 'width' : 800, 'height' : 480 }

        self.font_list = {}
        self.load_fonts()
        self.blender = {}
        self.game = {}
        self.init_blender_file()

    def init_blender_file(self):
        self.blender['scene'] = Blender.Scene.GetCurrent()
        
        self.blender['render'] = self.blender['scene'].getRenderingContext()
        self.blender['render'].enableGameFrameExpose()

        self.blender['camera'] = Camera.New('persp', 'CamViewer')
        self.blender['camera'].setLens(3.06)
        self.blender['camera_object'] = self.blender['scene'].objects.new(self.blender['camera'])
        self.blender['camera_object'].setLocation(6.7, -2.22 , 1)
        self.blender['scene'].objects.camera = self.blender['camera_object']

        self.blender['text'] = Text3d.New("tmp_text") #Create the Text3d object
        self.blender['text'].setExtrudeDepth(0)    #Give some relief 
        self.blender['text'].setDefaultResolution(1)
        self.blender['text_object'] = self.blender['scene'].objects.new(self.blender['text'])
        self.blender['scene'].objects.unlink(self.blender['text_object'])
        
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

class ODP_Text():
    
    def __init__( self, x_text ) :

        self.attributes = x_text.attributes
        self.id = x_text.getAttribute('id')
        self.style_name = x_text.getAttribute( 'stylename' )
        self.text = x_text.firstChild
        self.cond_style_name = x_text.getAttribute( 'condstylename' )
        self.class_names = x_text.getAttribute( 'classnames' )
        self.level = 1
        parent = x_text.parentNode

        while (parent.tagName != 'draw:text-box') :
            if ( parent.parentNode.tagName == 'text:list-item') :
                self.level += 1
            parent = parent.parentNode

    def build( self , build_context) :
        build_context.doc['current_line'] += 1
        i_page = build_context.doc['current_page']
        i_frame = build_context.doc['current_frame']
        i_element = build_context.doc['current_element']
        i_element_type = build_context.doc['current_element_type']
        i_line = build_context.doc['current_line']

        i_name = "p%d.f%d.%s_%d.l_%d" % ( i_page , i_frame , i_element_type , i_element , i_line )
        i_text = self.text.data.encode('utf-8')

        
        i_position_y = -1 * ( i_line - 1 )
        i_position_x = 1 * ( self.level )
        i_position_z = -5 * ( i_page - 1 )

        b_text = build_context.blender['text']
        b_text_object = build_context.blender['text_object']
        b_scene = build_context.blender['scene']
        print ("%r" % (self.text.data), i_name, b_text.getSize())
        b_text.setText(i_text)   #Set the text for Text3d object
        b_text.setFont(build_context.font_list['Liberation Sans']['Bold']['blender'] ) #Set the font to Text3d object
        b_mesh = Mesh.New(i_name)
        
        b_mesh.getFromObject(b_text_object,0,0)
        
        b_object = b_scene.objects.new(b_mesh)
        b_object.setLocation( i_position_x , i_position_y , i_position_z )
        b_object.makeDisplayList()
        

    def __str__( self ) :
        str = ""

        str+="                   |TEXT\n"
        str+="                   | classnames    : %s\n" % (self.class_names)
        str+="                   | condstylename : %s\n" % (self.cond_style_name)
        str+="                   | stylename     : %s\n" % (self.style_name)
        str+="                   | id            : %s\n" % (self.id)
        str+="                   | text          : %s\n" % (unicode(self.text))
        #str+="                   | attributes    : %s\n" % (self.attributes)
        str+="                   | level         : %s\n" % (self.level)
        str+="                   =====\n"
        
        return str

class ODP_TextBox() :
    def __init__( self , x_textbox):
        self.texts = []

        self.addTextsFrom( x_textbox )

    def addTextsFrom( self, x_textbox ) :

        i_texts = x_textbox.getElementsByType(text.P)
        for i_text in i_texts:
            self.texts.append( ODP_Text(i_text) )

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

    def __init__( self, x_frame ) :
        self.style_name = x_frame.getAttribute( 'stylename') 
        self.class_name = x_frame.getAttribute( 'class' )
        self.width = x_frame.getAttribute( 'width' )
        self.height = x_frame.getAttribute( 'height' )
        self.x = x_frame.getAttribute( 'x' )
        self.y = x_frame.getAttribute( 'y' )
        self.zindex = x_frame.getAttribute( 'zindex' )
        self.frame_elements = []
        
        self.attributes = x_frame.attributes

        self.addElementsFrom(x_frame)

    def addElementsFrom( self , x_frame) :
        
        i_walk = True
        i_element = x_frame.firstChild
        while ( i_walk == True ) :
            
            if ( i_element.tagName == 'draw:text-box' ) :
                self.frame_elements.append( ODP_TextBox( i_element ) )

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
        #str+="         | attributes: %s\n" % (self.attributes)
        str+="         =====\n"

        for i in self.frame_elements :
            str += "%s" % (i)

        return str

class ODP_Page() :

    def __init__( self, x_page ) :
        
        self.name = ""
        self.frames = []
        self.number = 0

        self.name = x_page.getAttribute('name')
        
        self.addFramesFrom(x_page)

    def addFramesFrom( self , x_page) :

        i_walk = True
        i_element = x_page.firstChild
        while ( i_walk == True ) :
        #    print i_element.tagName
            if ( i_element.tagName == 'draw:frame' ) :
                self.frames.append( ODP_Frame(i_element) )
            if ( i_element.nextSibling != None ):
                i_element = i_element.nextSibling
            else :
                i_walk = False

    def build( self , build_context) :
        build_context.doc['current_line'] = 0         
        build_context.doc['current_frame'] = 0
        build_context.doc['current_page'] += 1
        for i_frame in self.frames :
            i_frame.build(build_context)

    def __str__( self ) :
        str = ""
        str += "    |PAGE %s\n" % (self.name)
        str += "    | number %s\n" % (self.number)
        str += "    =====\n"
        for frame in self.frames :
            str += "%s" % (frame)
        return str

class ODP_Presentation() :
    
    def __init__( self, x_presentation ) :
        self.footer = ""
        self.time = ""
        self.pages = []
        
        self.footer = x_presentation.getElementsByType( presentation.FooterDecl)[0].firstChild
        self.time = x_presentation.getElementsByType( presentation.DateTimeDecl)[0].getAttribute( 'source' )
        self.addPagesFrom(x_presentation)
        
    def addPagesFrom( self, x_presentation ) :
        
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
                self.pages.append( ODP_Page( i_element) )
                self.pages[-1].number = i_page_number

            if (i_element.nextSibling != None) :
                i_element = i_element.nextSibling
            else :
                i_walk = False
                
    def build( self , build_context) :
        
        for i_page in self.pages :
            i_page.build(build_context)
        print(build_context)



    def __str__(self):
        str = ""
        str += "|PRESENTATION\n"
        str += "| Footer is %s\n" % (self.footer)
        str += "| Time is %s\n" % (self.time)
        str += "=====\n"
        for p in self.pages:
            str += "%s\n" % p
        return str


if __name__ == '__main__':

    # TODO: Verify if script is installed in the plugins Blender directory

    odp_file = ''

    if Blender.mode == 'background' or Blender.mode == 'interactive':
#        print sys.argv
        real_argv_index = sys.argv.index('--') + 1
        real_argv=sys.argv[real_argv_index:]
        print real_argv

        from optparse import OptionParser
        usage = "usage: blender -b -P %prog -- [options] filename"
        prog = "odp_importer.py"
        parser = OptionParser(usage=usage,prog=prog)
        
        parser.add_option("-q", "--quiet",
                          action="store_false", dest="verbose", default=True,
                          help="don't print status messages to stdout")
        parser.add_option("-t", "--template",
                          action="store_false", dest="template", default=True,
                          help="don't print status messages to stdout")

        (options, args) = parser.parse_args(real_argv)
        print options , args

        if len(args) == 0:
            parser.error("You must provide at least a filename")
        if len(args) > 1:
            parser.error("You must provide JUST ONE filename")
        if Blender.sys.exists(args[0]) != 1:
            parser.error("File '%s' does not exist or is not a file" % (args[0]))
        
        odp_file = args[0]

    doc = load(odp_file)
    print ("DEBUG opendocument")
    print Blender.mode
        
    d = doc.presentation
    build_context = BuildContext()
    op = ODP_Presentation(d)
    #print (unicode(op))
    op.build(build_context)

    for i in doc.styles.getElementsByType(style.Style):
        print i.qname[1]
        print i.attributes
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
