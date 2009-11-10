"""
    Smooth Slides for Blender

    Copyright © 2009 Kevin Roy
    This file is part of "Smooth Slides for Blender"

    Smooth Slides for Blender is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

co = GameLogic.getCurrentController()

#get Scene
scene = GameLogic.getCurrentScene()

#get Objects
control_obj = co.owner

obj = scene.objects

#get Sensors
sens = {}
sens['right']       = co.sensors['right']
sens['left']        = co.sensors['left']
sens['grab']        = co.sensors['grab']
sens['mouse_grab']  = co.sensors['mouse_grab']

#get Actuators
act = {}
act['send_message_0'] = co.actuators['send_message_0']
#act['send_message_1'] = co.actuators['send_message_1']

#get Properties
prop = {}
prop['hit_object'] = control_obj['hit_object']
prop['key_status'] = control_obj['key_status']
prop['slide']      = control_obj['slide']
prop['max_slide']  = control_obj['max_slide']
prop['grab_mode']  = control_obj['grab_mode']
prop['win_width']  = control_obj['win_width']
prop['grab_val']  = control_obj['grab_val']
prop['mouse_ini']  = control_obj['mouse_ini']
prop['mouse_accel']  = control_obj['mouse_accel']


def set_prop(prop_name , prop_value) :
    control_obj[prop_name] = prop_value
    prop[prop_name] = control_obj[prop_name]

def send_to(object , subject , body , msg_actuator) :
    msg_actuator.propName = object
    msg_actuator.subject = subject
    msg_actuator.body = body
    co.activate(msg_actuator)


def goto_next_slide() :
    send_to( 'OBAnimations' , 'control_next' , control_obj.name , act['send_message_0'] )

def goto_prev_slide() :
    send_to( 'OBAnimations' , 'control_prev' , control_obj.name , act['send_message_0'] )

def increment_grab() :
    send_to( 'OBAnimations' , 'control_incr' , '' , act['send_message_0'] )

def set_grab_mode(mode) :
    set_prop('grab_mode' , mode)
    send_to('OBAnimations' , 'control_grab' , "%d" % mode , act['send_message_0'] )

key_str = ''

if prop['grab_mode'] == False:

    set_prop('grab_val',0)

    if sens['right'].triggered:
        if sens['right'].positive:
            key_str = '[right]'
            set_prop('key_status' , key_str)
            goto_next_slide()

    if sens['left'].triggered:
        if sens['left'].positive :
            key_str = '[left]'
            set_prop('key_status' , key_str)
            goto_prev_slide()
else :
    frame_inc = 0
    key_str = prop['key_status']
    if sens['mouse_grab'].positive:
        key_str = '[mouse]'
        set_prop('grab_val',3.0 * float(prop['mouse_ini'] - sens['mouse_grab'].getXPosition()) / float(prop['win_width']) )
    else :
        if sens['right'].positive :
            key_str = '[right]'
            set_prop('grab_val',prop['grab_val'] + 0.1 )
        if sens['left'].positive :
            key_str = '[left]'
            set_prop('grab_val',prop['grab_val'] - 0.1 )

    set_prop('key_status' , key_str)
    increment_grab()


if (sens['grab'].triggered or sens['mouse_grab'].triggered) :
    if (sens['grab'].positive or sens['mouse_grab'].positive) :
        set_grab_mode(True)
    else:
        set_grab_mode(False)

if sens['mouse_grab'].positive and sens['mouse_grab'].triggered:
    set_prop('mouse_ini',sens['mouse_grab'].getXPosition())

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
    
    
