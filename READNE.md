# Blood Donation Project

## Overview

This project analyzes blood donation data and generates visualizations to understand trends and retention rates.

## Requirements

- Python 3.x
- Install required modules by running: `pip install -r requirements.txt`

## Project Structure

- `script.py`: Main Python script for analyzing blood donation data.
- `requirements.txt`: List of required Python modules.
- `README.md`: Project overview and instructions.

## Usage

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/blood-donation-project.git
    ```

2. Navigate to the project directory:

    ```bash
    cd blood-donation-project
    ```

3. Install the required modules:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the script:

    ```bash
    python script.py
    ```

## Scheduling the Script

To schedule the script to run daily at 9 am using cron, follow these steps:

1. Open the crontab file for editing:

    ```bash
    crontab -e
    ```

2. Check the path to your Python 3 interpreter:

    ```bash
    which python3
    ```

3. Check the absolute path of your script:

    ```bash
    realpath your_script.py
    ```

4. Add the following line to schedule the script to run at 9 am every day:

    ```bash
    0 9 * * * /path/to/python3 /path/to/your_script.py
    ```
