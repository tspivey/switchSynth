# -*- coding: UTF-8 -*-

# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

# Full getext (please don't change)
_ = lambda x : x

# Add-on information variables
addon_info = {
	# for previously unpublished addons, please follow the community guidelines at:
	# https://bitbucket.org/nvdaaddonteam/todo/src/56140dbec531e4d7591338e1dbc6192f3dd422a8/guideLines.txt
	# add-on Name, internal for nvda
	"addon_name" : "switchSynth",
	# Add-on summary, usually the user visible name of the addon.
	# TRANSLATORS: Summary for this add-on to be shown on installation and add-on information.
	"addon_summary" : _("Switch synth"),
	# Add-on description
	# Translators: Long description to be shown for this add-on on add-on information from add-ons manager
	"addon_description" : _("""Allows easy switching between synthesizers.
To switch synthesizers, press control+shift+NVDA+1 through control+shift+NVDA+6.
To save the current voice in the currently selected slot, press control+shift+NVDA+v."""
	),
	# version
	"addon_version" : "1.02-dev",
	# Author(s)
	"addon_author" : "Tyler Spivey <tspivey@pcdesk.net>",
	# URL for the add-on documentation support
	"addon_url" : None,
	# Documentation file name
	"addon_docFileName" : "readme.html",
}


import os.path

# Define the python files that are the sources of your add-on.
# You can use glob expressions here, they will be expanded.
pythonSources = ["addon/globalPlugins/switchSynth.py"]

# Files that contain strings for translation. Usually your python sources
i18nSources = pythonSources + ["buildVars.py", "docHandler.py"]

# Files that will be ignored when building the nvda-addon file
# Paths are relative to the addon directory, not to the root directory of your addon sources.
excludedFiles = []
