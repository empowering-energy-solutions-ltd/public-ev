EV
==============================

Documentation available at: https://vigilant-invention-wo4gg4l.pages.github.io/

This project aims to simulate the effect of an EV charging system on a sites annual energy bills, consumption and carbon emissions. There are 3 basic optimization methods that show the varying effect on consumption, emissions and cost:

1. `Basic optimisation` ensures the system does not cause the site to exceed its load demand limit.
2. `Emission optimisation` ensures the verhicles are charged emitting the minimum amount of carbon possible, while keeping load demand in mind. This is done using energy generation emission data to optimise charging to times where the impact is its lowest.
3. `Cost optimisation` charges the vehicles when energy is its cheapest, while keeping load demand in mind. This is done using the sites annual energy price profile.

These optimisation options are displayed against the current site system to highlight the changes. An example of this can be found in `Demo_notebook.ipynb` in the `notebooks` folder.


Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    │
    ├── notebooks          <- Jupyter notebooks.
    │   └── Demo_notebook.ipynb      <- Demonstration notebook to show how to use the EV tool.
    │
    ├── ev_model          <- EV system modeling tool
    │   │
    │   ├── __init__.py
    │   │
    │   ├── data
    │   │   │
    │   │   ├── data_processing.py     <- scripts to generate dataframes for optimisation
    │   │   ├── enums.py     <- Enum script for project
    │   │   ├── example_data_import.py     <- Scripts for importing invoice data and energy export data from data folder
    │   │   ├── schema.py     <- Schema scripts for project
    │   │   └── viz_functions.py     <- Visualisation class for plotting ev modeling results
    │   │
    │   └── models     <- Scripts to generate a ev charging system
    │       ├── bricks.py     <- Scripts for the TimeseriesRecorder, Schedule and EV Battery
    │       ├── charger.py     <- Scripts to create a charger object
    │       ├── controller.py     <- Scripts that control charging profiles & optimisation
    │       ├── ev_system.py     <- Class to concat all elements of the EV system into one class
    │       ├── sim_functions.py     <- Scripts to generate a simulated system
    │       ├── sim_parameters.py     <- Script holding simulation settings
    │       └── vehicles.py     <- Class representing a complete EV
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment for pip package installation
    │                         
    └── pyproject.toml   <- .toml file for poetry to create a venv for package management


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
