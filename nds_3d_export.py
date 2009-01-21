#!BPY

""" Registration info for Blender menus:
Name: 'Nintendo DS GL CallList'
Blender: 246
Group: 'Export'
Tip: 'Export for Nintendo DS DevkitPro'
"""
__author__ = "Kevin (KiNiOu) ROY"
__url__ = ("blender", "kiniou", "Author's site, http://blog.knokorpo.fr")
__version__ = "0.2"

__bpydoc__ = """\
This script export models in Nintendo DS CallList for
the DevKitPro SDK in a .h file.

Usage:

Go to Export and type a name for the file.

v0.1:<br>
    UV-textured meshes + Normals + Colors.
    Export into "C-style" format.
    Export Texture into PCX Format with correct size.

v0.2:<br>
    Export into "Binary" format.

TODO :<br>
    - 3D Animation support
    - Export directly into binary format
"""

from Blender.BGL import *
import Blender
from Blender import Texture,Image,Material,Object, Draw, BGL, Window , sys
import random
from random import random
import math
from math import *



# Define libnds binary functions and macros

def floattov16(n) :
	return ( (n) * (1 << 12) )

def floattov10(n) :
	if (n>.998) :
		return 0x1FF 
	else :
		return (((n)*(1<<9)))

def floattot16(n) :
	return (((n) * (1 << 4)))

def VERTEX_PACK(x,y) :
	return ( ((x) & 0xFFFF) | ((y) << 16) )

def NORMAL_PACK(x,y,z) :
	return (((x) & 0x3FF) | (((y) & 0x3FF) << 10) | ((z) << 20))
	
def RGB15(r,g,b) :
	return ((r)|((g)<<5)|((b)<<10))

def TEXTURE_PACK(u,v) :
	return ((u & 0xFFFF) | ((v) << 16))


# a _mesh_option represents export options in the gui
class _mesh_options (object) :
	__slots__ = 'format' , 'uv_export' ,'texfile_export' , 'normals_export' , 'color_export' , 'mesh_data' , 'mesh_name', 'texture_data' , 'texture_list' , 'texture_w' , 'texture_h', 'dir_path'

	def __init__(self,mesh_data,dir_path) :
		self.format = 1 			#Which format for the export? 0->Binary, 1->C-Style
		self.uv_export = 1 			#Do we export uv coordinates? 0->No, 1->Yes
		self.normals_export = 1     #Do we export normals coordinates ? 0->No, 1->Yes
		self.color_export = 1		#Do we export color attributes ? 0->No, 1->Yes
		self.mesh_data = mesh_data  #The Blender Mesh data
		self.mesh_name = mesh_data.name #The Blender Mesh name
		self.list_textures() #Retrieve all texture bound to the Blender mesh
		self.texture_w = 128
		self.texture_h = 128
		self.dir_path = dir_path
		self.texfile_export = 0

	def list_textures(self) :
		print "listing textures for mesh \"%s\"" % self.mesh_name
		materials = self.mesh_data.materials
		self.texture_data = []
		#Here we take the first material in the mesh
		tex = []		
		if len(materials)>0 : 
			tex = materials[0].getTextures()

		self.texture_list = []
		#Here we take the first Texture of Image Type
		img_found = 0
		if len(tex)>0 :
			for t in tex : 
				if t != None :
					if (t.tex.getType() == 'Image' and t.tex.getImage() != None) : 
						image = t.tex.getImage()
						self.texture_list.append(t)
						img_found = 1
						print "%s %dx%d" % (image.getName(),image.getSize()[0],image.getSize()[1])
		
		if (img_found == 1):
			self.texture_data.append(self.texture_list[0].tex.getImage())
		else :
			print "!!!Warning : Cannot find any textures bound to the mesh!!!"
			print "!!!          TEXTURE_PACKs won't be exported           !!!"

	def get_final_path_mesh(self):
		return ( Blender.sys.join(self.dir_path,self.mesh_name + (".h" if (self.format) else ".bin")) )

	def get_final_path_tex(self):
		return ( Blender.sys.join(self.dir_path,self.mesh_name + ".pcx") )

	def __str__(self):
		return "File Format:%s , Exporting Texture:%s , Exporting Normals:%s , Exporting Colors:%s" % (self.format,self.uv_export,self.normals_export,self.color_export)



