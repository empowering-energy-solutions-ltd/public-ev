from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import numpy.typing as npt
import pandas as pd
from e2slib.structures import site_schema

from ev_model.data import data_processing, schema
from ev_model.data.enums import SiteScheduleOptimzer
from ev_model.data.schema import OptimizerSchema
from ev_model.models import bricks, charger, ev_system, sim_parameters, vehicles


def charger_load_availability_profile(
    site_load_demand_profile: npt.NDArray[np.float64],
    max_import_demand: pd.DataFrame,
    max_charger_output: float,
    existing_load_demand: npt.NDArray[np.float64] | None = None
) -> npt.NDArray[np.float64]:
  """
  Calculate the load availability profile from a charger based on the max import demand constraint.

  Arguments:
    site_load_demand_profile npt.NDArray[np.float64]:
      The site load demand profile.
    max_import_demand pd.DataFrame:
      The maximum import demand for each timestep.
    max_charger_output float:
      The maximum charger output.
    existing_load_demand npt.NDArray[np.float64] | None:
      The existing load demand.

  Returns:
      The charger load availability profile."""
  if existing_load_demand:
    pass
  else:
    charger_max_load_profile = np.where(
        site_load_demand_profile + max_charger_output > max_import_demand,
        max_import_demand - site_load_demand_profile, max_charger_output)
    charger_max_load_profile = np.where(charger_max_load_profile < 0, 0,
                                        charger_max_load_profile)
    return charger_max_load_profile


def optimizer_selector(
    electricity_demand: pd.DataFrame,
    target_dataf: pd.DataFrame | None = None) -> pd.DataFrame:
  """ 
  Choose between basic, emissions or price controls to optimize charging.

  Arguments:
    electricity_demand pd.DataFrame:
      The electricity demand.
    target_dataf pd.DataFrame:
      The target dataframe (carbon, price, basic).

  Returns:
      A dataframe containing site demand and the chosen control method.
  """
  if target_dataf is None:
    return data_processing.create_dataf_base(electricity_demand)
  elif target_dataf.equals(electricity_demand):
    dataf = data_processing.create_dataf_for_control(target_dataf,
                                                     electricity_demand)
    dataf[schema.OptimizerSchema.SITE_ENERGY] = dataf.iloc[:, 0]
    dataf = dataf.iloc[:, 1:3]
    return dataf
  else:
    return data_processing.create_dataf_for_control(target_dataf,
                                                    electricity_demand)


def combine_load_profile(site_dataf: pd.DataFrame, new_ev: vehicles.EV,
                         max_import_demand: pd.DataFrame,
                         max_charger_output: float) -> pd.DataFrame:
  """ 
  Combines the basic charger availability load profile with EV availability and 
  ensures it won't exceed the demand limit.
  
  Arguments:
    site_dataf pd.DataFrame:
      The site data frame.
    new_ev vehicles.EV:
      The new EV.
    max_import_demand pd.DataFrame:
      The maximum import demand.
    max_charger_output float:
      The maximum charger output.

  Returns:
      The combined load profile.
  """
  site_dataf[OptimizerSchema.CHARGER_LOAD_PROFILE] = 0
  plugged_time = new_ev.battery.schedule.get_plugged_profile(site_dataf.index)
  site_dataf.loc[plugged_time, OptimizerSchema.
                 CHARGER_LOAD_PROFILE] = charger_load_availability_profile(
                     site_dataf.loc[plugged_time, OptimizerSchema.SITE_ENERGY]
                     / sim_Arguments.POWER_TO_ENERGY_FACTOR,
                     max_import_demand.loc[
                         plugged_time,
                         site_schema.ResultsSchema.PEAK_ELECTRICITY_IMPORT],
                     max_charger_output)
  return site_dataf


def cumsum_energy_consumed(site_dataf: pd.DataFrame,
                           ascending: bool = True) -> pd.DataFrame:
  """ Creates a cumulated energy column to identify when required charge is reached. 

  Arguments:
    site_dataf pd.DataFrame:
      The site dataframe.
    ascending bool:
      The ascending order.

  Returns:
      The data frame with the cumulative energy consumed."""
  temp_dataf = site_dataf.copy()
  target_col = OptimizerSchema.OPTIMIZER_TARGET
  temp_dataf = temp_dataf.sort_values(target_col, ascending=ascending)
  temp_dataf[OptimizerSchema.CUMULATIVE_ENERGY] = (
      temp_dataf[OptimizerSchema.CHARGER_LOAD_PROFILE] *
      sim_Arguments.POWER_TO_ENERGY_FACTOR).cumsum()
  return temp_dataf


