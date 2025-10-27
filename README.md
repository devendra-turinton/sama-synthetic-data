# SAMA Synthetic Data Generator

This repository contains Python scripts for generating synthetic military intelligence data for the Situational Awareness Module of Army (SAMA) system.

## Overview

The SAMA system aggregates multi-source intelligence data to provide comprehensive situational awareness for border monitoring operations along the India-Pakistan and India-China borders. This data generator creates realistic synthetic data for system development and testing.

## Key Features

- Scenario-based data generation using LLM (Claude)
- Realistic military intelligence simulation
- Multi-source intelligence correlation
- Geospatially accurate data
- Classification hierarchy management
- SQL export for database import

## Requirements

- Python 3.12+
- Anthropic API key
- PostgreSQL (optional, for database import)

## Installation

1. Clone this repository
2. Install dependencies:
```
   pip install -r requirements.txt
```
3. Set up your environment variables:
```
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

## Usage

Generate data for all scenarios:
```
python main.py
```

Generate data for a specific scenario:
```
python main.py --scenario pakistan_infiltration
```

## Data Structure

The generator creates data for the following tables:

### Classification Hierarchies
- Activity classification (types, sub-types, classifications)
- Target classification (types, sub-types, classifications)
- Incident classification (types, sub-types, classifications)

### Operational Tables
- ELINT (Electronic Intelligence) data
- IMINT (Imagery Intelligence) data
- TACINT (Tactical Intelligence) data
- Enemy Activity data
- Situation Report (SITREP) data

## Output

Generated data is saved to the `data/output` directory in both JSON and SQL formats.

## License

This project is licensed under the MIT License.