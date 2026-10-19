# Floowandereeze & Modding ETL

[![Pylint](https://github.com/Nauder/floowandereeze-and-modding-etl-dl/actions/workflows/pylint.yml/badge.svg)](https://github.com/Nauder/floowandereeze-and-modding-etl-dl/actions/workflows/pylint.yml)
[![Black](https://github.com/Nauder/floowandereeze-and-modding-etl-dl/actions/workflows/black.yml/badge.svg)](https://github.com/Nauder/floowandereeze-and-modding-etl-dl/actions/workflows/black.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

![Python](https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=white)
![UnityPy](https://img.shields.io/badge/UnityPy-1.20-orange?logo=unity&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-latest-6554A8?logo=pandas&logoColor=white)

## Overview

This project is an **Extract, Transform, Load (ETL) pipeline** designed to extract metadata from the global version of
the Yu-Gi-Oh! Duel Links game via **reverse engineering**, transform it into a structured format, and store the results
in **Parquet files**, mainly to be used by the Floowandereeze & Modding tool.

This project **does not** extract the assets themselves (e.g. png files containing art of cards), it only gets the
references to the bundles containing the data, which can be used for modding.

## Features

- **Extracts** game metadata by reverse engineering Unity game files. The data currently extracted includes:
  - Card Arts.
  - English card names, read directly from the game's downloaded card tables.
  - Character, sleeve, and playmat display names where available in the game's text tables.
  - Sleeves.
  - Playmats.
- **Transforms** raw game data into a structured format, and cleans bad data.
- **Loads** the processed data into Parquet files for efficient storage and querying.

## Table of Contents

- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Important Files Structure](#important-files-structure)
- [Configuration](#configuration)
- [CI/CD](#cicd)
- [Validation](#validation)
- [License](#license)

## Technologies Used

- [**Python**](https://www.python.org/) for scripting and data processing
- [**UnityPy**](https://github.com/K0lb3/UnityPy) for reverse engineering Unity assets
- [**pandas**](https://pandas.pydata.org/) for data manipulation
- [**PIL**](https://pypi.org/project/pillow/) for image manipulation

## Installation

### Prerequisites

Ensure you have the following installed:

- Python 3.8+
- pip package manager
- Yu-Gi-Oh! Duel Links, with the in-game download complete

### Steps

```sh
# Clone the repository
git clone https://github.com/Nauder/floowandereeze-and-modding-etl-dl.git
cd floowandereeze-and-modding-etl-dl

# Install dependencies
pip install -r requirements.txt
```

## Usage

### ETL from Game Data

Replace the empty string in `config.json` with your game path.

Run the extraction script to pull data from Unity game files:

```sh
python .\etl\main.py
```

To run the extraction and export steps together, launch `python etl/gui_main.py` and select **Write Data**.
The export writes Parquet files inside `data/`, plus `version.txt` with the extraction date.

### Card names

The card-name step works offline and reads the Steam client's downloaded `CARD_Name`, `CARD_Indx`, and
`CARD_Prop3` tables from the configured `game_path`. It decodes YDLZ versions 1 and 2, then joins each
name's byte offset to its artwork ID from the property table. It does not use YGOPRODeck or the SQLite cache.
Names use the game's English spelling, including names for alternate artwork and game-specific cards.
The card Parquet columns remain unchanged.

Complete the in-game data download before running the ETL. Missing or incompatible tables produce an
error; artwork IDs without a name in the game tables are logged and skipped. Cards still need small,
medium, and large artwork references to be exported. Duplicate names receive ` (alt N)` suffixes.

The CLI currently runs ID extraction and name matching, writing `etl/services/temp/data.json`.
Use the GUI's **Write Data** step to export Parquet files, or enable `write_data()` in `etl/main.py`.

### Other asset names

The same **Get Asset Names** step also reads `IDS_NPC_NAME` and `IDS_ITEM` from the local game files,
plus `IDS_SKILL` when an accessory name references a skill. These MessagePack tables may scramble
both keys and values; the pipeline decodes them and resolves character names, character subnames,
and skill-name references in item labels.

`characters.parquet`, `sleeves.parquet`, and `fields.parquet` include a nullable string `name` column.
Their existing IDs and artwork references are preserved, including entries with duplicate names.
Missing labels, blank names, and unresolved references produce `null` rather than removing the asset.
Missing optional text tables produce a warning; damaged tables produce an error.

Run `pip install -r requirements.txt` to install the MessagePack dependency, then rerun **Get Asset Names**
and **Write Data** to populate the new fields. Card names and all other names still work offline.

## Important Files Structure

```txt
├── data/                 # Final Parquet files
├── etl/
│   ├── services/         # Pipeline logic
│   ├── main.py           # Main script
│   └── util.py           # Utility functions
├── config.json           # Configurable parameters
└── README.md             # This
```

The `data/` folder in the repository contains the game metadata as of it's last push, so if there was no game update
after the last push it should already be up to date.

## Configuration

Modify the values in `config.json`, the configurations are:

- **game_path** path to your Duel Links installation's account data folder, such as `LocalData/2cdc25a0`.
- **num_threads** amount of threads to use when extracting data, performance varies by hardware.
- **excluded_sleeves** sleeve assets to be ignored when building the list of sleeves. The game names sleeve materials
the same way as animated sleeve frames, so they are removed manually.

The only mandatory configuration is the **game_path**, the rest come with default values that should be appropriate for most cases.

## CI/CD

This project uses GitHub Actions for continuous integration and code quality checks:

- **Pylint**: Runs on every push and pull request to the main branch to ensure code quality and catch potential errors.
The check requires a minimum score of 9/10.
- **Black**: Runs on every push and pull request to the main branch to enforce consistent code formatting across the
project.

## Validation

Run the binary-table and offline pipeline regression tests with Python's built-in runner:

```sh
python -m unittest discover -s tests -v
black . --check --extend-exclude "etl/decode"
pylint etl --ignore-paths=etl/decode,local --disable=import-error --fail-under=9
```

## License

This project is licensed under the [GNU General Public License](LICENSE).
