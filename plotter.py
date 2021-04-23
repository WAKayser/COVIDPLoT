#!/bin/python
"""
Vaccination progress  made in the netherlands.

Wouter Kayser
"""
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import date
from vaccine_data import *
from patient_data import *


def download_data():
    """Get latest json file from corona dashboard."""
    url = 'https://coronadashboard.rijksoverheid.nl/json/NL.json'

    r = requests.get(url)
    return r.json()


data = download_data()
fig = plt.figure(figsize=(16, 10))
plt.subplot(211)
df = get_vaccinations(data)
plt.plot(df['date'], df['value'], label='vaccinated')

# exponential = vaccination_prediction(df, type='exponential')
# plt.plot(exponential['date'], exponential['value'],
#          label='Extrapolate exponential')

linear = vaccination_prediction(df, type='linear')
plt.plot(linear['date'], linear['value'], label='Extrapolate linear')

same = vaccination_prediction(df, type='no_growth')
plt.plot(same['date'], same['value'], label='Extrapolate same')

hugo = get_hugo(df)
# plt.plot(hugo['days_april'], hugo['vacs_april'], label='April tempo')
plt.plot(hugo['days_may'], hugo['vacs_may'], label='May tempo')
plt.plot(hugo['days_june'], hugo['vacs_june'], label='June tempo')

current_week = get_week_planning(data)
plt.plot(current_week['date'], current_week['value'],
         label='Scheduled this week', linewidth=3)

previous_deliveries, future_deliveries = get_deliveries(data)
plt.plot(previous_deliveries['date'], previous_deliveries['value'],
         ':', label='Vaccinations delivered', linewidth=3)
plt.plot(future_deliveries['date'], future_deliveries['value'],
         ':', label='Vaccinations delivery estimation', linewidth=3)

# Plotting the vaccination speed predicted by hugo de jonge
plt.axvline(df['date'].iloc[-1], linewidth=3)
plt.ylabel('Vaccinations per day')
plt.xlabel('Date')
plt.ylim(0, 250000)
plt.xlim(pd.to_datetime('2021-01-01'), same['date'].iloc[-1])
plt.title('Vaccinations per day as predicted by past or Hugo de Jonge')
plt.legend()

ax = plt.subplot(212)

covid = get_covid_cases(data)
ax.plot(covid['date'], covid['value'], label='Infections', color='k')
ax.plot(covid['date'], covid['average'], label='Average infections',
        color='k', linewidth=3)
covid_prediction = infection_predictor(covid, same['date'].iloc[-1])
ax.plot(covid_prediction['date'], covid_prediction['value'],
        'k+', label='Infection prediction')

levels = [[6250, 'Zeer Ernstig'],
          [2500, 'Ernstig'],
          [875, 'Zorgelijk']]

for level in levels:
    plot_danger_levels(*level, plt)


ax2 = ax.twinx()
ICs = get_ic_cases(data)
ax2.plot(ICs['date'], ICs['value'], label='IC occupation', color='r')
ax2.plot(ICs['date'], ICs['average'], label='Average IC occupation',
         color='r', linewidth=3)
ic_prediction = infection_predictor(ICs, same['date'].iloc[-1])
ax2.plot(ic_prediction['date'], ic_prediction['value'],
         'r+', label='IC prediction')

steps = [['2021-01-12', 'PersCo: geen aanpassingen'],
         ['2021-01-20', 'PersCo: Avondklok 9 uur'],
         ['2021-02-02', 'PersCo: Scholen open'],
         ['2021-02-23', 'PersCo: beetje versoepelen'],
         ['2021-03-08', 'PersCo: beetje versoepelen'],
         ['2021-03-23', 'PersCo: Avondklok 10 uur'],
         ['2021-04-13', 'PersCo: Stappenplan'],
         ['2021-04-28', 'stap 1: terrassen'],
         ['2021-05-11', 'stap 2: buiten locaties'],
         ['2021-05-26', 'stap 3: uit eten + binnen kunst'],
         ['2021-06-16', 'stap 4: evenementen'],
         ['2021-07-07', 'stap 5: binnen horeca']]

for step in steps:
    plot_steps_gov(*step, plt)

plt.axvline(df['date'].iloc[-1], linewidth=3)

ax.set_ylim(0, 12000)
ax.set_ylabel('Cases per day')
ax2.set_ylabel('IC occupation per day', color='r')
ax2.set_ylim(0, 1000)
ax2.set_xlabel('Date')
ax2.tick_params(axis='y', colors='red')

plt.title('COVID-19 Cases and IC occupation plus stappenplan')
plt.xlim(pd.to_datetime('2021-01-01'), same['date'].iloc[-1])

ic_cap = data['intensive_care_lcps']['last_value']['beds_occupied_non_covid']

ax2.axhline(1350 - ic_cap, color='r', linestyle='--',
            label='IC capacity for COVID')

lines, labels = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines + lines2, labels + labels2, loc=0)

plt.tight_layout()
plt.savefig('results.svg')
