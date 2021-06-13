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


def plot_save(data, light=True):
    """Plot all the data."""
    if light:
        pass
    else:
        plt.style.use('dark_background')

    fig = plt.figure(figsize=(16, 10))
    plt.subplot(211)
    df = get_vaccinations(data)
    plt.plot(df['date'], df['value'], label='vaccinated')

    # exponential = vaccination_prediction(df, type='exponential')
    # plt.plot(exponential['date'], exponential['value'],
    #          label='Extrapolate exponential')

    target = get_target(data, df)

    linear = vaccination_prediction(df, target, type='linear')
    plt.plot(linear[linear['region'] == 'rivm']['date'],
             linear[linear['region'] == 'rivm']['value'],
             label='Extrapolate linear RIVM')
    plt.plot(linear[linear['region'] == 'wouter']['date'],
             linear[linear['region'] == 'wouter']['value'],
             label='Extrapolate linear wouter')

    plt.plot(linear[linear['region'] == 'rivm full']['date'],
             linear[linear['region'] == 'rivm full']['value'],
             label='Extrapolate linear RIVM full')
    plt.plot(linear[linear['region'] == 'wouter full']['date'],
             linear[linear['region'] == 'wouter full']['value'],
             label='Extrapolate linear wouter full')

    same = vaccination_prediction(df, target, type='no_growth')
    plt.plot(same[same['region'] == 'rivm']['date'],
             same[same['region'] == 'rivm']['value'],
             label='Extrapolate same RIVM')
    plt.plot(same[same['region'] == 'wouter']['date'],
             same[same['region'] == 'wouter']['value'],
             label='Extrapolate same wouter')

    plt.plot(same[same['region'] == 'rivm full']['date'],
             same[same['region'] == 'rivm full']['value'],
             label='Extrapolate same RIVM full')
    plt.plot(same[same['region'] == 'wouter full']['date'],
             same[same['region'] == 'wouter full']['value'],
             label='Extrapolate same wouter full')

    hugo = get_hugo(df, target)
    # plt.plot(hugo['days_april'], hugo['vacs_april'], label='April tempo')
    # plt.plot(hugo['days_may'], hugo['vacs_may'], label='May tempo')
    plt.plot(hugo['days_june'], hugo['vacs_june_rivm'],
             label='First jabs rivm')
    plt.plot(hugo['days_june'], hugo['vacs_june_wouter'],
             label='First jabs wouter')
    plt.plot(hugo['days_last'], hugo['vacs_last_set'],
             label='Last jabs tempo')

    current_week = get_week_planning(data)
    plt.plot(current_week['date'], current_week['value'],
             label='Scheduled this week', linewidth=3)

    previous_deliveries, future_deliveries = get_deliveries(data)
    plt.plot(previous_deliveries['date'], previous_deliveries['value'],
             ':', label='Vaccinations delivered', linewidth=3)
    plt.plot(future_deliveries['date'], future_deliveries['value'],
             ':', label='Vaccinations delivery estimation', linewidth=3)

    steps = [['2021-01-06', 'Zorg en instellingen'],
             ['2021-01-26', '90+'],
             ['2021-02-12', '80+'],
             ['2021-02-15', '65-61 en hoog risico'],
             ['2021-03-13', '75+'],
             ['2021-04-06', '70+'],
             ['2021-04-26', '65+'],
             ['2021-05-01', '50+ en medische indicatie'],
             ['2021-05-25', '40+'],
             ['2021-06-02', '30+'],
             ['2021-06-10', '18+'],
             ['2021-06-21', 'Iedereen mag Janssen'],
             ['2021-07-07', 'Iedereen eerste prik'],
             ['2021-09-01', 'Iedereen volledig'],
             ]

    for step in steps:
        plot_steps_gov(*step, plt, light, 200, 0.5)

    # Plotting the vaccination speed predicted by hugo de jonge
    plt.axvline(df['date'].iloc[-1], linewidth=3)
    plt.ylabel('Vaccinations per day')
    plt.xlabel('Date')
    plt.ylim(bottom=0)

    last_month = max(max(same['date']).month + 1, 9)
    last_month = '{:02d}'.format(last_month)
    x_end = pd.to_datetime(f'2021-{last_month}-01')
    plt.xlim(pd.to_datetime('2021-01-01'), x_end)
    plt.title('Vaccinations per day as predicted by past or Hugo de Jonge')
    plt.legend(loc='upper left')

    ax = plt.subplot(212)

    covid = get_covid_cases(data)
    covid_prediction = infection_predictor(covid, same['date'].iloc[-1])

    if light:
        ax.plot(covid['date'], covid['value'], label='Infections', color='k')
        ax.plot(covid['date'], covid['average'], label='Average infections',
                color='k', linewidth=3)
        ax.plot(covid_prediction['date'], covid_prediction['value'],
                'k+', label='Infection prediction')
    else:
        ax.plot(covid['date'], covid['value'], label='Infections', color='w')
        ax.plot(covid['date'], covid['average'], label='Average infections',
                color='w', linewidth=3)
        ax.plot(covid_prediction['date'], covid_prediction['value'],
                'w+', label='Infection prediction')

    levels = [[6250, 'Zeer Ernstig'],
              [2500, 'Ernstig'],
              [875, 'Zorgelijk']]

    for level in levels:
        plot_danger_levels(*level, plt, light)

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
             ['2021-04-28', 'Stap 1: terrassen'],
             ['2021-05-18', 'Stap 2: buiten locaties'],
             ['2021-06-05', 'Stap 3: Horeca 10 + binnencultuur'],
             ['2021-06-30', 'Stap 4: Minder voorwaarden + disco'],
             ['2021-09-01', 'Stap 5: Einde maatregelen']]

    for step in steps:
        plot_steps_gov(*step, plt, light)

    plt.axvline(covid['date'].iloc[-1], linewidth=3)

    ax.set_ylim(0, 10000)
    ax.set_ylabel('Cases per day')
    ax2.set_ylabel('IC occupation per day', color='r')
    ax2.set_ylim(0, 1000)
    ax2.set_xlabel('Date')
    ax2.tick_params(axis='y', colors='red')

    plt.title('COVID-19 Cases and IC occupation plus stappenplan')
    plt.xlim(pd.to_datetime('2021-01-01'), x_end)

    ic_cap = data['intensive_care_lcps']['last_value']

    ax2.axhline(1350 - ic_cap['beds_occupied_non_covid'], color='r',
                linestyle='--', label='IC capacity for COVID')

    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper right')

    plt.tight_layout()
    if light:
        plt.savefig('results_light.svg')
    else:
        plt.savefig('results_dark.svg')


data = download_data()
plot_save(data, light=True)
plot_save(data, light=False)
