from datetime import datetime
from enum import Enum

import numpy as np
import numpy.typing as npt
import pandas as pd

from ev_model.data import enums
from ev_model.models import (bricks, charger, ev_system, sim_parameters,
                             vehicles)


def get_list_columns(data_recorder_type: enums.DataRecorderType) -> list[Enum]:
  """Get the list of columns for the data recorder.
  
  Arguments:
    data_recorder_type enums.DataRecorderType:
      Type of data recorder.
  
  Returns:
      List of columns for the data recorder.
  """
  lookup_dict = {
      enums.DataRecorderType.CHARGER: list(enums.ChargerData),
      enums.DataRecorderType.EV: list(enums.EVData),
      enums.DataRecorderType.SITE: list(enums.SiteData),
  }
  return lookup_dict.get(data_recorder_type, ["Unknown data recorder type"])


def create_timesteps(start_date: datetime,
                     end_date: datetime) -> npt.NDArray[np.datetime64]:
  """Create a numpy array with the timesteps for the simulation.

  Arguments:
    start_date datetime:
      Start date of the simulation.
    end_date datetime:
      End date of the simulation.
  
  Returns:
      Numpy array with the timesteps for the simulation.
  """
  return pd.date_range(
      start=start_date,
      end=end_date,
      freq='30min',  # type: ignore
      tz='UTC').to_numpy()


def create_recorder(
    sim_year: int,
    data_recorder_type: enums.DataRecorderType) -> bricks.TimeserieRecorder:
  """Create a timeseries recorder for the simulation.

  Arguments:
    sim_year int:
      Year of the simulation.
    data_recorder_type enums.DataRecorderType:
      Type of data recorder.

  Returns:
      Timeseries recorder for the simulation.
  """
  start_date = datetime(sim_year, 1, 1, 0, 0)
  end_date = datetime(sim_year, 12, 31, 23, 59, 59)
  timesteps = create_timesteps(start_date, end_date)
  list_columns = get_list_columns(data_recorder_type)
  return bricks.TimeserieRecorder(timesteps, list_columns)


def create_single_EV(ev_name: str, sim_year: int, list_of_days: list[int],
                     battery_size: float) -> vehicles.EV:
  """Create a single EV object.
  
  Arguments:
    ev_name str:
      Name of the EV.
    sim_year int:
      Year of the simulation.
    list_of_days list[int]:
      List of days to create the EV schedule.
    battery_size float:
      Size of the EV battery.
      
  Returns:
      EV object."""
  ev_data_recorder = create_recorder(
      sim_year=sim_year, data_recorder_type=enums.DataRecorderType.EV)
  ev_schedule = bricks.Schedule(list_days=list_of_days)
  ev_battery = bricks.Battery(0.5, 1, battery_size, ev_schedule)
  return vehicles.EV(ev_name, ev_battery, ev_data_recorder)


def create_multiple_EVs(
    nb_evs: int,
    sim_year: int,
    list_of_days: list[int],
    min_battery_size: int = 60,
    max_battery_size: int = 120,
) -> list[vehicles.EV]:
  """Create a list of EVs.

  Arguments:
    nb_evs int:
      Number of EVs to create.
    sim_year int:
      Year of the simulation.
    list_of_days list[int]:
      List of days to create the EV schedule.
    min_battery_size int:
      Minimum size of the EV battery.
    max_battery_size int:
      Maximum size of the EV battery.

  Returns:
      List of EVs.
  """
  np.random.seed(sim_parameters.RANDOM_SEED)
  list_evs = []
  for ii in range(nb_evs):
    temp_name = f'EV_{ii+1}'
    battery_size = np.round(
        np.random.uniform(min_battery_size, max_battery_size), 2)
    temp_ev = create_single_EV(temp_name, sim_year, list_of_days, battery_size)
    list_evs.append(temp_ev)
  return list_evs


def set_fleet_charging_amount(list_evs: list[vehicles.EV],
                              charging_amount: float = 0.15) -> None:
  """Set the target state of charge for the fleet of EVs.

  Arguments:
    list_evs list[vehicles.EV]:
      List of EVs to set the target state of charge.
    charging_amount float:
      Amount of charge to add to the target state of charge.
  """
  for temp_ev in list_evs:
    temp_ev.battery.target_soc = temp_ev.battery.current_soc + charging_amount


def create_single_charger(
    charger_name: str,
    sim_year: int,
    charger_type: enums.ChargerType,
    charger_output: float,
    list_evs: list[vehicles.EV],
) -> charger.Charger:
  """ Create a single charger and assign a list of EVs to it.

  Arguments:
      charger_name str:
        Name of charger object.
      sim_year int:
        Year of the simulation.
      charger_type enums.ChargerType:
        Type of charger.
      charger_output float:
        Maximum output of the charger (E.g 7kW, 21kW).
      list_evs list[vehicles.EV]:
        List of EVs that to assign to the charger.

  Returns:
        Charger object with the assigned EVs.
  """
  charger_data_recorder = create_recorder(
      sim_year=sim_year, data_recorder_type=enums.DataRecorderType.CHARGER)
  return charger.Charger(name=charger_name,
                         charger_type=charger_type,
                         max_output=charger_output,
                         ev_list=list_evs,
                         no_connections=len(list_evs),
                         data_recorder=charger_data_recorder)


def create_multiple_chargers(
    list_evs: list[vehicles.EV], sim_year: int,
    charger_output: float) -> dict[str, charger.Charger]:
  """Create as many chargers as EVs and assign each EV to a charger.

  Arguments:
      list_evs list[vehicles.EV]:
        List of EVs to assign to the chargers.
      sim_year int:
        Year of the simulation.
      charger_output float:
        Maximum output of the charger (E.g 7kW, 21kW).
    
  Returns:
        Dictionary of charger objects with the assigned EVs."""
  np.random.seed(sim_parameters.RANDOM_SEED)
  dict_chargers = {}
  for ii, temp_ev in enumerate(list_evs):
    temp_ev_list = [temp_ev]
    temp_name = f'Charger_{ii+1}'
    temp_charger = create_single_charger(temp_name, sim_year,
                                         enums.ChargerType.LEVEL_2,
                                         charger_output, temp_ev_list)
    dict_chargers.update({temp_charger.name: temp_charger})
  return dict_chargers


def create_ev_system(
    sim_year: int,
    dict_chargers: dict[str, charger.Charger]) -> ev_system.Ev_System:
  """Create an EV system with a dictionary of chargers.
  
  Arguments:
    sim_year int:
      Year of the simulation.
    dict_chargers dict[str, charger.Charger]:
      Dictionary of charger objects.
      
  Returns:
      EV system object."""
  site_data_recorder = create_recorder(
      sim_year=sim_year, data_recorder_type=enums.DataRecorderType.SITE)
  ev_system_name = 'EV_System'
  return ev_system.Ev_System(ev_system_name, site_data_recorder, dict_chargers)
