import Rasterizer

Rasterizer.showMouse(True)
co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
control_obj = co.getOwner()

obj = scene.getObjectList()


slide = {}
for o in obj:
    if o.name.count('Page_') > 0:
        slide[o.name] = o

orientation = None
position = None
scaling = None
for i in range(1,len(slide) + 1):
    if (i == 1):
        position = obj["OBNext_Slide"].getPosition()
        orientation = obj["OBNext_Slide"].orientation
        scaling = obj["OBNext_Slide"].scaling
    else:
        position_ns = obj["OBNext_Slide"].getPosition()
        position_nsi = obj["OBNext_Slide_Inc"].getPosition()
        position_ns[0] += position_nsi[0] * (i-1)
        position_ns[1] += position_nsi[1] * (i-1)
        position_ns[2] += position_nsi[2] * (i-1)
        position = position_ns
        orientation = obj["OBNext_Slide_Inc"].orientation
        scaling = obj["OBNext_Slide_Inc"].scaling

    slide["OBPage_%d" % (i)].setPosition(position)
    slide["OBPage_%d" % (i)].orientation = orientation
    slide["OBPage_%d" % (i)].scaling = scaling

setattr( control_obj,'max_slide',len(slide) )
