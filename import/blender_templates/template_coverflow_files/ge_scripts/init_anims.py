from math import *

co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
control_obj = co.owner

obj = scene.objects


#get Actuators
act = {}
act['ge_state'] = co.actuators['ge_state']

#get Properties
prop = {}
prop['current_slide']  = control_obj['current_slide']
prop['max_slides'] = control_obj['max_slides']
prop['selected_slide'] = control_obj['selected_slide']
prop['real_slide'] = control_obj['real_slide']
prop['grab_mode'] = control_obj['grab_mode']
prop['grab_slide'] = control_obj['grab_slide']

def set_prop(prop_name , prop_value) :
    control_obj[prop_name] = prop_value
    prop[prop_name] = control_obj[prop_name]

def init_slides_pos():
    bounds = 5
    first_slide = max( [ int(prop['current_slide']) - bounds , 0] )
    last_slide = min( [ int(prop['current_slide']) + bounds, prop['max_slides'] ] )
    for i in range(first_slide , last_slide + 1):
        dx = i - prop['current_slide']
        diff = dx
        if (diff < 0):
            diff = max( [ diff , -1.0 ] )
        else :
            diff = min( [ diff , 1.0 ] )

        if ( i > 0 and i < prop['max_slides'] ):
            slide = obj['OBPage_%d' % i]
            slide.position = [ diff + dx/2 , 0 , (1 - fabs(diff) )*1.5  ]
            slide.orientation = glRotatef(-sin(diff * pi / 180.0 ) * 70,0,0,1)

def glRotatef(angle , x , y , z):
    c = cos(angle * pi / 180.0)
    s = sin(angle * pi / 180.0)

    matrix = []
    matrix.append([ x*x*(1-c) + c   , x*y*(1-c) - z*s , x*z*(1-c) + y*s ])
    matrix.append([ y*x*(1-c) + z*s , y*y*(1-c) + c   , y*z*(1-c) - x*s ])
    matrix.append([ x*z*(1-c) - y*s , y*z*(1-c) + x*s , z*z*(1-c) + c   ])

    return matrix

obj_slides = obj['OBSlides'].children
max_slides = len( obj_slides )


set_prop('max_slides' , max_slides + 1)
set_prop('current_slide' , 0 )

init_slides_pos()

co.activate(act['ge_state'])
