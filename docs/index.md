# Welcome to the EV tool

This project aims to simulate the effect of an EV charging system on a sites annual energy bills, consumption and carbon emissions. There are 3 basic optimization methods that show the varying effect on consumption, emissions and cost:

1. `Basic optimisation` ensures the system does not cause the site to exceed its load demand limit.
2. `Emission optimisation` ensures the verhicles are charged emitting the minimum amount of carbon possible, while keeping load demand in mind. This is done using energy generation emission data to optimise charging to times where the impact is its lowest.
3. `Cost optimisation` charges the vehicles when energy is its cheapest, while keeping load demand in mind. This is done using the sites annual energy price profile.

These optimisation options are displayed against the current site system to highlight the changes. An example of this can be found in `Demo_notebook.ipynb` in the `notebooks` folder.