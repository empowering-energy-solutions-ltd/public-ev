import copy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from e2slib.common import datetime_schema as dt_schema
from e2slib.common import functions, site_schema

from ev_model.data import schema
from ev_model.models.ev_system import Ev_System


class SitePlotter:
  """ Class to create plots for the site demand and the simulated demand.  
      ------------  NOT FUNCTIONAL  ------------

  Attributes:
    site_demand pd.DataFrame:
        A dataframe with the site demand.
    sim_demand pd.DataFrame: 
        A dataframe with the simulated demand.
  
  Methods:
    combined_sim_and_site: 
        Combines the site demand and the simulated demand.
    plot_for_a_week: 
        Plots the demand for a week.
    plot_base_profile: 
        Plots the site demand for a week.
    plot_simulated_profile: 
        Plots the simulated demand for a week.
    plot_base_simulated_combined_power: 
        Plots the site and simulated demand for a week.
    plot_base_simulated_combined_profile: 
        Plots the site and simulated demand for a week.
    create_plots: 
        Creates the plots.
  """

  def __init__(self, site: Ev_System):
    self.site_demand = site.site_electricity_demand
    self.sim_demand = site.data_recorder.recorded_data

  def combined_sim_and_site(self) -> pd.DataFrame:
    """
    Combines the site demand and the simulated demand.
    
    Returns:
      pd.DataFrame
        A dataframe with the combined demand.
    """
    data = self.site_demand[
        site_schema.SiteDataSchema.
        IMPORT_ELECTRICITY_DEMAND] + self.sim_demand['ENERGY_INPUT']
    return pd.DataFrame(
        data, columns=[site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND])

  def plot_for_a_week(self, var_name: str) -> pd.DataFrame:
    """
    Plots the demand for a week.

    Arguments:
      var_name str:
        The name of the variable to plot.  

    Returns;
      pd.DataFrame
        A dataframe with the demand for a week.  
    """
    if var_name == 'site_demand':
      new_dataf = self.site_demand.iloc[1104:].head(336).copy()
      new_dataf.index = pd.to_datetime(new_dataf.index,
                                       format='%Y-%m-%d %H:%M:%S')
      new_dataf[schema.PlotSchema.INDEX] = np.linspace(0, 7, len(new_dataf))
    elif var_name == 'sim_demand':
      new_dataf = self.sim_demand.iloc[1104:].head(336).copy()
      new_dataf.index = pd.to_datetime(new_dataf.index,
                                       format='%Y-%m-%d %H:%M:%S')
      new_dataf[schema.PlotSchema.INDEX] = np.linspace(0, 7, len(new_dataf))
      new_dataf = new_dataf.rename(
          {
              'ENERGY_INPUT':
              site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND
          },
          axis=1)
    elif var_name == 'combined_demand':
      new_dataf = self.combined_sim_and_site().iloc[1104:].head(336).copy()
      new_dataf.index = pd.to_datetime(new_dataf.index,
                                       format='%Y-%m-%d %H:%M:%S')
      new_dataf[schema.PlotSchema.INDEX] = np.linspace(0, 7, len(new_dataf))
    return new_dataf

  def plot_base_profile(self, title: str, ylim_max: float) -> plt.Axes:
    """
    Plots the site demand for a week.

    Arguments:
      title str:
        The title of the plot.  
      ylim_max float:
        The maximum value of the y-axis.  
    
    Returns:
      plt.Axes
        The plot.
    """
    dataf = self.plot_for_a_week('site_demand')
    plt.plot(dataf[schema.PlotSchema.INDEX],
             dataf[site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND] * 2)
    plt.xlabel(schema.PlotSchema.DATETIME)
    plt.ylabel(schema.PlotSchema.POWER)
    plt.title(title)
    plt.ylim(-1, ylim_max)
    plt.grid()
    plt.show()

  def plot_simulated_profile(self, title: str, ylim_max: float) -> plt.Axes:
    """
    Plots the simulated demand for a week.
    
    Arguments:
      title str:
        The title of the plot.  
      ylim_max float:
        The maximum value of the y-axis.  
    
    Returns:
      plt.Axes:
        The plot.
    """
    dataf = self.plot_for_a_week('sim_demand')
    plt.plot(dataf[schema.PlotSchema.INDEX],
             dataf[site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND] * 2)
    plt.xlabel(schema.PlotSchema.DATETIME)
    plt.ylabel(schema.PlotSchema.POWER)
    plt.title(title)
    plt.ylim(-1, ylim_max)
    plt.grid()
    plt.show()

  def plot_base_simulated_combined_power(self, title: str,
                                         ylim_max: float) -> plt.Axes:
    """
    Plots the site and simulated demand for a week.

    Arguments:
      title str:
        The title of the plot.  
      ylim_max float:
        The maximum value of the y-axis.  
    
    Returns:
      plt.Axes:
        The plot.
    """
    base_df = self.plot_for_a_week('site_demand')
    sim_df = self.plot_for_a_week('combined_demand')
    plt.fill_between(
        base_df[schema.PlotSchema.INDEX],
        base_df[site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND] *
        2,  # type: ignore
        sim_df[site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND] *
        2)  # type: ignore
    plt.plot(base_df[schema.PlotSchema.INDEX],
             base_df[site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND] * 2)
    plt.plot(base_df[schema.PlotSchema.INDEX],
             sim_df[site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND] * 2)
    plt.xlabel(schema.PlotSchema.DATETIME)
    plt.ylabel(schema.PlotSchema.POWER)
    plt.title(title)
    plt.xlim(0, 5)
    plt.ylim(-1, ylim_max)
    plt.grid()
    plt.show()

  def plot_base_simulated_combined_profile(self, title: str,
                                           ylim_max: float) -> plt.Axes:
    """
    Plots the site and simulated demand for a week.

    Arguments
    ----------
    `title`: `str`
        The title of the plot.  
    `ylim_max`: `float`
        The maximum value of the y-axis.  

    Returns
    -------
    `plt.Axes`
        The plot.
    """

    sim_df = self.plot_for_a_week('combined_demand')
    plt.plot(sim_df[schema.PlotSchema.INDEX],
             sim_df[site_schema.SiteDataSchema.IMPORT_ELECTRICITY_DEMAND])
    plt.xlabel(schema.PlotSchema.DATETIME)
    plt.ylabel(schema.PlotSchema.ENERGY)
    plt.title(title)
    plt.ylim(-1, ylim_max)
    plt.grid()
    plt.show()

  def create_plots(self, ylim_max: float) -> None:
    """
    Creates the plots.

    Arguments
    ----------
    `ylim_max`: `float`
        The maximum value of the y-axis.
    
    Returns
    -------
    `None`
    """

    self.plot_base_profile('Power demand of site over a week (January 2022)',
                           ylim_max=ylim_max)
    self.plot_simulated_profile(
        'Simuated power demand of site over a week (January 2022)',
        ylim_max=ylim_max)
    self.plot_base_simulated_combined_power(
        'Power demand of site with chargers over a week (January 2022)',
        ylim_max=ylim_max)
    self.plot_base_simulated_combined_profile(
        'Consumption profile of site over a week (January 2022)',
        ylim_max=ylim_max)
