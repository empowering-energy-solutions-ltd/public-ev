from pathlib import Path

import pandas as pd
from timeseries.common import enums as pp_num
from timeseries.economic import tariff_creator


def import_electricity_prices() -> pd.DataFrame:
  """
  Import electricity prices from a csv file.
  
  Returns:
      A dataframe with the electricity prices.
  """
  elec_path = Path(r'..//data')
  fn = "Converted_electrical_invoices.csv"
  energy_price_dict = {pp_num.EnergyCarrier.ELECTRICITY: elec_path / fn}
  site_prices = tariff_creator.EnergyTariffImporter("site")
  site_prices.load_data(energy_price_dict)
  return site_prices.get_tariff_structure(1234)


def export_electricity_prices(year: int | None = None) -> pd.DataFrame:
  """
  Import electricity prices from a csv file.

  Arguments:
    year int | None:
      The year of the data to import. If None, all the data are imported.
  
  Returns:
      A dataframe with the electricity prices.
  """
  export_elec_path = Path(r'..//data')
  fn = "csv_agileoutgoing_G_North_Western_England.csv"
  export_dataf = pd.read_csv(export_elec_path / fn,
                             header=None,
                             names=[
                                 'Datetime', 'Time', 'Area code', 'Area name',
                                 'unit price (incl. VAT)'
                             ])
  export_dataf['Datetime'] = pd.to_datetime(export_dataf['Datetime'],
                                            format="%Y-%m-%d %H:%M:%S%z")
  export_dataf.set_index('Datetime', inplace=True)
  if year is None:
    export_dataf = export_dataf.loc[:, 'unit price (incl. VAT)'].to_frame()
  else:
    export_dataf = export_dataf.loc[export_dataf.index.year == year,
                                    'unit price (incl. VAT)'].to_frame()
  return export_dataf / 100  #Convert in GBP/kWh
