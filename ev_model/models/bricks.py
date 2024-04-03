from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd


@dataclass
class TimeserieRecorder:
  """Class used to record timeseries data.

  Attributes:
    index npt.NDArray[np.datetime64]:
      A numpy array with the datetime index.
    header list[Enum]:
      A list with the column names.
    recorded_data pd.DataFrame:
      A dataframe with the recorded data.

  Methods:
    get_column_names:
      Returns the column names.
    get_index_name:
      Returns the index name.
    record_single_data:
      Records a single data point.
    record_batch_data:
      Records a batch of data."""
  index: npt.NDArray[np.datetime64]
  header: list[Enum]
  recorded_data: pd.DataFrame = field(init=False)

  def __post_init__(self):
    self.recorded_data = pd.DataFrame(index=self.index,
                                      columns=self.get_column_names())
    self.recorded_data.index.name = self.get_index_name()
    for c in self.recorded_data.columns:
      self.recorded_data[c] = 0

  def get_column_names(self) -> list[str]:
    """Returns the column names.
    
    Returns:
          A list with the column names."""
    return [c.name for c in self.header[1:]]

  def get_index_name(self) -> str:
    """Returns the index name.

    Returns:
          The index name."""
    return self.header[0].name

  def record_single_data(self, new_index: datetime, new_data: float):
    """append new data"""

  def record_batch_data(self, index: npt.NDArray[np.datetime64],
                        values: npt.NDArray[np.float64],
                        col_name: str) -> None:
    """Records a batch of data.
    
    Arguments:
      index npt.NDArray[np.datetime64]:
          A numpy array with the datetime index.  
      values npt.NDArray[np.float64]:
          A numpy array with the values to be recorded.  
      col_name str:
          The name of the column to be recorded. 
          """
    self.recorded_data.loc[index, col_name] = values.astype('int64')


@dataclass
class Schedule:
  """Class used to define the schedule of people with EVs, when are they working, 
  connecting their EVs, etc.
  WIP: to be developed

  Attributes:
    arrival_time datetime.time:
      The time when the person arrives at work.
    departure_time datetime.time:
      The time when the person leaves work.
    list_days list[int] | None:
      The list of days when the EV is connected.

  Methods:
    is_plugged:
      Returns if the EV is connected.
    get_plugged_profile:
      Returns the profile of the EV being connected.
  """
  arrival_time: time = time(8, 0)
  departure_time: time = time(17, 0)
  list_days: list[int] | None = None  #list of days when the EV is connected

  def __post_init__(self):
    if self.list_days is None:
      self.list_days = list(range(5))  # Monday to Friday

  def is_plugged(self, current_dt: datetime) -> bool:
    """Returns if the EV is connected.

    Arguments:
      current_dt datetime:
        The current datetime.
    
    Returns:
        If the EV is connected."""
    assert self.list_days is not None
    plugged = False
    if current_dt.weekday() in self.list_days:
      current_time = current_dt.time()
      plugged = (self.arrival_time <= current_time <= self.departure_time)
    return plugged

  def get_plugged_profile(
      self, timesteps: npt.NDArray[np.datetime64]) -> npt.NDArray[Any]:
    """Returns the profile of the EV being connected.

    Arguments:
      timesteps npt.NDArray[np.datetime64]:
          A numpy array with the timesteps.
    
    Returns:
          A numpy array with the profile of the EV being connected."""
    return np.array([self.is_plugged(temp_dt) for temp_dt in timesteps])


