"""ExecutionBuilder class"""
from typing import Dict, List

from qililab.execution.execution import Execution
from qililab.execution.execution_buses.pulse_scheduled_bus import PulseScheduledBus
from qililab.execution.execution_buses.pulse_scheduled_readout_bus import (
    PulseScheduledReadoutBus,
)
from qililab.execution.execution_manager import ExecutionManager
from qililab.platform import Platform
from qililab.platform.components.bus import Bus
from qililab.platform.components.bus_types import (
    ContinuousBus,
    TimeDomainBus,
    TimeDomainReadoutBus,
)
from qililab.pulse import PulseSchedule
from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
from qililab.typings.execution import ExecutionOptions
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(
        self, platform: Platform, pulse_schedules: List[PulseSchedule], execution_options: ExecutionOptions
    ) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """

        return Execution(
            execution_manager=self._build_execution_manager(platform=platform, pulse_schedules=pulse_schedules),
            platform=platform,
            options=execution_options,
        )

    def _build_execution_manager(self, platform: Platform, pulse_schedules: List[PulseSchedule]):
        """Loop over pulses in PulseSequence, classify them by bus index and instantiate a Pulse Scheduled Bus class.

        Returns:
            ExecutionManager: ExecutionManager object.
        """
        control_pulse_schedule_buses: Dict[int, PulseScheduledBus] = {}
        readout_pulse_schedule_buses: Dict[int, PulseScheduledReadoutBus] = {}
        for pulse_schedule in pulse_schedules:
            for pulse_bus_schedule in pulse_schedule.elements:
                port, bus_idx, bus = self._get_bus_info_from_pulse_bus_schedule_port(platform, pulse_bus_schedule)
                if bus is None:
                    raise ValueError(f"There is no bus connected to port {port}.")

                if self._is_time_domain_readout_bus(bus):
                    self._add_readout_pulse_bus_schedule(
                        bus=bus,
                        bus_idx=bus_idx,
                        readout_pulse_schedule_buses=readout_pulse_schedule_buses,
                        pulse_bus_schedule=pulse_bus_schedule,
                    )
                    continue

                if self._is_time_domain_bus(bus):
                    self._add_control_pulse_bus_schedule(
                        bus=bus,
                        bus_idx=bus_idx,
                        control_pulse_schedule_buses=control_pulse_schedule_buses,
                        pulse_bus_schedule=pulse_bus_schedule,
                    )
                    continue

        continuous_buses = self._get_continuous_buses(platform=platform)

        return ExecutionManager(
            pulse_scheduled_buses=list(control_pulse_schedule_buses.values()),
            pulse_scheduled_readout_buses=list(readout_pulse_schedule_buses.values()),
            continuous_buses=continuous_buses,
            num_schedules=len(pulse_schedules),
        )

    def _is_time_domain_readout_bus(self, bus: Bus):
        """check if the given bus is a time domain readout one"""
        return isinstance(bus, TimeDomainReadoutBus)

    def _is_time_domain_bus(self, bus: Bus):
        """check if the given bus is a time domain one"""
        return isinstance(bus, TimeDomainBus)

    def _add_readout_pulse_bus_schedule(
        self,
        bus: TimeDomainReadoutBus,
        bus_idx: int,
        readout_pulse_schedule_buses: Dict[int, PulseScheduledReadoutBus],
        pulse_bus_schedule: PulseBusSchedule,
    ):
        """add a new pulse scheduled readout bus associated to the pulse bus schedule"""
        if bus_idx not in readout_pulse_schedule_buses:
            readout_pulse_schedule_buses[bus_idx] = PulseScheduledReadoutBus(
                bus=bus, pulse_schedule=[pulse_bus_schedule]
            )
            return
        readout_pulse_schedule_buses[bus_idx].add_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule)

    def _add_control_pulse_bus_schedule(
        self,
        bus: TimeDomainBus,
        bus_idx: int,
        control_pulse_schedule_buses: Dict[int, PulseScheduledBus],
        pulse_bus_schedule: PulseBusSchedule,
    ):
        """add a new pulse scheduled control bus associated to the pulse bus schedule"""
        if bus_idx not in control_pulse_schedule_buses:
            control_pulse_schedule_buses[bus_idx] = PulseScheduledBus(bus=bus, pulse_schedule=[pulse_bus_schedule])
            return
        control_pulse_schedule_buses[bus_idx].add_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule)

    def _get_bus_info_from_pulse_bus_schedule_port(self, platform: Platform, pulse_bus_schedule: PulseBusSchedule):
        """get the bus information that it is connected to the port in the pulse bus schedule"""
        port = pulse_bus_schedule.port
        bus_idx, bus = platform.get_bus(port=port)
        return port, bus_idx, bus

    def _get_continuous_buses(self, platform: Platform):
        """get the continuous buses from the platform"""
        return [bus for bus in platform.buses if isinstance(bus, ContinuousBus)]