def find_last_index(dataf: pd.DataFrame, energy_required: float) -> int:
  """ Finds the index where target charge is achieved.

  Arguments:
    dataf pd.DataFrame:
      The dataframe.
    energy_required float:
      The energy required to reach full charge.

  Returns:
      The last index."""
  last_index = len(
      dataf[dataf[OptimizerSchema.CUMULATIVE_ENERGY] < energy_required]) + 1
  if last_index > len(dataf):
    last_index = len(dataf)
  return last_index


def generate_filter(dataf: pd.DataFrame,
                    energy_required: float) -> npt.NDArray[np.bool_]:
  """ Generates a filter to identify and extract the data for when the target charge is achieved.

  Arguments:
    dataf pd.DataFrame:
      The dataframe.
    energy_required float:
      The energy required.

  Returns:
      The filter.
  """
  # temp_dataf = dataf.copy()
  last_charging_index = find_last_index(dataf, energy_required)
  filt = np.full(len(dataf), False)
  filt[:last_charging_index] = True
  return filt


def calculate_optimized_charging_profile(
    dataf: pd.DataFrame, energy_required: float) -> npt.NDArray[np.float64]:
  """ Calculates the updated optimized charging profile and returns it.

  Arguments:
    dataf pd.DataFrame:
      The dataframe.
    energy_required float:
      The energy required.

  Returns:
      The updated charging profile.
  """
  temp_dataf = dataf.copy()
  filt = generate_filter(temp_dataf, energy_required)

  org_charger_load_profile = temp_dataf.loc[
      filt, OptimizerSchema.CHARGER_LOAD_PROFILE].values

  total_charger_energy_output = 0
  updated_charger_load_profile = np.zeros(len(org_charger_load_profile))
  for ii, temp_charger_power_output in enumerate(org_charger_load_profile):
    temp_charger_energy_output = temp_charger_power_output * sim_Arguments.POWER_TO_ENERGY_FACTOR
    if total_charger_energy_output + temp_charger_energy_output > energy_required:

      temp_charger_energy_output = (energy_required -
                                    total_charger_energy_output)
      temp_charger_power_output = temp_charger_energy_output / sim_Arguments.POWER_TO_ENERGY_FACTOR

    total_charger_energy_output += temp_charger_energy_output
    updated_charger_load_profile[ii] = temp_charger_power_output
  return updated_charger_load_profile


def apply_new_charging_profile(dataf: pd.DataFrame,
                               energy_required: float) -> pd.DataFrame:
  """ Applies the new charger load profile to the dataframe removing the additional 
    cumulative values and sorts back to chronological order.

  Arguments:
    dataf pd.DataFrame:
      The dataframe.
    energy_required float:
      The energy required.

  Returns:
      The updated dataframe.
  """
  temp_dataf = dataf.copy()
  filt = generate_filter(dataf, energy_required)
  updated_charger_load_profile = calculate_optimized_charging_profile(
      dataf, energy_required)
  temp_dataf.loc[
      filt,
      OptimizerSchema.CHARGER_LOAD_PROFILE] = updated_charger_load_profile
  temp_dataf.loc[
      ~filt,
      OptimizerSchema.CHARGER_LOAD_PROFILE] = 0  #set everything else to 0
  return temp_dataf[
      OptimizerSchema.CHARGER_LOAD_PROFILE].to_frame().sort_index()


def run_optimizer(dict_chargers: dict[str,
                                      charger.Charger], site_df: pd.DataFrame,
                  max_import_demand: pd.DataFrame) -> pd.DataFrame:
  """ Loops through each charger and EV to apply a controlled charging profile to each one.

  Arguments:
    dict_chargers dict[str, charger.Charger]:
      The dictionary of chargers.
    site_df pd.DataFrame:
      The site data frame.
    max_import_demand pd.DataFrame:
      The maximum import demand.

  Returns:
      The results dataframe.
  """
  results_df = site_df.copy()
  site_demand = site_df[OptimizerSchema.SITE_ENERGY].sum()
  max_site_load = site_df[
      OptimizerSchema.SITE_ENERGY].max() / sim_Arguments.POWER_TO_ENERGY_FACTOR
  print(
      f'The site demand is {site_demand} kWh and max import {max_site_load} kW'
  )
  for sim_charger in dict_chargers.values():
    for temp_ev in sim_charger.ev_list:
      charger_load_profile = get_charging_profile_for_year(
          site_df, temp_ev, sim_charger.max_output, max_import_demand)
      sim_charger.charging_profile(
          charger_load_profile.index,
          charger_load_profile[OptimizerSchema.CHARGER_LOAD_PROFILE].values)
      charger_energy_demand = sim_charger.data_recorder.recorded_data[
          'ENERGY_INPUT'].values  #kWh
      site_df[OptimizerSchema.SITE_ENERGY] += charger_energy_demand
      ev_demand = np.sum(charger_energy_demand)
      site_demand = site_df[OptimizerSchema.SITE_ENERGY].sum()
      max_site_load = site_df[OptimizerSchema.SITE_ENERGY].max(
      ) / sim_Arguments.POWER_TO_ENERGY_FACTOR
    results_df[sim_charger.name] = sim_charger.data_recorder.recorded_data[
        'ENERGY_INPUT'].values
  return results_df


