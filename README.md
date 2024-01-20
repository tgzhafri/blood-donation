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
    ````

## Setting Up Telegram Bot

Follow these steps to set up a Telegram bot for this project:

1. Create a Telegram bot:
   - Open Telegram and search for the "BotFather" bot.
   - Start a chat with BotFather and use the `/newbot` command to create a new bot.
   - Follow the instructions to choose a name and username for your bot. BotFather will provide you with a token for your new bot.

2. Obtain your Telegram Group ID:
   - Create a group on Telegram (or use an existing one).
   - Add your bot to the group.
   - Send any message to the group.
   - Open a web browser and go to `https://api.telegram.org/bot<YourBotToken>/getUpdates` (replace `<YourBotToken>` with your actual bot token).
   - Look for the `chat` object and find the `id` value. This is your Telegram Group ID.

3. Set up environment variables:
   - Create a `.env` file in your project directory.
   - Add the following lines to the `.env` file:
     ```
     TELEGRAM_TOKEN=your_bot_token
     TELEGRAM_GROUP_ID=your_group_id
     ```
     Replace `your_bot_token` with the token obtained from BotFather and `your_group_id` with the Telegram Group ID.

4. Run the script and send plots to Telegram:
   - Run your script (`python script.py`).
   - The script will send plots to the specified Telegram group.

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
    0 9 * * * /path/to/python3 /path/to/script.py
    ``