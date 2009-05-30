co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
control_obj = co.getOwner()

obj_list = scene.getObjectList()


#get Sensors
play_sensor = co.getSensor('arm_play')
stop_sensor = co.getSensor('arm_stop')
check_anim_sensor = co.getSensor('check_anim')

#get Actuators
action_act = co.getActuator('bounce_anim')

#get Properties
state = getattr(control_obj,'state')
prev_state = getattr(control_obj,'prev_state')
frame = getattr(control_obj,'frame')

if play_sensor.isPositive():
    print "PLAY !!!!!!!"
    setattr(control_obj,'prev_state',state)
    setattr(control_obj,'state',True)

if stop_sensor.isPositive():
    print "STOP !!!!!!!"
    setattr(control_obj,'prev_state',state)
    setattr(control_obj,'state',False)

if check_anim_sensor.isPositive():
    if prev_state != state :
        if state == True :
            action_act.set("LoopEnd",1,30,0)
            GameLogic.addActiveActuator(action_act,True)
            setattr(control_obj,'prev_state',state)
            
        elif state == False :
            action_act.set("FromProp",1,1,0)
            setattr(control_obj,'frame', 1)
            action_act.setProperty('frame')
            GameLogic.addActiveActuator(action_act, True)
            setattr(control_obj,'prev_state',state)