def get_charging_profile_for_single_day(
    day_dataf: pd.DataFrame, ev: vehicles.EV, max_import_demand: pd.DataFrame,
    max_charger_load: float) -> pd.DataFrame:
  """ Applies the charging profile to a single day of data.

  Arguments:
    day_dataf pd.DataFrame:
      The day data frame.
    ev vehicles.EV:
      The EV.
    max_import_demand pd.DataFrame:
      The maximum import demand.
    max_charger_load float:
      The maximum charger load.

  Returns:
      The updated dataframe.
    
  """
  day_dataf = (day_dataf.pipe(
      combine_load_profile, ev, max_import_demand,
      max_charger_load).pipe(cumsum_energy_consumed).pipe(
          apply_new_charging_profile, ev.battery.requested_energy))
  return day_dataf


def get_single_day_data(temp_date: datetime.date,
                        site_data: pd.DataFrame) -> pd.DataFrame:
  """ 
  Extracts the data for a single day.

  Arguments:
    temp_date datetime.date:
      The date.
    site_data pd.DataFrame:
      The site data frame.

  Returns:
      The data frame for the single day."""
  filt = (site_data.index.date == temp_date)
  return site_data[filt].copy()


def get_charging_profile_for_year(site_data: pd.DataFrame,
                                  temp_ev: vehicles.EV,
                                  max_charger_output: float,
                                  max_import_demand: pd.DataFrame) -> None:
  """ Applies controls to a charger and its EVs to each day of the year. 
  
  Arguments:
    site_data pd.DataFrame:
      The site data frame.
    temp_ev vehicles.EV:
      The EV.
    max_charger_output float:
      The maximum charger output.
    max_import_demand pd.DataFrame:
      The maximum import demand.

  Returns:
      The charging profile for the year."""
  new_frames = []
  for temp_date in set(site_data.index.date):
    day_dataf: pd.DataFrame = get_single_day_data(temp_date, site_data)
    day_import_demand: pd.DataFrame = get_single_day_data(
        temp_date, max_import_demand)
    day_dataf = get_charging_profile_for_single_day(day_dataf, temp_ev,
                                                    day_import_demand,
                                                    max_charger_output)
    new_frames.append(day_dataf)
  charger_load_profile = pd.concat(new_frames).sort_index()
  return charger_load_profile


