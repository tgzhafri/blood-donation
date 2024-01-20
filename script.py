import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from io import BytesIO
from telegram import Bot, InputFile
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Load aggregate and granular datasets
# aggregate data set
donations_facility = "https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_facility.csv"
donations_state = "https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_state.csv"
newdonors_facility = "https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/newdonors_facility.csv"
newdonors_state = "https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/newdonors_state.csv"

donations_facility_data = pd.read_csv(donations_facility)
donations_state_data = pd.read_csv(donations_state)
newdonors_facility_data = pd.read_csv(newdonors_facility)
newdonors_state_data = pd.read_csv(newdonors_state)

# print(donations_facility_data.head())
# print(donations_state_data.head())
# print(newdonors_facility_data.head())
# print(newdonors_state_data.head())

# Data Cleaning and Preprocessing

# Modify this line based on the actual column names in your DataFrame
donations_state_data['date'] = pd.to_datetime(donations_state_data['date'])

# Extract the year from the 'date' column
donations_state_data['year'] = donations_state_data['date'].dt.year

# Resample data to monthly frequency and sum the values for each year and state
monthly_donations = donations_state_data.groupby(['state', pd.Grouper(key='date', freq='M')])['daily'].sum().reset_index()

# Plotting aggregate blood donation trends for each state 
unique_states = monthly_donations['state'].unique()

# Plot for all states in Malaysia
fig, ax1 = plt.subplots(figsize=(15, 8))

for state in unique_states:
    if state != 'Malaysia':
        state_data = monthly_donations[monthly_donations['state'] == state]
        ax1.plot(state_data['date'], state_data['daily'], label=f"{state}")

ax1.set_title('Monthly Blood Donations Trend For States in Malaysia')
ax1.set_xlabel('Date')
ax1.set_ylabel('Monthly Donations')
ax1.legend()

# Save the plot to a BytesIO object
img_buffer_1 = BytesIO()
plt.savefig(img_buffer_1, format='png')
img_buffer_1.seek(0)
plt.close()

# Plot for Malaysia
malaysia_data = monthly_donations[monthly_donations['state'] == 'Malaysia']

fig, ax2 = plt.subplots(figsize=(15, 8))
ax2.plot(malaysia_data['date'], malaysia_data['daily'], label='Malaysia', color='red')

ax2.set_title('Monthly Blood Donations Trend in Malaysia')
ax2.set_xlabel('Date')
ax2.set_ylabel('Monthly Donations')
ax2.legend()

plt.tight_layout()
# plt.show()

# Save the plot to a BytesIO object
img_buffer_2 = BytesIO()
plt.savefig(img_buffer_2, format='png')
img_buffer_2.seek(0)
plt.close()

#####-----------------------------------------------------------
# # Question 2: How well is Malaysia retaining blood donors?

# Part 1: Yearly Donation Trends for States in Malaysia
# Convert 'date' columns to datetime type
donations_state_data['date'] = pd.to_datetime(donations_state_data['date'])
newdonors_state_data['date'] = pd.to_datetime(newdonors_state_data['date'])

# Merge the two dataframes on 'date' and 'state'
merged_data = pd.merge(donations_state_data, newdonors_state_data, on=['date', 'state'])

# Yearly Donation Trends for States in Malaysia
df_yearly = donations_state_data.groupby(['state', pd.Grouper(key='date', freq='Y')]).sum()
df_yearly['total_donations'] = df_yearly['donations_regular'] + df_yearly['donations_irregular']
df_yearly['percentage_regular'] = (df_yearly['donations_regular'] / df_yearly['total_donations']) * 100

unique_states = df_yearly.index.get_level_values('state').unique().difference(['Malaysia'])

# Plot for all states in Malaysia (excluding Malaysia)
fig, ax1 = plt.subplots(figsize=(15, 8))

for state in unique_states:
    state_data = df_yearly.loc[state]
    ax1.plot(state_data.index.get_level_values('date'), state_data['percentage_regular'], marker='o', linestyle='-', label=state)

ax1.set_title('Yearly Donation Trends for States in Malaysia (Excluding Malaysia)')
ax1.set_xlabel('Year')
ax1.set_ylabel('Percentage')
ax1.legend()

# Save the plot to a BytesIO object
img_buffer_3 = BytesIO()
plt.savefig(img_buffer_3, format='png')
img_buffer_3.seek(0)
plt.close()

