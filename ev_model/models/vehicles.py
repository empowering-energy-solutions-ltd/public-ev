from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from ev_model.data import enums
from ev_model.models import bricks


@dataclass
class EV:
  """ Class to represent an EV. 

  Attributes:
    name: str
      Name of the EV.
    battery: bricks.Battery
      Battery of the EV.
    data_recorder: bricks.TimeserieRecorder
      Data recorder to store the results of the simulation.
      
  Methods:
    charging_profile: 
      Return the charging profile of the EV.
    get_recorded_data: 
      Return the recorded data of the EV.
  """
  name: str
  battery: bricks.Battery
  data_recorder: bricks.TimeserieRecorder

  def charging_profile(
      self, timesteps: npt.NDArray[np.datetime64],
      charger_max_energy_outputs: npt.NDArray[np.float64]
  ) -> npt.NDArray[np.float64]:
    """Run the charging profile of the EV.

    Arguments:
      timesteps npt.NDArray[np.datetime64]:
        Timesteps for the simulation.
      charger_max_energy_outputs npt.NDArray[np.float64]:
        Maximum energy output of the charger.

    Returns:
        Energy input of the EV.
    """
    soc_arr = np.zeros(len(timesteps))
    energy_input_arr = np.zeros(len(timesteps))
    plugged_flag_arr = np.zeros(len(timesteps))
    for index, charge_timestep in enumerate(timesteps):
      # print(charge_timestep, charger_energy_output)
      current_charger_output = charger_max_energy_outputs[index]
      current_charger_output = self.battery.run_model(charge_timestep,
                                                      current_charger_output)
      soc_arr[index] = self.battery.current_soc
      energy_input_arr[index] = current_charger_output
      plugged_flag_arr[index] = self.battery.schedule.is_plugged(
          charge_timestep)

    self.data_recorder.record_batch_data(timesteps, soc_arr,
                                         enums.EVData.SOC.name)
    self.data_recorder.record_batch_data(timesteps, energy_input_arr,
                                         enums.EVData.ENERGY_INPUT.name)
    self.data_recorder.record_batch_data(timesteps, plugged_flag_arr,
                                         enums.EVData.PLUGGED.name)
    return energy_input_arr

  def get_recorded_data(self) -> dict[str, npt.NDArray[np.float64]]:
    """Return the recorded data of the EV.

    Returns:
        A dictionary with the recorded data of the EV.
    """
    return {self.name: self.data_recorder.recorded_data}
