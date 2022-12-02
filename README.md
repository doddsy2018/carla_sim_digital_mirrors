# carla_sim
Carla Simulator client - xbox360 joystick control, rear view mirrors, share memory model

## Introduction

This code demonstrates how to share carla data between different python processes via a [shared memory dictionary](https://pypi.org/project/shared-memory-dict/).  

Features
- Uses xbox360 controller
- Mirror sensor camera images are processed and stored in a shared memory object
- Main simulation thread uses pygame window.
- Share memory is accessed by the mirror view routines and displayed using opencv

## Prerequisites

- Download and Install Carla Simualtor 0.9.13 
    - (https://carla.org/)
    - (https://github.com/carla-simulator/carla)
    - (https://github.com/carla-simulator/carla/releases/tag/0.9.13)
- Download and Install AdditionalMaps_0.9.13
- Install Python 3.8.10
- Install Poetry Dependency Management (https://python-poetry.org/docs/)

## Setup and Execute

- `poetry install` - setup the environment
- Ensure the Carla Simulator is running on localhost and listening to port 2000
  - `.\CarlaUE4.exe -windowed -ResX=1024 -ResY=786 -carla-rpc-port=2000 -quality-level=High`
- `poetry run python sim_main.py` - main simulation thread
- `poetry run python mirror_views.py` - dual mirror views
- `poetry run python right_mirror_view.py` - rigth mirror only
- `poetry run python left_mirror_view.py` - left mirror only

## Utilities

- `poetry run python util_get_joystick_values.py` - Display joystick values untility tool

## Screenshot

![screenshot](./images/sim_view.PNG)



