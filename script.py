import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from io import BytesIO
from telegram import Bot, InputFile
import asyncio
from dotenv import load_dotenv
import datetime as dt

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

# Function to plot blood donor retention rate by age group in Malaysia (yearly)
def plot_retention_rate_heatmap(data, title, xlabel, ylabel, filename):
    plt.figure(figsize=(15, 8))
    sns.heatmap(data, annot=True, fmt= '.0%',cmap='YlGnBu', vmin = 0.0 , vmax = 0.4, cbar_kws={'label': 'Retention Rate %'})
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
donations_state_df = load_and_preprocess_csv("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_state.csv")
blood_donation_df = pd.read_parquet("https://dub.sh/ds-data-granular")

## Question 1 - How are blood donations in Malaysia / states trending?
# Resample data to monthly frequency and sum the values for each year and state
monthly_donations = donations_state_df.groupby(['state', pd.Grouper(key='date', freq='M')])['daily'].sum().reset_index()
img_buffer_1 = plot_blood_donation_trends(monthly_donations, 'Monthly Blood Donations Trend For States in Malaysia', 'Year', 'Monthly Donations', 'blood_donations_trend_1.png')

# Extract data specific to Malaysia
malaysia_monthly_data = monthly_donations[monthly_donations['state'] == 'Malaysia']
img_buffer_2 = plot_blood_donation_trends(malaysia_monthly_data, 'Monthly Blood Donations Trend in Malaysia', 'Year', 'Monthly Donations', 'blood_donations_trend_2.png', color='red')

## Question 2 - How well is Malaysia retaining blood donors? (meaning, are people with a history of blood donation coming back to donate regularly)

# A function that will parse the date Time based cohort
def get_year(x): return dt.datetime(x.year, 1, 1)

def get_date_int(df, column):
    year = df[column].dt.year
    month = df[column].dt.month
    day = df[column].dt.day
    return year, month, day

blood_donation_df['visit_date'] = pd.to_datetime(blood_donation_df['visit_date'])
blood_donation_df['VisitYear'] = blood_donation_df['visit_date'].apply(get_year)

grouping = blood_donation_df.groupby('donor_id')['VisitYear']

blood_donation_df['CohortYear'] = grouping.transform('min')

visit_year, _, _ = get_date_int(blood_donation_df, 'VisitYear')
cohort_year, _, _ = get_date_int(blood_donation_df, 'CohortYear')

years_diff = visit_year - cohort_year

blood_donation_df['CohortIndex'] = years_diff

grouping = blood_donation_df.groupby(['CohortYear', 'CohortIndex'])

# Counting number of unique customer Id's falling in each group of CohortMonth and CohortIndex
cohort_data = grouping['donor_id'].apply(pd.Series.nunique)
cohort_data = cohort_data.reset_index()

 # Assigning column names to the dataframe created above
cohort_counts = cohort_data.pivot(index='CohortYear',
                                 columns ='CohortIndex',
                                 values = 'donor_id')

cohort_sizes = cohort_counts.iloc[:,0]

retention = cohort_counts.divide(cohort_sizes, axis=0)

# Converting the retention rate into percentage and Rounding off.
retention.round(3)*100

retention.index = retention.index.strftime('%Y')

img_buffer_3 = plot_retention_rate_heatmap(retention, 'Yearly Blood Donor Retention Rate %', 'Cohort Year', 'Year', 'blood_donor_retention_rate.png')

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