#!/bin/sh


template=./blender_templates/template_coverflow.blend
blender2.49 -b $template -P odp_importer.py -- $@ 
