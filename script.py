import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from io import BytesIO
from telegram import Bot, InputFile
import asyncio
from dotenv import load_dotenv

# Function to load and preprocess data
def load_and_preprocess_data(url):
    data = pd.read_csv(url)
    data['date'] = pd.to_datetime(data['date'])
    data['year'] = data['date'].dt.year
    return data

# Function to save plots to BytesIO object
def save_plot_to_buffer(figure, filename):
    buffer = BytesIO()
    figure.savefig(buffer, format='png')
    buffer.seek(0)
    plt.show()
    plt.close()
    return buffer

# Function to plot blood donation trends for states
def plot_blood_donation_trends(data, title, xlabel, ylabel, filename, color=None):
    fig, ax = plt.subplots(figsize=(15, 8))

    if color == 'red':
        ax.plot(data['date'], data['daily'], label=title, color='red')
    else:
        unique_states = data['state'].unique()
        for state in unique_states:
            if state != 'Malaysia':
                state_data = data[data['state'] == state]
                ax.plot(state_data['date'], state_data['daily'], label=f"{state}")
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    return save_plot_to_buffer(fig, filename)

# Function to plot yearly donation trends for states
def plot_yearly_donor_retention_trends(data, title, xlabel, ylabel, filename):
    unique_states = data.index.get_level_values('state').unique().difference(['Malaysia'])
    fig, ax = plt.subplots(figsize=(15, 8))

    for state in unique_states:
        state_data = data.loc[state]
        ax.plot(state_data.index.get_level_values('date'), state_data['percentage_regular'], marker='o', linestyle='-', label=state)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    return save_plot_to_buffer(fig, filename)

# Function to plot quarterly donation trends in Malaysia
def plot_quarterly_donation_trends(data, title, xlabel, ylabel, filename, color='red'):
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.plot(data.index, data['percentage_regular'], marker='o', linestyle='-', label='Malaysia', color=color)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    plt.tight_layout()
    return save_plot_to_buffer(fig, filename)

# Function to plot blood donor retention rate by age group in Malaysia (yearly)
def plot_retention_rate_heatmap(data, title, xlabel, ylabel, filename):
    plt.figure(figsize=(12, 8))
    sns.heatmap(data, cmap='YlGnBu', annot=True, fmt=".2%", cbar_kws={'label': 'Retention Rate'})
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    return save_plot_to_buffer(plt, filename)

# Function to send plots to Telegram group
async def send_plots_to_telegram(img_buffers, chat_id, token):
    bot = Bot(token=token)

    try:
        for i, img_buffer in enumerate(img_buffers, start=1):
            print(f'Sending plot {i} to Telegram...')
            await bot.send_photo(chat_id=chat_id, photo=InputFile(img_buffer[0], filename=img_buffer[1]))
    except Exception as e:
        print(f"Error: {e}")

# Load and preprocess data
donations_facility_data = load_and_preprocess_data("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_facility.csv")
donations_state_data = load_and_preprocess_data("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_state.csv")
newdonors_state_data = load_and_preprocess_data("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/newdonors_state.csv")

## Question 1 - How are blood donations in Malaysia / states trending?
# Resample data to monthly frequency and sum the values for each year and state
monthly_donations = donations_state_data.groupby(['state', pd.Grouper(key='date', freq='M')])['daily'].sum().reset_index()
img_buffer_1 = plot_blood_donation_trends(monthly_donations, 'Monthly Blood Donations Trend For States in Malaysia', 'Date', 'Monthly Donations', 'blood_donations_trend_1.png')

# Extract data specific to Malaysia
malaysia_monthly_data = monthly_donations[monthly_donations['state'] == 'Malaysia']
img_buffer_2 = plot_blood_donation_trends(malaysia_monthly_data, 'Monthly Blood Donations Trend in Malaysia', 'Date', 'Monthly Donations', 'blood_donations_trend_2.png', color='red')

