#!/bin/sh

template=./blender_templates/template_coverflow.blend
blender -b $template -P odp_blenderize.py -- $@ 2>&1
