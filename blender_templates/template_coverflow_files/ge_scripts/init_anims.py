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
        len_pagenum = len("%s" % prop['max_slides'])
        if ( i > 0 and i < prop['max_slides'] ):
            i_name = ("OBPage_%0"+str(len_pagenum)+"d") % ( i )
            slide = obj[i_name]
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