class _nds_cmdpack_vertex (object) :
	__slots__ = 'x','y','z'
	
	def __init__(self,vertex=(0.0,0.0,0.0)):
		self.x, self.y, self.z = vertex

	def get_cmd_str(self):
		return "FIFO_VERTEX16"

	def get_val_str(self):
		return "VERTEX_PACK(floattov16(%f),floattov16(%f)) ,\nVERTEX_PACK(floattov16(%f),0)" % (self.x,self.y,self.z)
		
	def get_nb_val(self):
		return 2

	def __str__(self):
		return "(%f,%f,%f)" % (self.x,self.y,self.z)


class _nds_cmdpack_normal (object):
	__slots__ = 'x','y','z'

	def __init__(self,normal=(0.0,0.0,0.0)):
		self.x, self.y, self.z = normal

	def get_cmd_str(self):
		return "FIFO_NORMAL"

	def get_val_str(self):
		return "NORMAL_PACK(floattov10(%3.6f),floattov10(%3.6f),floattov10(%3.6f))" % (self.x,self.y,self.z)
	
	def get_nb_val(self):
		return 1

	def __str__(self):
		return "(%f,%f,%f)" % (self.x,self.y,self.z)


class _nds_cmdpack_color (object):
	__slots__ = 'r','g','b'

	def __init__(self,color=(0,0,0)):
		self.r,self.g,self.b = color
	
	def get_cmd_str(self):
		return "FIFO_COLOR"

	def get_val_str(self):
		return "RGB15(%d,%d,%d)" % (self.r,self.g,self.b)

	def get_nb_val(self):
		return 1

	def __str__(self):
		return "(%d,%d,%d)" % (self.r,self.g,self.b)


class _nds_cmdpack_texture (object):
	__slots__ = 'u','v'
	
	def __init__(self,uv=(0.0,0.0)):
		self.u,self.v = uv

	def get_cmd_str(self):
		return "FIFO_TEX_COORD"

	def get_val_str(self):
		return "TEXTURE_PACK(floattot16(%3.6f),floattot16(%3.6f))" % (self.u,self.v)

	def get_nb_val(self):
		return 1
		
	def __str__(self):
		return "(%f,%f)" % (self.u,self.v)


class _nds_mesh_vertex (object):
	__slots__ = 'vertex','uv','normal','color'

	def __init__(self):
		self.vertex = None
		self.uv = None
		self.normal = None
		self.color = None

	def __str__(self):
		return " vertex=%s uv=%s normal=%s color=%s " % (self.vertex , self.uv , self.normal , self.color)


