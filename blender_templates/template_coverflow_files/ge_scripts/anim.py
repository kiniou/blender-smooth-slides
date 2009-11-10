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
control_obj = co.getOwner()

obj = scene.getObjectList()


#get Sensors
sens = {}
sens['anim_next']   = co.sensors['anim_next']
sens['anim_prev']   = co.sensors['anim_prev']
sens['check_anim']  = co.sensors['check_anim']

#get Actuators
act = {}
act['anim']         = co.actuators['anim']

#get Properties
prop = {}
prop['state']       =  control_obj['state']
prop['frame']       =  control_obj['frame']
prop['direction']   =  control_obj['direction']

def set_prop(prop_name , prop_value) :
    control_obj[prop_name] = prop_value
    prop[prop_name] = control_obj[prop_name]






if sens['anim_next'].isPositive():
    #print "PLAY FORWARD %s" % (control_obj.name)
    set_prop('frame' , 1)
    set_prop('state' , 1)
    set_prop('direction' , 1)

if sens['anim_prev'].isPositive():
    #print "PLAY BACKWARD %s" % (control_obj.name)
    set_prop('frame' , 30)
    set_prop('state' , 1)
    set_prop('direction' , -1)

if sens['check_anim'].isPositive():

    parent = control_obj.getParent()
    if getattr(parent, 'state') == 1:
        set_prop('frame' , getattr(parent,'cur_frame') % 30 + 1)
#    if   prop['state'] == 0 :
#        set_prop('frame',1)
#
#    elif prop['state'] == 1 :
#        if prop['direction'] > 0 and  prop['frame'] < 30 :
#            set_prop('frame',prop['frame']+1)
#        elif prop['direction'] < 0 and  prop['frame'] > 1 :
#            set_prop('frame',prop['frame']-1)
#        else:
#            set_prop('state',0)
    
    GameLogic.addActiveActuator(act['anim'],True)