# Plot yearly donor retention for states
df_yearly = donations_state_data.groupby(['state', pd.Grouper(key='date', freq='Y')]).sum()
df_yearly['total_donations'] = df_yearly['donations_regular'] + df_yearly['donations_irregular']
df_yearly['percentage_regular'] = (df_yearly['donations_regular'] / df_yearly['total_donations']) * 100
img_buffer_3 = plot_yearly_donor_retention_trends(df_yearly, 'Yearly Blood Donor Retention Trends for States in Malaysia', 'Year', 'Percentage', 'blood_donations_trend_3.png')

## Question 2 - How well is Malaysia retaining blood donors? (meaning, are people with a history of blood donation coming back to donate regularly)
# Plot quarterly donor retention in Malaysia
malaysia_data = donations_state_data[donations_state_data['state'] == 'Malaysia']
df_quarterly_malaysia = malaysia_data.groupby(pd.Grouper(key='date', freq='M')).sum()
df_quarterly_malaysia['total_donations'] = df_quarterly_malaysia['donations_regular'] + df_quarterly_malaysia['donations_irregular']
df_quarterly_malaysia['percentage_regular'] = (df_quarterly_malaysia['donations_regular'] / df_quarterly_malaysia['total_donations']) * 100
img_buffer_4 = plot_quarterly_donation_trends(df_quarterly_malaysia, 'Quarterly Blood Donor Trends in Malaysia', 'Quarter', 'Percentage', 'blood_donations_trend_4.png', color='red')

# Plot blood donor retention rate by age group in Malaysia (yearly)
merged_data = pd.merge(donations_state_data, newdonors_state_data, on=['date', 'state'])
merged_data['date'] = pd.to_datetime(merged_data['date'])
merged_data['year'] = merged_data['date'].dt.year

age_columns = [col for col in merged_data.columns if col.isdigit() or ('-' in col and all(part.isdigit() for part in col.split('-')))]
age_columns.append('donations_regular')

# Group by year and sum the relevant columns
yearly_data = merged_data.groupby('year')[['date'] + age_columns].agg({'date': 'first', **{age: 'sum' for age in age_columns}})

filtered_data = yearly_data[age_columns].copy()
filtered_data.iloc[:, :-1] = filtered_data.iloc[:, :-1].replace(0, np.nan)
retention_rate = filtered_data.iloc[:, :-1].div(filtered_data['donations_regular'], axis=0)
img_buffer_5 = plot_retention_rate_heatmap(retention_rate, 'Blood Donor Retention Rate by Age Group in Malaysia (Yearly)', 'Age Group', 'Year', 'blood_donations_trend_5.png')

# Function to send plots to Telegram group
async def send_plots_to_telegram(img_buffers, chat_id, token):
    bot = Bot(token=token)

    try:
        for i, img_buffer in enumerate(img_buffers, start=1):
            print(f'Sending plot {i} to Telegram...')
            await bot.send_photo(chat_id=chat_id, photo=InputFile(img_buffer[0], filename=img_buffer[1]))
    except Exception as e:
        print(f"Error: {e}")

# Top-level asynchronous function
async def main():
    # Load environment variables
    load_dotenv()

    # Send plots to Telegram
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_GROUP_ID')
    await send_plots_to_telegram([(img_buffer_1, 'blood_donations_trend_1.png'), 
                                  (img_buffer_2, 'blood_donations_trend_2.png'),
                                  (img_buffer_3, 'blood_donations_trend_3.png'), 
                                  (img_buffer_4, 'blood_donations_trend_4.png'),
                                  (img_buffer_5, 'blood_donations_trend_5.png')
                                  ], chat_id, token)

# Run the asynchronous event loop
if __name__ == "__main__":
    asyncio.run(main())
    

'''
To schedule a script to run daily at 9 am using cron, you need to add a crontab entry. Here are the steps:

Open the crontab file for editing using the command:
crontab -e
This will open the crontab file in the default text editor.

Check python path 
which python3

Check file path
realpath your_script.py

Add the following line to schedule the script to run at 9 am every day:
0 9 * * * /path/to/python3 /path/to/your_script.py
'''