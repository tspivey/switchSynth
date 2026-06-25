#Copyright 2013-2026 Tyler Spivey, released under the GPL
try:
	import cPickle
except ModuleNotFoundError:
	import _pickle as cPickle
import os
import copy
import config
import globalPluginHandler
import speech
try:
	from speech import getSynth, setSynth
except ImportError:
	from synthDriverHandler import getSynth, setSynth

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

	def script_setSynth1(self, gesture):
		self.loadSynth(1)
	script_setSynth1.__doc__ = _("Sets the currently active synthesizer to slot 1.")

	def script_setSynth2(self, gesture):
		self.loadSynth(2)
	script_setSynth2.__doc__ = _("Sets the currently active synthesizer to slot 2.")

	def script_setSynth3(self, gesture):
		self.loadSynth(3)
	script_setSynth3.__doc__ = _("Sets the currently active synthesizer to slot 3.")

	def script_setSynth4(self, gesture):
		self.loadSynth(4)
		script_setSynth4.__doc__ = _("Sets the currently active synthesizer to slot 4.")

	def script_setSynth5(self, gesture):
		self.loadSynth(5)
	script_setSynth5.__doc__ = _("Sets the currently active synthesizer to slot 5.")

	def script_setSynth6(self, gesture):
		self.loadSynth(6)
	script_setSynth6.__doc__ = _("Sets the currently active synthesizer to slot 6.")

	def loadSynth(self, slot):
		self.slot = slot
		if slot in self.synths:
			config.conf.profiles[0]['speech'][self.synths[slot]['name']].clear()
			config.conf.profiles[0]['speech'][self.synths[slot]['name']].update(self.synths[slot]['config'])
			config.conf['speech'][self.synths[slot]['name']] = copy.deepcopy(self.synths[slot]['config'])

			config.conf['speech'][self.synths[slot]['name']]._cache.clear()
			if getSynth().name != self.synths[slot]['name']:
				setSynth(self.synths[slot]['name'])
			else:
				getSynth().loadSettings(onlyChanged=True)
		getSynth().saveSettings()
		ui.message(str(slot))

	def script_saveSynth(self, gesture):
		if self.slot not in self.synths:
			self.synths[self.slot] = {}
		self.synths[self.slot]['name'] = getSynth().name
		if hasattr(config.conf['speech'][getSynth().name], 'items'):
			items = config.conf['speech'][getSynth().name].items()
		else:
			items = config.conf['speech'][getSynth().name].iteritems()
		items = dict(items)
		for k, v in items.items():
			if isinstance(v, config.AggregatedSection):
				items[k] = v.copy()
		self.synths[self.slot]['config'] = items
		self.write()
		ui.message(_("saved"))
	#Translators: Input help mode message for save synth command.
	script_saveSynth.__doc__ = _("Save the currently used synthesizer and its settings to the currently selected slot")

	def write(self):
		path = os.path.join(config.getUserDefaultConfigPath(), "switch_synth.pickle")
		with open(path, 'wb') as f:
			cPickle.dump(self.synths, f, 0)

	def load(self):
		path = os.path.join(config.getUserDefaultConfigPath(), "switch_synth.pickle")
		if not os.path.exists(path): return
		with open(path, 'rb') as f:
			self.synths = cPickle.load(f)
		if 'version' not in self.synths:
			self.synths = {'version': 1}

	__gestures = {
	"kb:control+shift+NVDA+1": "setSynth1",
	"kb:control+shift+NVDA+2": "setSynth2",
	"kb:control+shift+NVDA+3": "setSynth3",
	"kb:control+shift+NVDA+4": "setSynth4",
	"kb:control+shift+NVDA+5": "setSynth5",
	"kb:control+shift+NVDA+6": "setSynth6",
	"kb:control+shift+NVDA+v":"saveSynth",
}
