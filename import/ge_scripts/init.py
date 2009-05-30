import Rasterizer

Rasterizer.showMouse(True)
co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
control_obj = co.getOwner()

obj_list = scene.getObjectList()
obj_armature = obj_list['OBBounce']
obj_armature.setVisible(False)

