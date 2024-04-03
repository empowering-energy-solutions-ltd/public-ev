import pandas as pd

from ev_model.data import schema
from ev_model.models import sim_parameters


def create_dataf_for_control(target_dataf: pd.DataFrame,
                             electricity_demand: pd.DataFrame) -> pd.DataFrame:
  """
  Creates a dataframe for optization based on control method. 

  Arguments:
    target_dataf pd.DataFrame:
      A dataframe with the target data (site import limit, carbon intensity, cost).  
    electricity_demand pd.DataFrame:
      A dataframe with the electricity demand of the site.  

  Returns:
      A concated dataframe with the target data and the electricity demand.
  """

  if isinstance(target_dataf.columns, pd.MultiIndex):
    new_columns = target_dataf.columns.get_level_values(0).tolist()
    new_columns[0] = schema.OptimizerSchema.OPTIMIZER_TARGET
    target_dataf.columns = pd.MultiIndex.from_arrays(
        [new_columns, target_dataf.columns.get_level_values(1)])
    target_dataf.columns = [schema.OptimizerSchema.OPTIMIZER_TARGET]
  else:
    target_dataf.columns = [schema.OptimizerSchema.OPTIMIZER_TARGET]

  return pd.concat([target_dataf, electricity_demand], axis=1)


def create_dataf_base(electricity_demand: pd.DataFrame) -> pd.DataFrame:
  """ 
  Creates a base dataframe for optimization. 

  Arguments:
    electricity_demand pd.DataFrame:
      A dataframe with the electricity demand of the site.
      
  Returns:
      A dataframe with the electricity demand and the optimizer target."""
  dataf = electricity_demand.copy()
  if schema.OptimizerSchema.SITE_ENERGY in dataf.columns:
    dataf[schema.OptimizerSchema.SITE_LOAD] = dataf[
        schema.OptimizerSchema.
        SITE_ENERGY] / sim_parameters.POWER_TO_ENERGY_FACTOR
  dataf[schema.OptimizerSchema.OPTIMIZER_TARGET] = dataf.index.hour
  return dataf
