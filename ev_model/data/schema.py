class BatterySchema:
  INDEX = "Datetime"
  ENERGY = "Energy kWh"
  SOC = "State of charge (%)"


class PrintSchema:
  BASE_CONSUMPTION = 'Annual electrical consumption without chargers'
  SIM_CONSUMPTION = 'Annual electrical consumption with chargers'
  DIFF_CONSUMPTION = 'Additional consumption'
  KWH = 'kWh'
  BASE_POWER_PEAK = 'Top 1% mean power demand without chargers'
  SIM_POWER_PEAK = 'Top 1% mean power demand with chargers'
  KW = 'kW'
  BASE_CARBON = 'Annual carbon intensity without chargers'
  SIM_CARBON = 'Annual carbon intensity with chargers'
  TONNES = 'tonnes'
  BASE_COST = 'Annual cost of electricity without chargers, £'
  SIM_COST = 'Annual cost of electricity with chargers, £'
  CHARGER_COST = 'Cost of chargers, £'
  MAINTENANCE_COST = 'Estimated maintenance cost per year, £'
  DIFF_COST = 'Increase annual energy charge, £'
  CAPEX = 'Total capital costs due to EV chargers, £'
  OPEX = 'Total operational costs due to EV chargers, £'
  BREAK = '------------------------------------------------'


class PlotSchema:
  INDEX = 'index_range'
  DATETIME = 'Datetime (Timestep=30 minutes)'
  POWER = 'Power demand (kW)'
  ENERGY = 'Consumption (kWh)'
  CARBON = 'Carbon emissions (g)'
  TIME_DAY = 'Time of day'


class OptimizerSchema:
  CHARGER_LOAD_PROFILE = "charger load profile [kW]"
  OPTIMIZER_TARGET = "target"
  CUMULATIVE_ENERGY = "Cumulative energy [kWh]"
  SITE_ENERGY = "Site energy [kWh]"
  SITE_LOAD = "Site load [kW]"
