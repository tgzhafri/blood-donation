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
def load_and_preprocess_csv(url):
    data = pd.read_csv(url)
    data['date'] = pd.to_datetime(data['date'])
    data['year'] = data['date'].dt.year
    return data

# Function to save plots to BytesIO object
def save_plot_to_buffer(figure, filename):
    buffer = BytesIO()
    figure.savefig(buffer, format='png')
    buffer.seek(0)
    # plt.show()
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

# Function to plot yearly donor retention trends in Malaysia
def plot_yearly_donor_retention_trends(data, title, xlabel, ylabel, filename, color='red'):
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.plot(data.index, data.values, marker='o', linestyle='-', label='Malaysia', color=color)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    plt.tight_layout()
    return save_plot_to_buffer(fig, filename)

# Function to plot blood donor retention rate by age group in Malaysia (yearly)
def plot_retention_rate_heatmap(data, title, xlabel, ylabel, filename):
    plt.figure(figsize=(15, 8))
    sns.heatmap(data.T, cmap='YlGnBu', annot=True, fmt=".2f", cbar_kws={'label': 'Retention Rate %'})
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
donations_state_data = load_and_preprocess_csv("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_state.csv")
newdonors_state_data = load_and_preprocess_csv("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/newdonors_state.csv")
granular_data = pd.read_parquet("https://dub.sh/ds-data-granular")

## Question 1 - How are blood donations in Malaysia / states trending?
# Resample data to monthly frequency and sum the values for each year and state
monthly_donations = donations_state_data.groupby(['state', pd.Grouper(key='date', freq='M')])['daily'].sum().reset_index()
img_buffer_1 = plot_blood_donation_trends(monthly_donations, 'Monthly Blood Donations Trend For States in Malaysia', 'Date', 'Monthly Donations', 'blood_donations_trend_1.png')

# Extract data specific to Malaysia
malaysia_monthly_data = monthly_donations[monthly_donations['state'] == 'Malaysia']
img_buffer_2 = plot_blood_donation_trends(malaysia_monthly_data, 'Monthly Blood Donations Trend in Malaysia', 'Date', 'Monthly Donations', 'blood_donations_trend_2.png', color='red')

## Question 2 - How well is Malaysia retaining blood donors? (meaning, are people with a history of blood donation coming back to donate regularly)

merged_donors_data = pd.merge(donations_state_data, newdonors_state_data, on=['date', 'state'])
merged_donors_data['total_donations'] = merged_donors_data['donations_regular'] + merged_donors_data['donations_irregular']

granular_data['visit_date'] = pd.to_datetime(granular_data['visit_date'])
granular_data['date'] = pd.to_datetime(granular_data['visit_date'])
merged_donors_data['date'] = pd.to_datetime(merged_donors_data['date'])

merged_donors_data['year'] = merged_donors_data['date'].dt.year

merged_donors_data = pd.merge_asof(
    merged_donors_data.sort_values('date'),
    granular_data.sort_values('visit_date'),
    by='date',
    left_on='date',
    right_on='visit_date',
)

total_donations_per_year = merged_donors_data.groupby('year')['total_donations'].sum()
unique_donors_per_year = granular_data.groupby(granular_data['visit_date'].dt.year)['donor_id'].nunique()
retention_rate = (unique_donors_per_year / total_donations_per_year) * 100

### Plot yearly blood donor retention rate in Malaysia
img_buffer_3 = plot_yearly_donor_retention_trends(retention_rate, 'Yearly Blood Donor Retention Trends in Malaysia', 'Year', 'Percentage', 'blood_donations_retention_rate.png')

### Plot blood donor retention rate by age group in Malaysia (yearly)

# Group by year and sum the relevant columns
age_columns = [col for col in merged_donors_data.columns if col.isdigit() or ('-' in col and all(part.isdigit() for part in col.split('-')))]
age_columns.append('total_donations')

# Group by year and sum the relevant columns
yearly_data = merged_donors_data.groupby('year')[['date'] + age_columns].agg({'date': 'first', **{age: 'sum' for age in age_columns}})
filtered_data = yearly_data[age_columns].copy()
filtered_data.iloc[:, :-1] = filtered_data.iloc[:, :-1].replace(0, np.nan)

# Calculate the retention rate per year and age group
retention_rate_age_group = (filtered_data.iloc[:, :-1] / filtered_data.iloc[:, :-1].shift(axis=1)).iloc[:, 1:].fillna(0) * 100

img_buffer_4 = plot_retention_rate_heatmap(retention_rate_age_group,'Retention Rate by Age Group Over the Years', "Year", "Age Group",'blood_donors_retention_rate_age_group_heatmap.png')

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
                                  (img_buffer_3, 'blood_donor_retention_trend_3.png'), 
                                  (img_buffer_4, 'blood_donor_retention_trend_4.png'),
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