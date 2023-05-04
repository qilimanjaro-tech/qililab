# Unit Testing Guidelines

- Each unit test should have all data (fixtures) required in its own file. Eg. check `test_pulse.py`

  ```python
  @pytest.fixture(name="pulse")
  def fixture_pulse() -> Pulse:
      pulse_shape = Gaussian(num_sigmas=4)
      return Pulse(
          amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape
      )
  ```

- Each fixture should be parameterized to cover as many cases as possible

  ```python
  @pytest.fixture(
      name="pulse_shape",
      params=[
          Rectangular(),
          Gaussian(num_sigmas=4),
          Drag(num_sigmas=4, drag_coefficient=1.0),
      ],
  )
  def fixture_pulse_shape(request: pytest.FixtureRequest) -> PulseShape:
      """Return Rectangular object."""
      return request.param  # type: ignore


  @pytest.fixture(name="pulse")
  def fixture_pulse(pulse_shape: PulseShape) -> Pulse:
      return Pulse(
          amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape
      )
  ```

  Add ids: `ids=lambda x: f"Shape: {x.name}"`

  Also,

  ```python
  @pytest.fixture(
      name="amplitude", params=[0, 0.1, 0.5, 1], ids=lambda x: f"amplitude: {x}"
  )
  def fixture_amplitude(request: pytest.FixtureRequest) -> int:
      """Return amplitude"""
      return request.param
  ```

- Randomization helps catch unexpected cases

  ```python
  @pytest.fixture(name="random_pulse")
  def fixture_random_pulse(pulse_shape: PulseShape) -> Pulse:
      amplitude = random.randint(0, 1)
      phase = random.uniform(0, 180)
      duration = random.randint(0, 200)
      frequency = random.uniform(4e9, 10e9)
      return Pulse(
          amplitude=amplitude,
          phase=phase,
          duration=duration,
          frequency=frequency,
          pulse_shape=pulse_shape,
      )
  ```

- Asserts should validate method's logic, not only return's type

  ```python
  assert dictionary[PULSE.AMPLITUDE] == pulse.amplitude
  assert dictionary[PULSE.DURATION] == pulse.duration
  assert dictionary[PULSE.PHASE] == pulse.phase
  assert dictionary[PULSE.FREQUENCY] == pulse.frequency
  assert dictionary[PULSE.PULSE_SHAPE] == pulse.pulse_shape.to_dict()
  ```

- Don't trust codecov! Codecove just tells us if any given line is hit up in any kind of test. We have to make sure we write proper test for this line and call assert. (eg. `label()` method of `Pulse` is not tested. Also, `test_keithley_2600.py` has tests with no asserts)

- Unit tests shouldn't assume properties of fixture. If yes, these properties should be provided expilicitely.

  Examples:

  - `test_bus_execution.py` -> `test_acquire_results_raises_error` assumes the alias of the bus.

    Instead of

    ```python
    def test_acquire_results_raises_error(self, bus_execution: BusExecution):
        """Test that the ``acquire_results`` raises an error when no readout system control is present."""
        with pytest.raises(
            ValueError,
            match="The bus drive_line_bus needs a readout system control to acquire the results",
        ):
            bus_execution.acquire_result()
    ```

    we should do

    ```python
    def test_acquire_results_raises_error(self, bus_execution: BusExecution):
        """Test that the ``acquire_results`` raises an error when no readout system control is present."""
        with pytest.raises(
            ValueError,
            match=f"The bus {bus_execution.alias} needs a readout system control to acquire the results",
        ):
            bus_execution.acquire_result()
    ```

  - `test_qblox_pulsar_qcm.py` -> `test_turn_off_method` assumes that the QCM has only one sequencer.

    Instead of

    ```python
    def test_turn_off_method(self, qcm: QbloxQCM):
        """Test turn_off method"""
        qcm.turn_off()
        qcm.device.stop_sequencer.assert_called_once()
    ```

    we should do

    ```python
    def test_turn_off_method(self, qcm: QbloxQCM):
        """Test turn_off method"""
        qcm.turn_off()
        assert qcm.device.stop_sequencer.call_count == qcm.num_sequencers
    ```

- Unit tests shouldn't depend on classes that are above the tested class! (eg. Check how `ExecutionManager` fixture is provided in `test_execution_manager.py`)

- Unit tests should only test the functionality of the tested class! (eg. Check the asserts in `test_execution_manager.py` -> `test_upload`)

These last two kinds of test behaviour belong to integration testing!
