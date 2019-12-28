#Copyright 2013-2016 Tyler Spivey, released under the GPL
import pickle
import os
import config
import globalPluginHandler
import speech
import ui
import addonHandler
addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Switch Synth")

	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.synths = {}
		self.slot = 1
		self.load()

	def script_setSynth(self, gesture):
		self.slot = slot = int(gesture.displayName[-1])
		if slot in self.synths:
			config.conf.profiles[0]['speech'][self.synths[slot]['name']].clear()
			config.conf.profiles[0]['speech'][self.synths[slot]['name']].update(self.synths[slot]['config'])
			config.conf['speech'][self.synths[slot]['name']]._cache.clear()
			speech.setSynth(self.synths[slot]['name'])
		speech.getSynth().saveSettings()
		ui.message(str(slot))
	#Translators: Input help mode message for set synth command.
	script_setSynth.__doc__ = _("Sets the currently active synthesizer to the selected slot.")

	def script_saveSynth(self, gesture):
		if self.slot not in self.synths:
			self.synths[self.slot] = {}
		self.synths[self.slot]['name'] = speech.getSynth().name
		self.synths[self.slot]['config'] = dict(config.conf['speech'][speech.getSynth().name].items())
		self.write()
		ui.message(_("saved"))
	#Translators: Input help mode message for save synth command.
	script_saveSynth.__doc__ = _("Save the currently used synthesizer and its settings to the currently selected slot")

	def write(self):
		path = os.path.join(config.getUserDefaultConfigPath(), "switch_synth.pickle")
		with open(path, 'wb') as f:
			pickle.dump(self.synths, f)

	def load(self):
		path = os.path.join(config.getUserDefaultConfigPath(), "switch_synth.pickle")
		if not os.path.exists(path): return
		with open(path, 'rb') as f:
			self.synths = pickle.load(f)
		if 'version' not in self.synths:
			self.synths = {'version': 0}

	__gestures = {
	"kb:control+shift+NVDA+1": "setSynth",
	"kb:control+shift+NVDA+2": "setSynth",
	"kb:control+shift+NVDA+3": "setSynth",
	"kb:control+shift+NVDA+4": "setSynth",
	"kb:control+shift+NVDA+5": "setSynth",
	"kb:control+shift+NVDA+6": "setSynth",
	"kb:control+shift+NVDA+v":"saveSynth",
}
