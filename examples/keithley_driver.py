from qililab.instruments import Keithley2600

settings = {"id_": 0, "category": "dc_source", "ip": "192.168.1.112", "firmware": None}
keithley = Keithley2600(settings=settings)

keithley.initial_setup()
