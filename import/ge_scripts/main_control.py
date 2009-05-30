def send_to(object , message , msg_actuator):
    msg_actuator.setToPropName(object.getName())
    msg_actuator.setSubject(message)
    GameLogic.addActiveActuator(msg_actuator,True)

co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
control_obj = co.getOwner()

obj_list = scene.getObjectList()
obj_armature = obj_list['OBBounce']

#get Sensors
mouse_sensor = co.getSensor('mouse')

#get Actuators
send_message_act = co.getActuator('send_message')

#get Properties
hit_object_prop = getattr(control_obj,'hit_object')


if hit_object_prop == '' and mouse_sensor.isPositive() and mouse_sensor.isTriggered():
    #object_focus = mouse_sensor.getHitObject()
    object_focus = obj_list['OBPage_1']
    if object_focus.getName() not in ['OBBounce']:
        setattr(control_obj,'hit_object',object_focus.getName())
    
        #object_focus.setParent(obj_armature)
        send_to(obj_armature,'play',send_message_act)
elif hit_object_prop != '' and not mouse_sensor.isPositive() and mouse_sensor.isTriggered():
    send_to(obj_armature,'stop',send_message_act)
    setattr(control_obj,'hit_object','')
    
    