class _nds_mesh (object) :
	__slots__ = 'name', 'quads' , 'triangles' , 'texture' , 'cmdpack_type' , 'cmdpack_value' , 'cmdpack_count' , 'uv_export' , 'color_export' , 'options', 'final_cmdpack'
	
	
	def __init__(self,mesh_options):
		print mesh_options
		self.options = mesh_options
		self.quads = []
		self.triangles = []
		self.cmdpack_type = []
		self.cmdpack_value = []
		self.cmdpack_count = 0
		if (self.options.uv_export and self.options.mesh_data.faceUV ): self.uv_export = True
		else: self.uv_export = False
		if (self.options.color_export and self.options.mesh_data.vertexColors ) : self.color_export = True
		else: self.color_export = False
		
		self.name = mesh_options.mesh_name
		self.get_quads(mesh_options.mesh_data)
		self.get_triangles(mesh_options.mesh_data)
		#self.get_texture(mesh_options.mesh_data)
		#self.rescale_mesh(mesh_options.mesh_data)
		if self.uv_export : self.rescale_texture()
		if self.color_export : self.rescale_color()
		self.prepare_cmdpack()
		self.construct_cmdpack()
		self.save()
		if (self.options.texfile_export) : self.save_tex()
		

	def save_tex(self) :
		try:
			import PIL.Image
		except ImportError :
			print "Python Imaging Library not installed"
		else :
			print self.options.texture_data[0].filename
			print Blender.sys.expandpath(self.options.texture_data[0].filename)
			if (self.options.texture_data[0].packed ) : self.options.texture_data[0].unpack(Blender.UnpackModes.USE_LOCAL)
			img = PIL.Image.open(Blender.sys.expandpath(self.options.texture_data[0].getFilename()))
			img_rgb = img.convert("RGB")
			img_pal = img_rgb.convert("P",palette=PIL.Image.ADAPTIVE)
			img_res = img_pal.resize((self.options.texture_w,self.options.texture_h) )
			img_res.save(self.options.get_final_path_tex())

		
	def add_nds_mesh_vertex(self,face,face_list):
		for i, v in enumerate(face.v):
			nds_mesh_vertex = _nds_mesh_vertex()
			#we copy vertex's coordinates information
			nds_mesh_vertex.vertex = _nds_cmdpack_vertex(v.co)
			#we copy vertex's normals information
			nds_mesh_vertex.normal = _nds_cmdpack_normal(v.no)
			#we copy vertex's UV coordinates information only if there is UV layer for the current mesh
			if (self.uv_export) : 
				#print face.uv[i]
				nds_mesh_vertex.uv = _nds_cmdpack_texture( (face.uv[i].x,1-face.uv[i].y))
			#we copy vertex's color only if there is Color Layer for the current mesh
			if (self.color_export) : 
				nds_mesh_vertex.color = _nds_cmdpack_color( (face.col[i].r,face.col[i].g,face.col[i].b) )
			#finally, we append the nds_mesh_vertex in the quads list
			face_list.append(nds_mesh_vertex)
		
	def get_quads(self,blender_mesh):
		for face in blender_mesh.faces :
			#we process the face only if this is a quad
			if (len(face) == 4) :
				self.add_nds_mesh_vertex(face,self.quads)

	def get_triangles(self,blender_mesh):
		for face in blender_mesh.faces :
			#we process the face only if this is a triangle
			if (len(face) == 3) :
				self.add_nds_mesh_vertex(face,self.triangles)
	
	def rescale_mesh(self,blender_mesh):
		max_x=max_y=max_z=min_x=min_y=min_z=max_l=0
		for v in blender_mesh.verts:
			if v.co[0]>max_x : max_x = v.co[0]
			elif v.co[0]<min_x : min_x = v.co[0]
			if v.co[1]>max_y : max_y = v.co[1]
			elif v.co[1]<min_y : min_y = v.co[1]
			if v.co[2]>max_z : max_z = v.co[2]
			elif v.co[2]<min_z : min_z = v.co[2]
		if (abs(max_x-min_x) > max_l) : max_l = abs(max_x-min_x)
		if (abs(max_y-min_y) > max_l) : max_l = abs(max_y-min_y)
		if (abs(max_z-min_z) > max_l) : max_l = abs(max_z-min_z)
		
		if (len(self.quads)>0):
			for f in self.quads:
				v=f.vertex
				f.vertex.x = v.x/max_l
				f.vertex.y = v.y/max_l
				f.vertex.z = v.z/max_l
		if (len(self.triangles)>0):
			for f in self.triangles:
				v=f.vertex
				f.vertex.x = v.x/max_l
				f.vertex.y = v.y/max_l
				f.vertex.z = v.z/max_l
			
			
	def rescale_texture(self):
		if (len(self.quads)>0):
			for f in self.quads:
				uv=f.uv
				f.uv.u = uv.u * self.options.texture_w
				f.uv.v = uv.v * self.options.texture_h
		if (len(self.triangles)>0):				
			for f in self.triangles:
				uv=f.uv
				f.uv.u = uv.u * self.options.texture_w
				f.uv.v = uv.v * self.options.texture_h
			
	def rescale_color(self):
		if (len(self.quads)>0):
			for f in self.quads:
				c=f.color
				f.color.r = c.r * 32 / 256
				f.color.g = c.g * 32 / 256
				f.color.b = c.b * 32 / 256
		if (len(self.triangles)>0):				
			for f in self.triangles:
				c=f.color
				f.color.r = c.r * 32 / 256
				f.color.g = c.g * 32 / 256
				f.color.b = c.b * 32 / 256
		
		