@dataclass
class Battery:
  """Class used to model the battery of an EV and its charging process.

  Attributes:
    current_soc float:
      The current state of charge of the battery.
    target_soc float:
      The target state of charge of the battery.
    battery_size float:
      The size of the battery in kWh.
    schedule Schedule:
      The schedule of the EV.
    battery_losses float:
      The losses of the battery in %/timestep.
    initial_soc float:
      The initial state of charge of the battery.
  
  Methods:
    current_energy_stored:
      Returns the current energy stored in the battery.
    target_energy_stored:
      Returns the target energy stored in the battery.
    requested_energy:
      Returns the requested energy to be stored in the battery.
    target_charge_achieved:
      Returns if the target charge is achieved.
    calculate_charging_time:
      Calculates the charging time for different chargers.
    calculate_losses:
      Calculates the losses of the battery.
    battery_is_charging:
      Charges the battery if it is not fully charged.
    reset_current_soc:
      Resets the current state of charge of the battery.
    battery_is_plugged:
      Charges the battery if it is plugged.
    run_model:
      Runs the model of the battery."""
  current_soc: float
  target_soc: float
  battery_size: float
  schedule: Schedule
  battery_losses: float = 0  # %/timestep
  initial_soc: float = 0

  def __post_init__(self):
    if self.target_soc > 1:
      self.target_soc = 1
    if self.current_soc > 1:
      self.current_soc = 1
    self.initial_soc = self.current_soc

  @property
  def current_energy_stored(self) -> float:
    """
    Returns the current energy stored in the battery.
    
    Returns:
        The current energy stored in the battery."""
    return self.battery_size * self.current_soc

  @property
  def target_energy_stored(self) -> float:
    """Returns the target energy stored in the battery.

    Returns:
        The target energy stored in the battery."""
    return self.battery_size * self.target_soc

  @property
  def requested_energy(self) -> float:
    """Returns the requested energy to be stored in the battery.

    Returns:
        The requested energy to be stored in the battery."""
    return self.target_energy_stored - self.current_energy_stored

  def target_charge_achieved(self) -> bool:
    """Returns if the target charge is achieved.

    Returns:
        If the target charge is achieved."""
    return self.current_soc == self.target_soc

  def calculate_charging_time(
      self, chargers_max_output: list[float]) -> dict[int, float]:
    """Calculates the charging time based on different chargers.
    
    Arguments:
      chargers_max_output list[float]:
        The list of maximum outputs of the chargers.
        
    Returns:
      A dictionary with the charging time for different chargers."""
    charging_time_by_charger_output = {}
    for index, max_output in enumerate(chargers_max_output):
      charge_time = (self.target_soc -
                     self.current_soc) * self.battery_size / max_output
      charging_time_by_charger_output[index] = charge_time
    return charging_time_by_charger_output

  def calculate_losses(self) -> None:
    """Calculates the losses of the battery from the current State Of Charge."""
    self.current_soc = self.current_soc - self.battery_losses

  def battery_is_charging(self, energy_input: float) -> float:
    """Charges the battery if it is not fully charged.
    
    Arguments:
      energy_input float:
        The energy input to the battery.
    
    Returns:
        The energy input to the battery."""
    temp_charge_amount = self.current_soc * self.battery_size + energy_input
    if temp_charge_amount <= self.battery_size * self.target_soc:
      self.current_soc = temp_charge_amount / self.battery_size
    else:
      energy_input = self.target_energy_stored - self.current_energy_stored
      self.current_soc = self.target_soc
    return energy_input

  def reset_current_soc(self) -> None:
    """The current soc is resetted to its initial value.
    """
    self.current_soc = self.initial_soc

  def battery_is_plugged(self, current_dt: datetime,
                         energy_input: float) -> float:
    """Charges the battery if it is plugged and if it is not fully charged yet.
    
    Arguments:
      current_dt datetime:
        The current datetime.  
    energy_input float:
        The energy input to the battery.  
    
    Returns:
        The energy input to the battery."""
    if self.schedule.is_plugged(current_dt):
      if not self.target_charge_achieved():
        energy_input = self.battery_is_charging(energy_input)
      else:
        energy_input = 0
    else:
      self.reset_current_soc()
      energy_input = 0
    return energy_input

  def run_model(self, current_dt: datetime, energy_input: float) -> float:
    """Calculate losses and charge the EV if it is connected and if it is not fully charged yet.
    
    Arguments:
      current_dt datetime:
        The current datetime.  
      energy_input float:
        The energy input to the battery.  
        
    Returns:
        The energy input to the battery."""
    self.calculate_losses()
    energy_input = self.battery_is_plugged(current_dt, energy_input)
    return energy_input
