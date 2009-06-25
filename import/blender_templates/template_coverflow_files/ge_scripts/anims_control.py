from math import *

inch = 72.0
cm = inch / 2.54
mm = cm * 0.1
pica = 12.0

co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
control_obj = co.owner

obj = scene.objects

#get Sensors
sens = {}
sens['check_anims'] = co.sensors['check_anims']
sens['control_next']= co.sensors['control_next']
sens['control_prev']= co.sensors['control_prev']
sens['control_incr']= co.sensors['control_incr']
sens['control_grab']= co.sensors['control_grab']

#get Actuators
act = {}
act['send_message'] = co.actuators['send_message']

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

def send_to(object , subject , body , msg_actuator) :
    msg_actuator.propName = object
    msg_actuator.subject = subject
    msg_actuator.body = body
    co.activate(msg_actuator)

def update_slides_pos():
    bounds = 5
    first_slide = max( [ int(prop['real_slide']) - bounds , 0] )
    last_slide = min( [ int(prop['real_slide']) + bounds , prop['max_slides'] ] )

    all_slides = set(range(1,prop['max_slides']))
    visible_slides = set(range(first_slide , last_slide + 1) )
    invisible_slides = all_slides.difference(visible_slides)

    for i in invisible_slides:
        if ( i > 0 and i < prop['max_slides'] ):
            slide = obj['OBPage_%d' % i]
            if (slide.visible == True):
                slide.visible = False
                for c in slide.childrenRecursive:
                    c.visible = False

    for i in visible_slides:
        dx = i - prop['real_slide']
        diff = dx
#        if ( i == int(prop['selected_slide']) ):
#            coef = -sin(dx * pi)
#        else :
        
#        if i == 1 : set_prop('debug',dx)
#            coef = -( sin(dx * pi) + 1) / 2.0
#        dist = i - prop['selected_slide']
        if ( dx < 0 ):
            dx = max([ dx , -1.0 ])
        else :
            dx = min([ dx ,  1.0 ])
        
        rotation = (-sin(dx * pi/2)) * ( -sin(cos(dx * pi/2)) + 1 ) * 90

        if ( i > 0 and i < prop['max_slides'] ):
            slide = obj['OBPage_%d' % i]
            if ( slide.visible == False ):
                slide.visible = True
                for c in slide.childrenRecursive:
                    c.visible = True
            #slide.position = [ diff*4 + dx , -( 1 - fabs(diff) ) * 6 ,0 ]
            faceup_len = ( 1 - fabs(dx) ) * -1.8 * cm
#            if (dx < 1.0 and dx > -1.0):
            slide.position = [ (i * 0.1* cm ) + (1.75 * cm * dx) , faceup_len ,0 ]
#            else :
                
#                slide.position = [ (i*(0.5*cm)) + (1 * cm * dx) , faceup_len ,0 ]
                #slide.position = [ i + (1 * cm * (dx/fabs(dx))) , faceup_len ,0 ]
            
            #slide.position = [ diff*4 + dx , max( [min( [-2*cos(diff*pi/2)+1,0] ) , -1] ) * 6 ,0 ]
            
            slide.orientation = glRotatef( rotation ,0,0,1 )
            #slide.orientation = glRotatef(-90 ,0,0,1 )

def update_camera_pos():
    position = prop['current_slide']

    camera = obj['OBCamera']
    floor = obj['OBFloor']
    pos_camera = obj['OBCamera'].position
    pos_floor = obj['OBFloor'].position
    camera.position = [position * 0.1 * cm , pos_camera[1] , pos_camera[2]]
    floor.position = [position * 0.1 * cm, pos_floor[1] , pos_floor[2]]


def glRotatef(angle , x , y , z):
    c = cos(angle * pi / 180)
    s = sin(angle * pi / 180)

    matrix = []
    matrix.append([ x*x*(1-c) + c   , x*y*(1-c) - z*s , x*z*(1-c) + y*s ])
    matrix.append([ y*x*(1-c) + z*s , y*y*(1-c) + c   , y*z*(1-c) - x*s ])
    matrix.append([ x*z*(1-c) - y*s , y*z*(1-c) + x*s , z*z*(1-c) + c   ])

    return matrix


def increment_selected_slide(incr):
    new_selected_slide = prop['selected_slide'] + incr
    if ( new_selected_slide < 0):
        new_selected_slide = 0
    elif ( new_selected_slide > prop['max_slides'] ):
        new_selected_slide = prop['max_slides']

    set_prop('selected_slide',new_selected_slide)

#def update_current_slide() :


#def update_real_slide() :

if sens['control_next'].triggered and sens['control_next'].positive :

    incr = 1
    increment_selected_slide(incr)
        
if sens['control_prev'].triggered and sens['control_prev'].positive :

    incr = -1
    increment_selected_slide(incr)
    
if sens['control_grab'].triggered and sens['control_grab'].positive :
    set_prop('grab_mode',bool(int(sens['control_grab'].getBodies()[0]) ) )
    set_prop('grab_slide',prop['current_slide'])

if sens['check_anims'].triggered and sens['check_anims'].positive :

    update_slides_pos()
    update_camera_pos()
#    update_current_slide()
#    update_real_slide()   
 
    if ( prop['grab_mode'] == True ):
        if ( sens['control_incr'].isPositive() ) :
            
            incr = getattr( obj['OBControl'] , 'grab_val')
            current_slide = prop['grab_slide'] + incr
            if (current_slide < 0):
                current_slide = 0
            elif (current_slide > prop['max_slides'] ) :
                current_slide = prop['max_slides']

            set_prop('selected_slide',round(current_slide))
            set_prop('current_slide',current_slide)
    else :
        diff = prop['selected_slide'] - prop['current_slide']
        set_prop('debug' , diff)
        if ( diff != 0 ):
            incr = diff / 10.0
            set_prop('current_slide',prop['current_slide'] + incr)

    diff = prop['selected_slide'] - prop['real_slide']
    if (diff > 1) : 
        set_prop('real_slide',prop['selected_slide'] - 1)
        diff = prop['selected_slide'] - prop['real_slide']
    elif (diff < -1) :
        set_prop('real_slide',prop['selected_slide'] + 1)
        diff = prop['selected_slide'] - prop['real_slide']
        
    if ( diff != 0 ):
        incr = diff / 10.0
        set_prop('real_slide',prop['real_slide'] + incr)
