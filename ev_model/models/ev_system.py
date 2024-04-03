from dataclasses import dataclass, field

import pandas as pd
from e2slib.common import common
from e2slib.structures import enums as e2s_enums
from e2slib.structures import site_schema

from ev_model.data import enums
from ev_model.models import bricks, charger


@dataclass
class Ev_System:
  """Class to represent an EV system.
  
  Attributes:
    name (str): Name of the EV system.
    data_recorder (bricks.TimeserieRecorder): Data recorder to store the results of the simulation.
    dict_site_assets (dict[str, charger.Charger]): Dictionary of charger.Charger in the system.
    timezone (str): Timezone of the system.
    _size_system (float): Installed capacity of the system.
    technology_type (e2s_enums.TechnologyType): Technology type of the system.

  Methods:
    get_capacity_installed: 
      Return the total installed capacity of the site.
    run_default_simulation: 
      Run a default simulation of the system.
    get_recorded_data_from_chargers:
      Return the recorded energy consumption data from all chargers.
    size_system:
      Return the installed capacity of the system.
    capital_cost:
      Return the capital cost of the system.
    annual_maintenance_cost:
      Return the annual maintenance cost of the system.
    lifetime:
      Return the lifetime of the system.
    additional_demand:
      Return the additional demand of the system.
    onsite_generation:
      Return the onsite generation of the system.
    export_results:
      Export the results of the system.
    """
  name: str
  data_recorder: bricks.TimeserieRecorder
  dict_site_assets: dict[str, charger.Charger] = field(default_factory=dict)
  timezone: str = 'UTC'
  _size_system: float = 0  # kW
  technology_type: e2s_enums.TechnologyType = e2s_enums.TechnologyType.EV

  def __post_init__(self) -> None:
    capacity_installed = self.get_capacity_installed()
    self.size_system = capacity_installed
    self.get_recorded_data_from_chargers()

  def get_capacity_installed(self) -> float:
    """Return the total installed capacity of the site.
    
    Returns:
      float:
        The total installed capacity of the site."""
    return sum(temp_charger.max_output
               for temp_charger in self.dict_site_assets.values())

  def run_default_simulation(self) -> None:
    """Run a default simulation of the system.
    
    Returns:
      None"""

    timesteps = self.data_recorder.index
    for temp_charger in self.dict_site_assets.values():
      temp_charger.charging_profile(timesteps)
    self.get_recorded_data_from_chargers()

  def get_recorded_data_from_chargers(self) -> pd.DataFrame:
    """Return the recorded energy consumption data from all chargers.
    
    Returns:
      pd.DataFrame:
        A dataframe with the recorded energy consumption data from all chargers."""
    frames = []
    for temp_charger in self.dict_site_assets.values():
      frames.append(pd.concat(temp_charger.get_recorded_data(), axis=1))
    all_charging_profiles = pd.concat(frames, axis=1)
    self.data_recorder.record_batch_data(all_charging_profiles.index,
                                         all_charging_profiles.sum(axis=1),
                                         enums.SiteData.ENERGY_INPUT.name)
    return all_charging_profiles

  @property
  def size_system(self) -> dict[e2s_enums.TechnologyType, float]:
    """Return the installed capacity of the system.

    Returns:
        A dictionary with the installed capacity of the system."""
    return {self.technology_type: self._size_system}

  @size_system.setter
  def size_system(self, size_system: float) -> None:
    """Set the installed capacity of the system.

    Arguments:
      size_system float:
        The installed capacity of the system.
    """
    self._size_system = size_system

  @property
  def capital_cost(self) -> dict[e2s_enums.TechnologyType, float]:
    """Return the capital cost of the system.
    
    Returns:
        A dictionary with the capital cost of the system.
    """
    total_cost = 0
    for temp_charger in self.dict_site_assets.values():
      total_cost += temp_charger.specific_capital_cost
    return {self.technology_type: total_cost}

  @property
  def annual_maintenance_cost(self) -> dict[e2s_enums.TechnologyType, float]:
    """Return the annual maintenance cost of the system.

    Returns:
        A dictionary with the annual maintenance cost of the system.
    """

    total_maintenance_cost = 0
    for temp_charger in self.dict_site_assets.values():
      total_maintenance_cost += temp_charger.specific_maintenance_cost
    return {self.technology_type: total_maintenance_cost}

  @property
  def lifetime(self) -> int:
    """Return the lifetime of the system.

    Returns:
      The lifetime of the system.
    """

    first_charger = next(iter(self.dict_site_assets.values()))
    return first_charger.lifetime

  @property
  def additional_demand(self) -> pd.DataFrame:
    """Return the additional demand of the system.

    Returns:
        A dataframe with the additional demand of the system.
    """
    self.get_recorded_data_from_chargers()
    columns = common.get_multiindex_single_column(
        site_schema.SiteDataSchema.ADDITIONAL_ELECTRICITY_DEMAND)
    additional_demand_df = self.data_recorder.recorded_data[
        enums.SiteData.ENERGY_INPUT.name].to_frame()
    additional_demand_df.columns = columns
    return additional_demand_df

  @property
  def onsite_generation(self) -> pd.DataFrame:
    """Return the onsite generation of the system.

    Returns:
        A dataframe with the onsite generation of the system.
    """

    columns = common.get_multiindex_single_column(
        site_schema.SiteDataSchema.ELECTRICITY_GENERATION)
    onsite_generation = pd.DataFrame(index=self.additional_demand.index,
                                     columns=columns)
    onsite_generation.iloc[:, 0] = 0.
    return onsite_generation

  def export_results(self) -> pd.DataFrame:
    """Export the results of the system.

    Returns:
        A dataframe with the results of the system.
    """
    additional_demand = self.additional_demand
    on_site_gen = self.onsite_generation
    return pd.concat([additional_demand, on_site_gen], axis=1).astype(float)
