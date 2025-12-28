from typing import List, Optional
from file import Json
from footswitch import FootSwitch, EffectSwitch
from loop import Pedal
from midi import Midi, Midi_preset
from patch import Bank, Patch

class BankManager:
    banks: List[Bank] = []
    statusFile: Json
    pedalList: List[Pedal] = []

    active_bank_name: str = ""
    active_patch_name: str = ""

    def __init__(self):
        self.banks = []
        self.file = Json()
        self.statusFile: Json = Json('active_status.json')

        active_bank_index = self.get_active_bank_index()
        active_patch_index = self.get_active_patch_index()

        self.footSwitch = FootSwitch()
        self.midi = Midi()

        for pedalData in self.file.data.get("pedalList", []):
            self.pedalList.append(Pedal(id=pedalData.get("id", 0), name=pedalData.get("name", "")))

        for bank_index, bank_data in enumerate(self.file.data.get("banks", [])):
            print(f"Index: {bank_index}, Bank Data: {bank_data}")

            patches = []
            for patch_index, patch_data in enumerate(bank_data.get("patches", [])):

                patch = Patch(
                    patch_data = patch_data,
                    footSwitch = self.footSwitch, 
                    active = (bank_index == active_bank_index and patch_index == active_patch_index),
                    pedalList = self.pedalList
                )

                if patch.active:
                    patch.select()
                    self.set_active_patch_name(patch)
                patches.append(patch)
                
            bank = Bank(
                name = bank_data.get("name", ""),
                patches = patches,
                active = (bank_index == active_bank_index)
            )
            if bank.active:
                self.set_active_bank_name(bank.name)
            self.banks.append(bank)

    def get_active_bank_index(self) -> int: 
        return self.statusFile.data.get("active_bank_index", 0)
        
    def get_active_patch_index(self) -> int:
        return self.statusFile.data.get("active_patch_index", 0)

    def get_active_bank(self) -> Optional[Bank]:
        return next((bank for bank in self.banks if bank.active), None)
    
    def get_banks_count(self) -> int:
        return len(self.banks)

    def move_up_bank(self) -> Optional[Bank]:
        current_index = next((i for i, bank in enumerate(self.banks) if bank.active), None)
        if current_index is None:
            return
        
        self.banks[current_index].deactivate()
        new_bank_index = current_index + 1
        if new_bank_index >= len(self.banks):
            new_bank_index = 0
        self.set_active_bank(self.banks[new_bank_index], new_bank_index)
        return self.banks[new_bank_index]

    def move_down_bank(self) -> Optional[Bank]:
        current_index = next((i for i, bank in enumerate(self.banks) if bank.active), None)
        if current_index is None:
            return
        
        self.banks[current_index].deactivate()
        new_bank_index = current_index - 1
        if new_bank_index < 0:
            new_bank_index = len(self.banks) - 1
        self.set_active_bank(self.banks[new_bank_index], new_bank_index)
        return self.banks[new_bank_index]

    def select_patch(self, patch_index: int) -> Optional[Patch]:
        current_bank = self.get_active_bank()
        if current_bank:
            current_patch = current_bank.get_active_patch()
            new_patch = current_bank.get_patch_by_index(patch_index)
    
            if new_patch:
                new_patch.select()
                if current_patch:
                    current_patch.deactivate()
            
                self.set_active_patch(new_patch, patch_index)
                return new_patch


    def set_active_bank(self, bank: Bank, new_bank_index: int):
        bank.activate(self.statusFile, new_bank_index)
        self.set_active_bank_name(bank.name)

    def set_active_bank_name(self, active_bank_name):
        self.active_bank_name = active_bank_name

    def get_active_bank_name(self) -> str:
        return self.active_bank_name or ""
    
    def set_active_patch(self, patch: Patch, new_patch_index: int):
        patch.activate(self.statusFile, new_patch_index)
        self.set_active_patch_name(patch)
    
    def set_active_patch_name(self, active_patch: Patch):
        self.active_patch_name = active_patch.name
    
    def get_active_patch_name(self) -> str:
        return self.active_patch_name or ""
    
    def get_active_patch(self) -> Optional[Patch]:
        current_bank = self.get_active_bank()
        if current_bank:
            return current_bank.get_active_patch()
        return None
    
    def get_patch_names(self) -> List[str]:
        """Get all patch names from the active bank."""
        current_bank = self.get_active_bank()
        if current_bank:
            return [patch.name for patch in current_bank.patches]
        return []
    
    
    def get_html_context(self, active_patch: Patch | None):

        if active_patch is None:
            return {}
        
        context = {
            "bank": self.get_active_bank_name(),
            "patch": self.get_active_patch_name(),
            "midi_data": active_patch.get_midi_list_html()
        }

        for i, loop in enumerate(active_patch.get_loops(), start=1):
            context[f"loop{i}_name"] = loop.pedal.name
            context[f"loop{i}_status"] = loop.get_css_class()

        for i, sw in enumerate(self.footSwitch.get_footswitch(), start=1):
            context[f"switch{i}_name"] = sw.name
            context[f"switch{i}_status"] = sw.get_css_class()
        

        print('Getting HTML context for patch:', context)
        return context
    
    