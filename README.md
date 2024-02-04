## Flood Adaptation Model
Created by: SEN1211 Group 03

|        Name        | Student Number |
|:------------------:|:--------|
|    Canan Tezgeç    | 5721482 |
|     Yongxue Tian   | 5767695 |
|   Anne Stehouwer   | 4455142 |

 
### Introduction
This directory contains an agent-based model (ABM) implemented in Python, focused on simulating household adaptation to flood events utilizing Expected Utility Theory. It uses the Mesa framework for ABM and incorporates geographical data processing for flood depth and damage calculations.

### Installation
To set up the project environment, follow these steps:
1. Open the folder in your favorite IDE, e.g. VS Code, PyCharm
2. Configure Python interpreter (3.11 recommended)
3. Setup a virtual environment, venv, activate it in the terminal
4. Run ```pip install -r requirements.txt``` to install the required packages

### File descriptions
The `model` directory contains the actual Python code for the model. It has the following files:
- `agents.py`: Defines the `Households` agent class, each representing a household in the model. These agents have attributes related to flood depth and damage, and these factors influence their behavior. Agents calculate the expected utility of each available measure and decide whether to take action. This script is crucial for modeling the impact of flooding on individual households.
- `functions.py`: Contains utility functions for the model, including setting initial values, calculating flood damage, and processing geographical data. These functions are essential for data handling and mathematical calculations within the model. It also includes the expected utility function, which is utilized to represent households' adaptation behaviors.
- `model.py`: The central script that sets up and runs the simulation. It integrates the agents and geographical data to simulate the complex interactions and adaptations of households to flooding scenarios.
- `verification.ipynb`: Jupyter notebook that is used for verification. Verification is also conducted in `analysis_extreme_value.ipynb` by doing extreme value tests.
- `model_run_experiment`, `model_run_sensitivity`, `model_run_extremevalue.ipynb`: Jupyter notebooks for running the model. 
- `analysis_experiment`,  `analysis_sensitivity`,  `analysis_extremevalue.ipynb`: Jupyter notebooks for analyzing and plotting the results.