#	def get_texture(self,blender_mesh):
#		self.texture = ("",0,0)

#		materials = blender_mesh.materials
#		
#		#Here we take the first material in the mesh
#		tex = []
#		if len(materials)>0 :
#			tex = materials[0].getTextures()

#		#Here we take the first Texture of Image Type
#		img_found = 0
#		if len(tex)>0 :
#			for t in tex :
#				if t != None :
#					if (t.tex.getType() == 'Image') :
#						image = t.tex.getImage()
#						img_found = 1
#						break
#		
#		if (img_found == 1):
#			self.texture = (image.getName(),image.getSize()[0],image.getSize()[1])
#		else :
#			print "!!!Warning : Cannot find any textures bound to the mesh!!!"
#			print "!!!          TEXTURE_PACKs won't be exported           !!!"



	def prepare_cmdpack(self):
		value_cnt = 0
		type_cnt = 0
		cmd_cnt = 0
		color_backup = ""
		if (len(self.quads) > 0):
			self.cmdpack_type.append("FIFO_BEGIN")		
			self.cmdpack_value.append("GL_QUADS")
			cmd_cnt += 1
			value_cnt += 1
		
			for i in range(len(self.quads)):
				v = self.quads[i]

				#if (self.color_export and v.color != None and color_backup==v.color.get_val_str()) :
				if (self.color_export and v.color != None ) :
					self.cmdpack_type.append(v.color.get_cmd_str())
					self.cmdpack_value.append(v.color.get_val_str())
					value_cnt += 1
					cmd_cnt += 1
					#color_backup = v.color.get_val_str()
							
				if (self.uv_export and v.uv != None) :
					self.cmdpack_type.append(v.uv.get_cmd_str())
					self.cmdpack_value.append(v.uv.get_val_str())
					value_cnt += 1
					cmd_cnt += 1

				if (v.normal != None):
					self.cmdpack_type.append(v.normal.get_cmd_str())
					self.cmdpack_value.append(v.normal.get_val_str())
					value_cnt += 1
					cmd_cnt += 1

				if (v.vertex != None) :
					self.cmdpack_type.append(v.vertex.get_cmd_str())
					self.cmdpack_value.append(v.vertex.get_val_str())
					value_cnt += 2
					cmd_cnt += 1

			self.cmdpack_type.append("FIFO_END")		
			self.cmdpack_value.append("")
			cmd_cnt += 1

		if (len(self.triangles) > 0):
			self.cmdpack_type.append("FIFO_BEGIN")		
			self.cmdpack_value.append("GL_TRIANGLE")
			cmd_cnt += 1
			value_cnt += 1
		
			for i in range(len(self.triangles)):
				v = self.triangles[i]

				#if (self.color_export and v.color != None and color_backup!=v.color.get_val_str()) :
				if (self.color_export and v.color != None ) :
					self.cmdpack_type.append(v.color.get_cmd_str())
					self.cmdpack_value.append(v.color.get_val_str())
					value_cnt += 1
					cmd_cnt += 1
					#color_backup = v.color.get_val_str()
				
			
				if (self.uv_export and v.uv != None) :
					self.cmdpack_type.append(v.uv.get_cmd_str())
					self.cmdpack_value.append(v.uv.get_val_str())
					value_cnt += 1
					cmd_cnt += 1

				if (v.normal != None):
					self.cmdpack_type.append(v.normal.get_cmd_str())
					self.cmdpack_value.append(v.normal.get_val_str())
					value_cnt += 1
					cmd_cnt += 1

				if (v.vertex != None) :
					self.cmdpack_type.append(v.vertex.get_cmd_str())
					self.cmdpack_value.append(v.vertex.get_val_str())
					value_cnt += 2
					cmd_cnt += 1

			self.cmdpack_type.append("FIFO_END")		
			# Note : there is no value associated with a FIFO_END command but we put empty to be symetric with the cmdpack_type list
			# This value will be filtered out when writing the file
			self.cmdpack_value.append("") 
			cmd_cnt += 1

		nb_nop = (int)(ceil(cmd_cnt/4.0)*4 - cmd_cnt)
		
		if (nb_nop > 0):
			for i in range(nb_nop):
				self.cmdpack_type.append("FIFO_NOP")		
				# Note : FIFO_NOP command are dummy command to fill the FIFO_COMMAND_PACK and as no value like FIFO_END command
				self.cmdpack_value.append("")
				cmd_cnt += 1
				
		self.cmdpack_count = value_cnt + (int)(ceil(cmd_cnt/4.0))
		


	def construct_cmdpack(self):
		print "construct the fifo command pack"
		self.final_cmdpack = []
		fifo_cmdpack = ""
		idx_stamp = 0
		for i in range(len(self.cmdpack_type)):
			if (i%4==0) : 
				self.final_cmdpack.append("")
				idx_stamp = len(self.final_cmdpack) - 1
				fifo_cmdpack += self.cmdpack_type[i]
			else : 
				fifo_cmdpack += " , " + self.cmdpack_type[i]
			
			if (self.cmdpack_value[i] != "") : self.final_cmdpack.append(self.cmdpack_value[i])
			
			if (i%4==3) :
				self.final_cmdpack[idx_stamp] = "FIFO_COMMAND_PACK( " + fifo_cmdpack + ")"
				fifo_cmdpack = ""
				
		#for i in final_cmdpack :
		#	print i
		

	def save(self) :
		f = open(self.options.get_final_path_mesh(),"w")
		f.write("u32 %s[] = {\n%d,\n" % (self.options.mesh_name,self.cmdpack_count))
		i=0
		for l in self.final_cmdpack:
			if (i != (len(self.final_cmdpack)-1)) : f.write(l + ",\n")
			else : f.write(l + "\n")
			i+=1
		f.write("};\n")
		f.close();

	def __str__(self):
		return "NDS Mesh [%s], Faces = %d (Quads=%d, Triangles=%d), Texture=%s" % (self.name,len(self.quads)/4+len(self.triangles)/3,len(self.quads)/4,len(self.triangles)/3,repr((self.options.get_final_path_tex(), self.options.texture_w,self.options.texture_h)) )
	

