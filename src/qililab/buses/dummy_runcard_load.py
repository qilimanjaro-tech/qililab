from qililab.typings.yaml_type import yaml
import importlib
from qililab.buses.interfaces.bus import BusInterface
from qililab.buses.instruments.drive_bus import DriveBus
from qcodes import Instrument

def find_instrument(runcard: dict, key: str, value: str) -> dict:
    instruments = runcard['instruments']
    for instrument in instruments.keys():
        if key in instrument and value in instrument[key]:
            return instrument
        elif 'submodules' in instrument:
            for submodule in instrument['submodules']:
                if key in submodule and value in submodule[key]:
                    return instrument
    return {}

with open("galadriel_test_abs_path.yml", "r") as stream:
    try:
        runcard = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

buses_module_name = "qililab.buses.instruments.drive_bus"
instruments_module_name = "qililab.drivers.instruments."

buses:list[BusInterface] = []

# for instrument in runcard['instruments']:
#     abs_path = instruments_module_name+instrument['type']
#     module_name, class_name = abs_path.rsplit(".", 1)
#     name = instrument['alias']
#     address = instrument['address']
#     InstrumentClass = getattr(importlib.import_module(module_name), class_name)
#     instrumen_instance = InstrumentClass(name, address)
#     instruments.append(instrumen_instance)

for bus in runcard['buses']:
    class_name = bus['type']
    if 'drive' in class_name.lower():
        print()
        MyClass = getattr(importlib.import_module(module_name), class_name)
        instance = MyClass()
        print(type(instance))
# module_name, class_name = "qililab.buses.instruments.drive_bus.DriveBus".rsplit(".", 1)
# print(module_name)
# print(class_name)
# MyClass = getattr(importlib.import_module(module_name), class_name)
# instance = MyClass()

# print(type(instance))
