from typing import List, Optional
from file import Json
from loop import Loop, Pedal
from midi import Midi, Midi_preset
from footswitch import FootSwitch

class Patch:
    name: str
    footSwitch: FootSwitch
    midiPresets: List[Midi_preset] = []
    midi: Midi
    loops: List = [Loop]
    active: bool = False

    def __init__(self, patch_data, footSwitch: FootSwitch, active: bool = False, pedalList: List[Pedal] = []):
        self.name = patch_data.get("name", "")
        self.footSwitch = footSwitch
        self.active = active
        self.midi = Midi()
        self.midiPresets = []
        self.switchStatusList = list(map(bool, patch_data.get("footswitch", [])))
        self.loops = []  

        print(f'Init Patch {self.name}: ')

        for pedal in pedalList:
            if pedal.id in patch_data.get("loops", []):
                loop = Loop(pedal=pedal, order=pedal.id, active=True)
                self.loops.append(loop)
                print(f'  Loop {pedal.name} activated')
            else:
                loop = Loop(pedal=pedal, order=pedal.id, active=False)
                self.loops.append(loop)
                print(f'  Loop {pedal.name} deactivated')

        for midiPresetConfig in patch_data.get("midi", []):
            # Support both dict entries like {"channel":1, "program":2}
            # and list/tuple entries like [1, 2]
            channel = None
            program = None

            if isinstance(midiPresetConfig, dict):
                channel = midiPresetConfig.get("channel")
                program = midiPresetConfig.get("program")
            elif isinstance(midiPresetConfig, (list, tuple)) and len(midiPresetConfig) >= 2:
                channel, program = midiPresetConfig[0], midiPresetConfig[1]
            else:
                # Skip malformed entries
                print(f"Warning: skipping malformed midi preset: {midiPresetConfig}")
                continue

            # Fallbacks if values are missing
            if channel is None:
                channel = 1
            if program is None:
                program = 0

            midiPreset = Midi_preset(channel=int(channel), program=int(program))
            self.midiPresets.append(midiPreset)
            print(f'  Midi Preset channel {midiPreset.channel} program: {midiPreset.program}')


    def select(self):
    
        for status, switch in zip(self.switchStatusList, self.footSwitch.get_footswitch()):
            if status:
                switch.activate()
            else:
                switch.deactivate()

        for midiPreset in self.midiPresets:
            self.midi.send_pc(midiPreset.channel, midiPreset.program)

    def activate(self, file: Json, index: int):
        self.active = True
        file.save_to_file("active_patch_index", index)

    def deactivate(self):
        self.active = False

    def get_loops(self) -> List[Loop]:
        return self.loops

    def get_midi_list(self) -> List[dict]:
        return [{"channel": preset.channel, "program": preset.program} for preset in self.midiPresets]

    def get_midi_list_html(self) -> str:
        html = "<ul>"
        for midiPreset in self.midiPresets:
            html += f"<li>Channel: {midiPreset.channel}, Program: {midiPreset.program}</li>"
        html += "</ul>"
        return html

class Bank:

    name: str
    patches: List[Patch] = []
    active: bool = False
    
    def __init__(self, name: str, patches: List[Patch], active: bool = False):
        self.name = name
        self.patches = patches
        self.active = active

    def activate(self, file: Json, index: int):
        self.active = True
        file.save_to_file("active_bank_index", index)

    def deactivate(self):
        self.active = False

    def get_patch_by_index(self, index: int) -> Optional[Patch]:
        return self.patches[index]
    
    def get_active_patch(self) -> Optional[Patch]:
        return next((patch for patch in self.patches if patch.active), None)
    