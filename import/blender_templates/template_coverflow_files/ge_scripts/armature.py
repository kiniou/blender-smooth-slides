co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
control_obj = co.getOwner()

obj = scene.getObjectList()


#get Sensors
sens = {}
sens['play'] = co.getSensor('arm_play')
sens['stop'] = co.getSensor('arm_stop')
sens['check_anim'] = co.getSensor('check_anim')

#get Actuators
act = {}
act['anim_slide'] = co.getActuator('anim_slide')

#get Properties
prop = {}
prop['state']       = getattr( control_obj , 'state'      )
prop['prev_state']  = getattr( control_obj , 'prev_state' )
prop['frame']       = getattr( control_obj , 'frame'      )
prop['slide_obj']   = getattr( control_obj , 'slide_obj'  )

def update_attached_slide() :
    position = control_obj.getPosition()
    scaling = control_obj.scaling
    orientation = control_obj.orientation
    obj[ prop['slide_obj'] ].setPosition(position)
    obj[ prop['slide_obj'] ].orientation = orientation
    obj[ prop['slide_obj'] ].scaling = scaling
    


if sens['play'].isPositive():
    print "PLAY !!!!!!!"
    if (prop['state'] == False) :
        setattr(control_obj,'slide_obj',sens['play'].getBodies()[0])
        #setattr(control_obj,'prev_state',prop['state'])
        setattr(control_obj,'prev_state',False)
        setattr(control_obj,'state',True)
    else :
        setattr(control_obj,'state',False)

if sens['stop'].isPositive():
    print "STOP !!!!!!!"
    setattr(control_obj,'prev_state',prop['state'])
    setattr(control_obj,'state',False)

if sens['check_anim'].isPositive():
    if prop['prev_state'] != prop['state'] :
        if prop['state'] == True :
            setattr(control_obj,'frame', 1)
            GameLogic.addActiveActuator(act['anim_slide'],True)
            setattr(control_obj,'prev_state',prop['state'])

        elif prop['state'] == False :
            setattr(control_obj,'frame', 30)
            setattr(control_obj,'prev_state',prop['state'])
    else :
        if prop['state'] == True:
            if prop['frame'] < 30 :
                setattr(control_obj,'frame',prop['frame']+1)
                update_attached_slide()
            else:
                setattr(control_obj,'state',False)
        else :
            setattr(control_obj,'frame',1)
            GameLogic.addActiveActuator(act['anim_slide'], False)