class _menu_nds_export (object) :
	__slots__ = 'nb_meshes', 'mesh_options','selected_menu_mesh','popup_elm','button' , 'texID'
	
	def __init__(self,dir_path):
		self.nds_list_meshes(dir_path)
		
	def nds_list_meshes(self,dir_path) :
		print "Get current selected Meshes" 

		scene = Blender.Scene.GetCurrent()

		objects = Blender.Object.GetSelected()
	
		self.nb_meshes = 0
		self.mesh_options = []
		for cur_obj in objects :
			if (cur_obj.getType()=="Mesh") :
				self.mesh_options.append( _mesh_options( cur_obj.getData(name_only=False,mesh=True) , dir_path) )
				self.nb_meshes += 1
		
		button = []
		
		
	def _menu_meshes_select(self,event, val) :
		print "%s , %s" % (event,val)

	def _menu_gui(self) :
		
		glEnable(GL_TEXTURE_2D)
		gluOrtho2D(0, 0, -500, -500)  
		glClearColor(1,1,1,1)
		glClear(GL_COLOR_BUFFER_BIT)
		glColor3f(0,0,0)
		glRasterPos2d(5, 200 + 15 )
		Draw.Text( "Mesh to export : %s" % (self.mesh_options[0].mesh_name) )
		glRasterPos2d(5, 200 + 15 -15)
		Draw.Text( "Save Format : %s" % ("C-Style Format" if (self.mesh_options[0].format) else "NDS Binary CallList" ) )
		glRasterPos2d(5, 200 + 15 -30)
		#Draw.Text( "Save Mesh into file : %s" % (Blender.sys.join(self.mesh_options[0].dir_path,self.mesh_options[0].mesh_name + (".h" if (self.mesh_options[0].format) else ".bin")) ) )
		Draw.Text( "Save Mesh into file : %s" % self.mesh_options[0].get_final_path_mesh())
		glRasterPos2d(5, 200 + 15 -45)
		if (self.mesh_options[0].texfile_export == 1) :
			#Draw.Text( "Save Texture into file : %s" % (Blender.sys.join(self.mesh_options[0].dir_path,self.mesh_options[0].mesh_name + ".pcx") ) )
			Draw.Text( "Save Texture into file : %s" % self.mesh_options[0].get_final_path_tex())
		else :
			Draw.Text( "No Texture export" )
		
		Draw.PushButton("GO!! Export!!" , 99 , 5 , 200 + 15 - 75 ,128, 20)
		
		Draw.Toggle( "C-Style File"   , 1 , 5 , 5 + 0  + 2 , 128 , 20 , self.mesh_options[0].format)
		Draw.Toggle( "Texture"        , 2 , 5 , 5 + 20 + 4 , 128 , 20 , self.mesh_options[0].uv_export )
		Draw.Toggle( "Normals"        , 3 , 5 , 5 + 40 + 6 , 128 , 20 , self.mesh_options[0].normals_export)
		Draw.Toggle( "Colors "        , 4 , 5 , 5 + 60 + 8 , 128 , 20 , self.mesh_options[0].color_export) 

		
		glBegin(GL_LINE_LOOP)
		glColor3f(0.0,0.0,0.0)
		glVertex2i( 5 + 128 + 5 , 5 + 128 + 0   )
		glVertex2i( 5 + 128 + 5 + 0 , 5 + 128 - ( 5 + 128 ) / 2   )
		glVertex2i( 5 + 128 + 5 + 0 , 5 + 128 - ( 5 + 128 )   )
		
		glEnd()

		glBegin(GL_LINES)
		glVertex2i( 0                         , 5 + 128 + 5  )
		glVertex2i( 5 + 128 + 5 + 5 + 256 + 5 , 5 + 128 + 5   )
		glEnd()
		
		self.texID = 0
		if (self.mesh_options[0].mesh_data.faceUV) :
			if (self.mesh_options[0].uv_export == 1 ) :
				if (len(self.mesh_options[0].texture_data) > 0) :
					img = self.mesh_options[0].texture_data[0]
					self.texID = img.glLoad()
				
					Draw.Toggle( "128" , 10 , 20 + 256, 5 +  0 +  2 , 32 , 20 , 1 if self.mesh_options[0].texture_w==128 else 0)
					Draw.Toggle( "64" , 11 , 20 + 256, 5 + 20 +  4 , 32 , 20 , 1 if self.mesh_options[0].texture_w==64  else 0)
					Draw.Toggle( "32" , 12 , 20 + 256, 5 + 40 +  6 , 32 , 20 , 1 if self.mesh_options[0].texture_w==32  else 0)
					Draw.Toggle( "16" , 13 , 20 + 256, 5 + 60 +  8 , 32 , 20 , 1 if self.mesh_options[0].texture_w==16  else 0)
					Draw.Toggle( "8" , 14 , 20 + 256, 5 + 80 + 10 , 32 , 20 , 1 if self.mesh_options[0].texture_w==8   else 0)
				
					Draw.Toggle( "128" , 20 , 60 + 256, 5 +  0 +  2 , 32 , 20 , 1 if self.mesh_options[0].texture_h==128 else 0)
					Draw.Toggle( "64" , 21 , 60 + 256, 5 + 20 +  4 , 32 , 20 , 1 if self.mesh_options[0].texture_h==64  else 0)
					Draw.Toggle( "32" , 22 , 60 + 256, 5 + 40 +  6 , 32 , 20 , 1 if self.mesh_options[0].texture_h==32  else 0)
					Draw.Toggle( "16" , 23 , 60 + 256, 5 + 60 +  8 , 32 , 20 , 1 if self.mesh_options[0].texture_h==16  else 0)
					Draw.Toggle( "8" , 24 , 60 + 256, 5 + 80 + 10 , 32 , 20 , 1 if self.mesh_options[0].texture_h==8   else 0)
				
					glColor3f(1.0,1.0,1.0)
					glBindTexture(GL_TEXTURE_2D,self.texID)
					glBegin(GL_QUADS)
					glTexCoord2f(0,0)
					glVertex2i( 5 + 128 + 5 + 5 + 0   , 5 + 128 + 0   )
					glTexCoord2f(1,0)
					glVertex2i( 5 + 128 + 5 + 5 + self.mesh_options[0].texture_w , 5 + 128 + 0   )
					glTexCoord2f(1,-1)
					glVertex2i( 5 + 128 + 5 + 5 + self.mesh_options[0].texture_w , 5 + 128 - self.mesh_options[0].texture_h )
					glTexCoord2f(0,-1)
					glVertex2i( 5 + 128 + 5 + 5 + 0   , 5 + 128 - self.mesh_options[0].texture_h )
					glEnd()
					self.mesh_options[0].texfile_export = 1
				else :
					glRasterPos2d(5 + 128 + 5 + 5 , 5 + 64 )
					Draw.Text("No Texture linked to this mesh")
					glRasterPos2d(5 + 128 + 5 + 5 , 5 + 64 - 15 )
					Draw.Text("Go to materials menu and load at least one image" )
					self.mesh_options[0].texfile_export = 0

			else :
				glRasterPos2d(5 + 128 + 5 + 5 , 5 + 64 )
				Draw.Text("Click on the [Texture] button")
				glRasterPos2d(5 + 128 + 5 + 5 , 5 + 64 - 15 )
				Draw.Text("to display Texture export" )
				self.mesh_options[0].texfile_export = 0


	def _menu_event(self,evt,val) :
		if (evt == Draw.ESCKEY) :
			Draw.Exit()                 # exit when user presses ESC
			return
		Draw.Redraw(1)

	def _menu_event_button(self,evt) :
		if   evt==1 : self.mesh_options[0].format = 1 - self.mesh_options[0].format
		elif evt==2 : self.mesh_options[0].uv_export = 1 - self.mesh_options[0].uv_export
		elif evt==3 : self.mesh_options[0].normals_export = 1 - self.mesh_options[0].normals_export
		elif evt==4 : self.mesh_options[0].color_export = 1 - self.mesh_options[0].color_export
		elif evt==10 : self.mesh_options[0].texture_w = 128
		elif evt==11 : self.mesh_options[0].texture_w = 64
		elif evt==12 : self.mesh_options[0].texture_w = 32
		elif evt==13 : self.mesh_options[0].texture_w = 16
		elif evt==14 : self.mesh_options[0].texture_w = 8
		elif evt==20 : self.mesh_options[0].texture_h = 128
		elif evt==21 : self.mesh_options[0].texture_h = 64
		elif evt==22 : self.mesh_options[0].texture_h = 32
		elif evt==23 : self.mesh_options[0].texture_h = 16
		elif evt==24 : self.mesh_options[0].texture_h = 8
		elif evt==99 : 
			nds_export = _nds_mesh(self.mesh_options[0])
			print nds_export
			Draw.Exit()                 # exit when user presses ESC
			return
		Draw.Redraw(1)

