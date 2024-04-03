from enum import Enum, auto


class ChargerType(Enum):
  'Slow, medium or fast charger'
  LEVEL_1 = auto()
  LEVEL_2 = auto()
  LEVEL_3 = auto()


class SiteScheduleOptimzer(Enum):
  'Availability, emissions or price'
  BASE_OPTIMIZER = auto()
  EMISSION_OPTIMIZER = auto()
  PRICE_OPTIMIZER = auto()
  PV_OPTIMIZER = auto()


class DataRecorderType(Enum):
  'Type of data recorder'
  EV = auto()
  CHARGER = auto()
  SITE = auto()


class EVData(Enum):

  @staticmethod
  def _generate_next_value_(name, start, count, last_values):
    return count

  TIMESTEP = auto()
  SOC = auto()
  ENERGY_INPUT = auto()
  PLUGGED = auto()


class ChargerData(Enum):

  @staticmethod
  def _generate_next_value_(name, start, count, last_values):
    return count

  TIMESTEP = auto()
  ENERGY_INPUT = auto()


class SiteData(Enum):

  @staticmethod
  def _generate_next_value_(name, start, count, last_values):
    return count

  TIMESTEP = auto()
  ENERGY_INPUT = auto()
