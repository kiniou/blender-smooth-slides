def send_to(object , subject , body , msg_actuator):
    msg_actuator.setToPropName(object.getName())
    msg_actuator.setSubject(subject)
    msg_actuator.setBody(body)
    GameLogic.addActiveActuator(msg_actuator,True)


def goto_next_slide( slide_num , act , obj):
    slide_name = "OBPage_%d" % ( slide_num )
    slide_obj = obj[slide_name]
    next_slide_obj = obj["OBNext_Slide"]
    #obj[current_slide].setParent(obj[anim_center_slide])
    #setattr(next_slide_obj,'slide_obj',slide_name)
    
    send_to(next_slide_obj , 'stop' , '', act['send_message_0'])
    send_to(next_slide_obj , 'play' , slide_name, act['send_message_1'])


co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
#control_obj = co.getOwner()

obj = scene.getObjectList()
#obj_armature = obj_list['OBBounce']

#get Sensors
sens = {}
sens['next_slide'] = co.getSensor('next_slide')
sens['prev_slide'] = co.getSensor('prev_slide')

#get Actuators
act = {}
act['send_message_0'] = co.getActuator('send_message_0')
act['send_message_1'] = co.getActuator('send_message_1')

#get Properties
prop = {}
prop['hit_object'] = getattr(obj['OBControl'],'hit_object')
prop['key_status'] = getattr(obj['OBControl'], 'key_status')
prop['slide'] = getattr(obj['OBControl'], 'slide')
prop['max_slide'] = getattr(obj['OBControl'], 'max_slide')

key_str = ''

if sens['next_slide'].isTriggered():
    key_str = '[next_slide]'
    if sens['next_slide'].isPositive() :
        setattr(obj['OBControl'],'key_status',prop['key_status'] + key_str)
        if prop['slide'] < prop['max_slide'] :
            setattr(obj['OBControl'],'slide',prop['slide'] + 1)
            goto_next_slide(prop['slide'] + 1 ,act,obj)
    else :
        setattr(obj['OBControl'],'key_status',prop['key_status'].replace(key_str,''))

if sens['prev_slide'].isTriggered():
    key_str = '[prev_slide]'
    if sens['prev_slide'].isPositive() :
        setattr(obj['OBControl'],'key_status',prop['key_status'] + key_str)
    else :
        setattr(obj['OBControl'],'key_status',prop['key_status'].replace(key_str,''))

#if hit_object_prop == '' and next_slide_sensor.isPositive() and next_slide_sensor.isTriggered():
#    #object_focus = mouse_sensor.getHitObject()
#    object_focus = obj_list['OBPage_1']
#    if object_focus.getName() not in ['OBBounce']:
#        setattr(control_obj,'hit_object',object_focus.getName())
#    
#        #object_focus.setParent(obj_armature)
#        send_to(obj_armature,'play',send_message_act)
#elif hit_object_prop != '' and not next_slide_sensor.isPositive() and next_slide_sensor.isTriggered():
#    send_to(obj_armature,'stop',send_message_act)
#    setattr(control_obj,'hit_object','')
    
    
