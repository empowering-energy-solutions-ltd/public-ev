from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
import numpy.typing as npt
import pandas as pd

from ev_model.data import enums
from ev_model.models import sim_parameters


class VehiclesProtocol(Protocol):

  def charging_profile(
      self, timesteps: npt.NDArray[np.datetime64],
      charger_max_energy_outputs: npt.NDArray[np.float64]
  ) -> npt.NDArray[np.float64]:
    ...

  def get_recorded_data(self) -> dict[str, npt.NDArray[np.float64]]:
    ...


class ChargerRecorder(Protocol):

  def record_batch_data(self, index: npt.NDArray[np.datetime64],
                        values: npt.NDArray[np.float64],
                        col_name: str) -> None:
    ...

  @property
  def recorded_data(self) -> pd.DataFrame:
    ...


@dataclass
class Charger:
  """Class to represent a charger.

  Attributes:
    name str:
      The name of the charger.
    charger_type enums.ChargerType:
      The type of the charger.
    max_output float:
      The maximum output of the charger.
    ev_list list[VehiclesProtocol]:
      A list with the EVs connected to the charger.
    no_connections int:
      The maximum number of EVs that can be connected to this charger.
    data_recorder ChargerRecorder:
      The data recorder for the charger.
    specific_capital_cost float:
      The specific capital cost of the charger.
    specific_maintenance_cost float:
      The specific maintenance cost of the charger.
    size_system float:
      The size of the system.
    lifetime int:
      The lifetime of the charger.
  
  Methods:
    charging_profile: 
      Returns the charging profile for the charger.
    get_recorded_data_from_evs:
      Returns the recorded data from all EVs.
    get_recorded_data:
      Returns the recorded data from the charger.
  """
  name: str
  charger_type: enums.ChargerType
  max_output: float
  ev_list: list[VehiclesProtocol]
  no_connections: int  #max number of EVs that can be connected to this charger
  data_recorder: ChargerRecorder
  specific_capital_cost: float = 12000  #GBP/charger
  specific_maintenance_cost: float = 0.01 * specific_capital_cost  #GBP/kW/year
  size_system: float = 10  #kW
  lifetime: int = 30  # years

  def __post_init__(self):
    ...

  @property
  def number_of_evs(self) -> int:
    return len(self.ev_list)

  def charging_profile(
      self,
      timesteps: npt.NDArray[Any],
      schedule_charging: npt.NDArray[np.float64] | None = None
  ) -> npt.NDArray[np.float64]:
    """Returns the charging profile for the charger.

    Arguments:
      timesteps npt.NDArray[Any]:
          The timesteps to be used.
      schedule_charging npt.NDArray[np.float64] | None:
          The schedule of charging for the charger.

    Returns:
          The total charger output.
    """
    total_charger_output = np.zeros(len(timesteps))
    if schedule_charging is None:
      schedule_charging = np.zeros(
          len(timesteps)) + self.max_output / self.number_of_evs
    schedule_energy_output = schedule_charging * sim_parameters.POWER_TO_ENERGY_FACTOR
    for ev in self.ev_list:
      dispatched_energy = ev.charging_profile(timesteps,
                                              schedule_energy_output)
      total_charger_output += dispatched_energy / sim_parameters.POWER_TO_ENERGY_FACTOR
    self.data_recorder.record_batch_data(
        timesteps,
        total_charger_output * sim_parameters.POWER_TO_ENERGY_FACTOR,
        enums.ChargerData.ENERGY_INPUT.name)
    return total_charger_output

  def get_recorded_data_from_evs(self) -> pd.DataFrame:
    """Return the recorded data from all EVs.
    
    Returns:
          The recorded data from all EVs."""
    frames = []
    for ev in self.ev_list:
      frames.append(pd.concat(
          ev.get_recorded_data(),
          axis=1))  # old code {ev.name: ev.data_recorder.recorded_data}
    return pd.concat(frames, axis=1)

  def get_recorded_data(self) -> dict[str, npt.NDArray[np.float64]]:
    """ Retrieve the recorded data from the charger. 
    
    Returns:
          The recorded data from the charger."""
    return {self.name: self.data_recorder.recorded_data}
