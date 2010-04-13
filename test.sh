#!/bin/sh

template=./blender_templates/template_coverflow.blend
blender -b $template -P show_odp.py -- $@ 2>&1