@dataclass
class Optimized_Sites:
  """ Class to run the optimizer for each control method.
  
  Attributes:
    timesteps npt.NDArray[np.datetime64]:
      The timesteps.
    site_electricity_demand pd.DataFrame:
      The site electricity demand.
    dict_of_chargers dict[str, charger.Charger]:
      The dictionary of chargers.
    site_data_recorder bricks.TimeserieRecorder:
      The site data recorder.
    max_import_demand pd.DataFrame:
      The maximum import demand.
    carbon_dataf pd.DataFrame | None:
      The carbon data frame.
    price_dataf pd.DataFrame | None:
      The price data frame.
    pv_dataf pd.DataFrame | None:
      The PV data frame.
  
  Methods:
    site_dataf_creator(control_type):
      Creates the site data frame.
    run_controller_optimizer():
      Runs the optimizer.
    calculate_totals():
      Calculates the totals.
    generate_controlled_site():
      Generates the controlled site.
    site_charging_profiles():
      Generates the site charging profiles.
    run_control_method():
      Runs the control method.
    run_all_control_methods():
      Runs all control methods.
  """

  timesteps: npt.NDArray[np.datetime64]
  site_electricity_demand: pd.DataFrame
  dict_of_chargers: dict[str, charger.Charger]
  site_data_recorder: bricks.TimeserieRecorder
  max_import_demand: pd.DataFrame
  carbon_dataf: pd.DataFrame | None = None
  price_dataf: pd.DataFrame | None = None
  pv_dataf: pd.DataFrame | None = None

  def site_dataf_creator(self,
                         control_type: SiteScheduleOptimzer) -> pd.DataFrame:
    """ Creates the site data frame.

    Arguments:
      control_type SiteScheduleOptimzer:
          The control type.
    
    Returns:
        The site data frame."""
    if control_type is SiteScheduleOptimzer.BASE_OPTIMIZER:
      return optimizer_selector(self.site_electricity_demand)
    elif control_type is SiteScheduleOptimzer.EMISSION_OPTIMIZER:
      return optimizer_selector(self.site_electricity_demand,
                                self.carbon_dataf)
    elif control_type is SiteScheduleOptimzer.PRICE_OPTIMIZER:
      return optimizer_selector(self.site_electricity_demand, self.price_dataf)
    elif control_type is SiteScheduleOptimzer.PV_OPTIMIZER:
      return optimizer_selector(target_dataf=self.pv_dataf,
                                electricity_demand=self.pv_dataf)

  def run_controller_optimizer(
      self, site_dataf: pd.DataFrame,
      chargers: dict[str, charger.Charger]) -> pd.DataFrame:
    """ 
    Runs the optimizer.
    
    Arguments:
      site_dataf pd.DataFrame:
        The site dataframe based on the control type.  
      chargers dict[str, charger.Charger]:
        The dictionary of chargers.  
      
    Returns:
      The results dataframe.
    """

    return run_optimizer(chargers, site_dataf, self.max_import_demand)

  def calculate_totals(
      self, site_dataf: pd.DataFrame,
      chargers_dict: dict[str, charger.Charger]) -> npt.NDArray[np.float64]:
    """ 
    Calculates the totals.
    
    Arguments:
      site_dataf pd.DataFrame:
        The site data frame.  
      chargers_dict dict[str, charger.Charger]:
        The dictionary of chargers.  
    
    Returns:
       The totals.
    """
    totals = np.zeros(len(site_dataf))
    for one_charger in chargers_dict.values():
      totals += (one_charger.data_recorder.recorded_data['ENERGY_INPUT'].values
                 ) / sim_Arguments.POWER_TO_ENERGY_FACTOR
    return totals

  def generate_controlled_site(
      self, chargers: dict[str, charger.Charger], site_dataf: pd.DataFrame,
      control_type: SiteScheduleOptimzer) -> ev_system.Ev_System:
    """
    Generates the controlled site.

    Arguments:
      chargers dict[str, charger.Charger]:
        The dictionary of chargers.
      site_dataf pd.DataFrame:
        The site data frame.
      control_type SiteScheduleOptimzer:
        The control type.

    Returns:
        The controlled site.
    """
    site_name = control_type.name + '_SITE'
    return ev_system.Ev_System(site_name, deepcopy(self.site_data_recorder),
                               chargers)

  def site_charging_profiles(self, controlled_site: ev_system.Ev_System,
                             site_dataf: pd.DataFrame,
                             chargers: dict[str, charger.Charger]) -> None:
    """
    Generates the site charging profiles.

    Arguments:
      controlled_site ev_system.Ev_System:
        The controlled site.
      site_dataf pd.DataFrame:
        The site data frame.
      chargers dict[str, charger.Charger]:
        The dictionary of chargers.
    """
    controlled_site.get_recorded_data_from_chargers()

  def run_control_method(
      self, control_type: SiteScheduleOptimzer) -> ev_system.Ev_System | None:
    """
    Runs the control method.

    Arguments:
      control_type SiteScheduleOptimzer:
        The control type.
    
    Returns:
        The controlled site or None.
    """
    if (self.carbon_dataf is None
        and control_type == SiteScheduleOptimzer.EMISSION_OPTIMIZER) or (
            self.price_dataf is None
            and control_type == SiteScheduleOptimzer.PRICE_OPTIMIZER) or (
                self.pv_dataf is None
                and control_type == SiteScheduleOptimzer.PV_OPTIMIZER):
      print(
          f"{control_type.name} could not be executed as profile was not supplied."
      )
    else:
      copy_chargers = deepcopy(self.dict_of_chargers)
      site_dataf = self.site_dataf_creator(control_type)
      self.run_controller_optimizer(site_dataf, copy_chargers)
      gen_site = self.generate_controlled_site(
          chargers=copy_chargers,
          site_dataf=self.site_electricity_demand,
          control_type=control_type)
      self.site_charging_profiles(gen_site, site_dataf, copy_chargers)
      return gen_site

  def run_all_control_methods(self) -> dict[str, ev_system.Ev_System]:
    """
    Runs all control methods.

    Returns:
        A dictionary with the controlled sites.
    """
    basic_site = self.run_control_method(SiteScheduleOptimzer.BASE_OPTIMIZER)
    emissions_site = self.run_control_method(
        SiteScheduleOptimzer.EMISSION_OPTIMIZER)
    price_site = self.run_control_method(SiteScheduleOptimzer.PRICE_OPTIMIZER)
    pv_site = self.run_control_method(SiteScheduleOptimzer.PV_OPTIMIZER)
    return {
        'Basic': basic_site,
        'Emission': emissions_site,
        'Price': price_site,
        'PV': pv_site
    }
