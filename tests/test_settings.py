"""Exercise saved slots against a layered NVDA configuration and live synths."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


class Section:

    def __init__(self, manager, path):
        self.manager = manager
        self.path = path
        self._cache = {}

    def _layers(self):
        layers = []
        for profile in self.manager.profiles:
            value = profile
            for key in self.path:
                value = value.get(key, {})
            layers.append(value)
        return layers

    def __getitem__(self, key):
        if key not in self._cache:
            for layer in reversed(self._layers()):
                if key in layer:
                    value = layer[key]
                    self._cache[key] = (
                        self.manager.section(self.path + (key,))
                        if isinstance(value, dict) else value
                    )
                    break
            else:
                raise KeyError(key)
        return self._cache[key]

    def __setitem__(self, key, value):
        section = self.manager.profiles[-1]
        for part in self.path:
            section = section.setdefault(part, {})
        section[key] = copy.deepcopy(value)
        self._cache.pop(key, None)
        for path, cached in self.manager.sections.items():
            if path[:len(self.path) + 1] == self.path + (key,):
                cached._cache.clear()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        keys = set()
        for layer in self._layers():
            keys.update(layer)
        return [(key, self[key]) for key in keys]

    def copy(self):
        return dict(self.items())


class Config:

    def __init__(self, base, profile=None):
        self.profiles = [base] + ([] if profile is None else [profile])
        self.sections = {}

    def section(self, path):
        if path not in self.sections:
            self.sections[path] = Section(self, path)
        return self.sections[path]

    def __getitem__(self, key):
        return self.section((key,))


class Synth:
    defaults = {
        "eloquence": {"voice": "Reed", "rate": 50, "pauseMode": "0", "sampleRate": "11025"},
        "espeak": {"voice": "en", "rate": 50},
    }

    def __init__(self, config, name):
        self.config = config
        self.name = name
        self.loadSettings()

    def loadSettings(self, onlyChanged=False):
        section = self.config["speech"][self.name]
        for key, default in self.defaults[self.name].items():
            setattr(self, key, section.get(key, default))

    def saveSettings(self):
        section = self.config["speech"][self.name]
        for key in self.defaults[self.name]:
            section[key] = getattr(self, key)


class SettingsTests(unittest.TestCase):

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.config = Config({"speech": {
            "eloquence": {"voice": "Reed", "rate": 50, "pauseMode": "2", "sampleRate": "22050"},
            "espeak": {"voice": "en", "rate": 50},
        }})
        self.current = Synth(self.config, "espeak")
        self.switches = []
        self.messages = []
        config = types.ModuleType("config")
        config.conf = self.config
        config.AggregatedSection = Section
        config.getUserDefaultConfigPath = lambda: self.temporary.name
        speech = types.ModuleType("speech")
        speech.getSynth = lambda: self.current
        speech.setSynth = self.setSynth
        handler = types.ModuleType("globalPluginHandler")
        handler.GlobalPlugin = object
        ui = types.ModuleType("ui")
        ui.message = self.messages.append
        addon = types.ModuleType("addonHandler")
        addon.initTranslation = lambda: None
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, {
            "config": config, "speech": speech, "globalPluginHandler": handler,
            "ui": ui, "addonHandler": addon,
        }).start()
        path = Path(__file__).resolve().parents[1] / "addon/globalPlugins/switchSynth.py"
        spec = importlib.util.spec_from_file_location("switchsynth_under_test", path)
        module = importlib.util.module_from_spec(spec)
        module._ = lambda text: text
        spec.loader.exec_module(module)
        self.plugin = module.GlobalPlugin()
        self.plugin.synths = {"version": 1,
            1: {"name": "eloquence", "config": {"voice": "Reed", "rate": 40}},
            2: {"name": "espeak", "config": {"voice": "en", "rate": 50}},
        }

    def setSynth(self, name):
        self.switches.append(name)
        self.current = Synth(self.config, name)
        return True

    def test_old_slot_preserves_settings_added_after_it_was_saved(self):
        saved = copy.deepcopy(self.plugin.synths[1])
        self.plugin.loadSynth(1)
        self.assertEqual(self.current.pauseMode, "2")
        self.assertEqual(self.current.sampleRate, "22050")
        self.assertEqual(self.current.rate, 40)
        self.assertEqual(self.plugin.synths[1], saved)

    def test_switch_away_and_back_preserves_live_unsaved_pause_mode(self):
        self.config["speech"]["eloquence"]["pauseMode"] = "0"
        self.current = Synth(self.config, "eloquence")
        self.current.pauseMode = "2"
        self.plugin.loadSynth(2)
        self.plugin.loadSynth(1)
        self.assertEqual(self.current.pauseMode, "2")

    def test_explicit_slot_value_still_overrides_current_setting(self):
        self.plugin.synths[1]["config"]["pauseMode"] = "0"
        self.plugin.loadSynth(1)
        self.assertEqual(self.current.pauseMode, "0")

    def test_reload_of_same_synth_preserves_new_settings(self):
        self.current = Synth(self.config, "eloquence")
        self.plugin.loadSynth(1)
        self.assertEqual(self.switches, [])
        self.assertEqual(self.current.pauseMode, "2")

    def test_saving_slot_captures_live_values_before_snapshot(self):
        self.current = Synth(self.config, "eloquence")
        self.current.pauseMode = "1"
        self.current.rate = 70
        self.plugin.script_saveSynth(None)
        self.assertEqual(self.plugin.synths[1]["config"]["pauseMode"], "1")
        self.assertEqual(self.plugin.synths[1]["config"]["rate"], 70)
        self.plugin.synths = {}
        self.plugin.load()
        self.assertEqual(self.plugin.synths[1]["config"]["pauseMode"], "1")

    def test_nested_new_settings_survive_without_changing_saved_slot(self):
        self.config["speech"]["eloquence"]["voiceSettings"] = {
            "voice1": {"rate": 50, "newSetting": "keep"},
        }
        self.plugin.synths[1]["config"]["voiceSettings"] = {"voice1": {"rate": 30}}
        self.plugin.loadSynth(1)
        nested = self.config["speech"]["eloquence"]["voiceSettings"]["voice1"]
        self.assertEqual(nested["newSetting"], "keep")
        self.assertEqual(nested["rate"], 30)
        self.assertEqual(self.plugin.synths[1]["config"]["voiceSettings"], {"voice1": {"rate": 30}})

    def test_profile_value_survives_without_replacing_base_value(self):
        self.config.profiles[0]["speech"]["eloquence"]["pauseMode"] = "1"
        self.config.profiles.append({"speech": {"eloquence": {"pauseMode": "2"}}})
        for section in self.config.sections.values():
            section._cache.clear()
        self.plugin.loadSynth(1)
        self.assertEqual(self.current.pauseMode, "2")
        self.assertEqual(self.config.profiles[0]["speech"]["eloquence"]["pauseMode"], "1")

    def test_saved_nested_config_is_detached_from_nvda_sections(self):
        self.current = Synth(self.config, "eloquence")
        self.config["speech"]["eloquence"]["voiceSettings"] = {"voice1": {"rate": 50}}
        self.plugin.script_saveSynth(None)
        saved = self.plugin.synths[1]["config"]["voiceSettings"]["voice1"]
        self.assertIsInstance(saved, dict)
        self.config["speech"]["eloquence"]["voiceSettings"]["voice1"]["rate"] = 90
        self.assertEqual(saved["rate"], 50)

    def test_empty_slot_keeps_current_synth(self):
        self.plugin.loadSynth(6)
        self.assertEqual(self.current.name, "espeak")
        self.assertEqual(self.switches, [])
        self.assertEqual(self.messages, ["6"])


if __name__ == "__main__":
    unittest.main()