def DSexport(dir_path):
	print "---------------"
	print " NDS  EXPORTER"
	print "---------------"

	screens = Window.GetScreens()
	for s in screens : print s
	menu = _menu_nds_export(dir_path)
	
	
	print "Mesh count = %d" % (menu.nb_meshes)

	if ( menu.nb_meshes == 0) :
		print "Problem : No mesh selected"
		return

	Draw.Register(menu._menu_gui, menu._menu_event, menu._menu_event_button)

#	f = open(filename,"w")

#	for cur_mesh in lst_mesh :
#		nds_export = _nds_mesh(cur_mesh)
#		cmd_pack = nds_export.construct_cmdpack()
#		print nds_export
#
#		f.write("u32 %s[] = {\n%d,\n" % (nds_export.name,nds_export.cmdpack_count))
#		i=0
#		for l in cmd_pack:
#			if (i != (len(cmd_pack)-1)) : f.write(l + ",\n")
#			else : f.write(l + "\n")
#			i+=1
#		f.write("};\n")
#	f.close();


def my_callback(filename):
#	if filename.find('/', -2) <= 0: filename += '.h' # add '.h' if the user didn't
	#print Blender.sys.dirname(filename)
	DSexport(Blender.sys.dirname(filename))


fname = Blender.sys.makename(ext = "")
Blender.Window.FileSelector(my_callback, "Select a directory","")