# Quarterly Donation Trends in Malaysia
malaysia_data = donations_state_data[donations_state_data['state'] == 'Malaysia']
df_quarterly_malaysia = malaysia_data.groupby(pd.Grouper(key='date', freq='M')).sum()
df_quarterly_malaysia['total_donations'] = df_quarterly_malaysia['donations_regular'] + df_quarterly_malaysia['donations_irregular']
df_quarterly_malaysia['percentage_regular'] = (df_quarterly_malaysia['donations_regular'] / df_quarterly_malaysia['total_donations']) * 100

# Plot just for Malaysia
fig, ax2 = plt.subplots(figsize=(15, 8))
ax2.plot(df_quarterly_malaysia.index, df_quarterly_malaysia['percentage_regular'], marker='o', linestyle='-', label='Malaysia', color='red')

ax2.set_title('Quarterly Donation Trends in Malaysia')
ax2.set_xlabel('Quarter')
ax2.set_ylabel('Percentage')
ax2.legend()

plt.tight_layout()
# plt.show()

# Save the plot to a BytesIO object
img_buffer_4 = BytesIO()
plt.savefig(img_buffer_4, format='png')
img_buffer_4.seek(0)
plt.close()

# Part 2: Blood Donor Retention Rate by Age Group in Malaysia (Yearly)
merged_data['date'] = pd.to_datetime(merged_data['date'])
merged_data['year'] = merged_data['date'].dt.year
yearly_data = merged_data.groupby('year').agg({'date': 'first', '17-24': 'sum', '25-29': 'sum', '30-34': 'sum',
                                               '35-39': 'sum', '40-44': 'sum', '45-49': 'sum', '50-54': 'sum',
                                               '55-59': 'sum', '60-64': 'sum', 'donations_regular': 'sum'})

age_columns = ['17-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', 'donations_regular']
filtered_data = yearly_data[age_columns]

filtered_data.iloc[:, :-1] = filtered_data.iloc[:, :-1].replace(0, np.nan)

retention_rate = filtered_data.iloc[:, :-1].div(filtered_data['donations_regular'], axis=0)

plt.figure(figsize=(12, 8))
sns.heatmap(retention_rate, cmap='YlGnBu', annot=True, fmt=".2%", cbar_kws={'label': 'Retention Rate'})

plt.xlabel('Age Group')
plt.ylabel('Year')
plt.title('Blood Donor Retention Rate by Age Group in Malaysia (Yearly)')
# plt.show()

# Save the plot to a BytesIO object
img_buffer_5 = BytesIO()
plt.savefig(img_buffer_5, format='png')
img_buffer_5.seek(0)
plt.close()
    
token = os.environ.get('TELEGRAM_TOKEN')
print(token)
# chat_id = os.environ.get('TELEGRAM_GROUP')

# Define an asynchronous function to send the plots to the Telegram group
async def send_plots():
    # Create a bot instance and replace "YOUR_BOT_TOKEN" with your actual bot token
    bot = Bot(token=token)

    # Replace "YOUR_CHANNEL" with your actual channel name or ID
    chat_id = os.environ.get('TELEGRAM_GROUP_ID')

    try:
        # Send the first plot to the Telegram group
        print('Sending blood donation trend...')
        await bot.send_photo(chat_id=chat_id, photo=InputFile(img_buffer_1, filename='blood_donations_trend_1.png'))
        
        print('Sending blood donation trend...')
        await bot.send_photo(chat_id=chat_id, photo=InputFile(img_buffer_2, filename='blood_donations_trend_2.png'))

        # Send the second plot to the Telegram group
        print('Sending retaining blood donors trend...')
        await bot.send_photo(chat_id=chat_id, photo=InputFile(img_buffer_3, filename='blood_donations_trend_3.png'))
       
        # Send the second plot to the Telegram group
        print('Sending retaining blood donors trend...')
        await bot.send_photo(chat_id=chat_id, photo=InputFile(img_buffer_4, filename='blood_donations_trend_4.png'))

        # Send the second plot to the Telegram group
        print('Sending retaining (blood donors x age group) heatmap...')
        await bot.send_photo(chat_id=chat_id, photo=InputFile(img_buffer_5, filename='blood_donations_trend_5.png'))
    except Exception as e:
        print(f"Error: {e}")

# Run the asynchronous event loop
asyncio.run(send_plots())


'''
To schedule a script to run daily at 9 am using cron, you need to add a crontab entry. Here are the steps:

Open the crontab file for editing using the command:
crontab -e
This will open the crontab file in the default text editor.

Add the following line to schedule the script to run at 9 am every day:
0 9 * * * /path/to/python3 /path/to/your_script.py
'''
