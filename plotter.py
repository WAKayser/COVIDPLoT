#!/bin/python
"""
Vaccination progress  made in the netherlands.

Wouter Kayser
"""
import pandas as pd
import matplotlib.pyplot as plt
import requests
import zipfile
import json
from datetime import date

from vaccine_data import *
from patient_data import *


def download_data():
    """Get latest json file from corona dashboard."""
    try:
        url = 'https://coronadashboard.rijksoverheid.nl/json/NL.json'

        r = requests.get(url)
        return r.json()
    except:  # noqa
        url = "https://coronadashboard.rijksoverheid.nl/json/latest-data.zip"
        r = requests.get(url)
        with open('nl.zip', 'wb') as file:
            file.write(r.content)

        with zipfile.ZipFile('nl.zip', 'r') as zip_file:
            zip_file.extract('NL.json')

        with open('NL.json') as json_file:
            return json.load(json_file)


def plot_save(data, light=True):
    """Plot all the data."""
    if light:
        pass
    else:
        plt.style.use('dark_background')

    fig = plt.figure(figsize=(24, 15))
    plt.subplot(311)
    df = get_vaccinations(data)
    plt.plot(df.index, df['value'], label='vaccinated')
    target = get_target(data, df)

    estimate = data['vaccine_coverage_per_age_group_estimated']['last_value']
    per_one = estimate['age_18_plus_has_one_shot']
    per_full = estimate['age_18_plus_fully_vaccinated']
    booster_per = data['booster_and_third_shot_administered']['last_value'][
        'administered_total'] / 15_200_000 * 100
    booster_per = format(booster_per, '.1f')

    support = data['vaccine_vaccinated_or_support']['last_value'][
        'percentage_average']

    same = vaccination_prediction(df, target, type='no_growth')

    current_week = get_week_planning(data)
    plt.plot(current_week['date'],
             current_week['value'],
             label='Scheduled this week',
             linewidth=3)

    steps = [['2021-01-06', 'Zorg en instellingen'], ['2021-01-26', '90+'],
             ['2021-02-12', '80+'], ['2021-02-15', '65-61 en hoog risico'],
             ['2021-03-13', '75+'], ['2021-04-06',
                                     '70+'], ['2021-04-26', '65+'],
             ['2021-05-01',
              '50+ en medische indicatie'], ['2021-05-25', '40+'],
             ['2021-06-02', '30+'], ['2021-06-10', '18+'],
             ['2021-06-23', 'Iedereen mag Janssen'],
             ['2021-07-07', '18+ eerste prik'],
             ['2021-09-01', 'Iedereen volledig'],
             ['2021-10-06', 'Booster Ernstige afweerstoornis'],
             ['2021-11-17', 'Booster 80+'], ['2021-12-01', 'Booster zorg'],
             ['2021-12-20', '1ste Booster']]

    for step in steps:
        plot_steps_gov(*step, plt, light, 200, 0.5)

    # Plotting the vaccination speed predicted by hugo de jonge
    # plt.axvline(df['date'].iloc[-1], linewidth=3)
    plt.ylabel('Vaccinations per day')
    plt.xlabel('Date')
    plt.ylim(bottom=0, top=350000)

    plt.xlim(pd.to_datetime('2021-01-01'), pd.to_datetime('2022-04-01'))
    plt.title(f'Vaccinations: 18+'
              f' one {per_one}%, full {per_full}%, booster {booster_per}%')

    plt.legend(loc='upper left')

    ax = plt.subplot(312)  # Second plot

    covid = get_covid_cases(data)
    total_covid = sum(covid['value'])
    per_covid = format(total_covid / 15_200_000 * 100, '.1f')

    covid_prediction = infection_predictor(covid, data, shift=3)

    if light:
        ax.plot(covid['date'], covid['value'], label='Infections', color='k')
        ax.plot(covid['date'][:-3],
                covid['average'][3:],
                label='Average infections',
                color='k',
                linewidth=3)
        ax.plot(covid_prediction['date'],
                covid_prediction['value'],
                'k+',
                label='Infection prediction')
    else:
        ax.plot(covid['date'], covid['value'], label='Infections', color='w')
        ax.plot(covid['date'][:-3],
                covid['average'][3:],
                label='Average infections',
                color='w',
                linewidth=3)
        ax.plot(covid_prediction['date'],
                covid_prediction['value'],
                'w+',
                label='Infection prediction')

    levels = [[6250, 'Zeer Ernstig'], [2500, 'Ernstig'], [875, 'Zorgelijk']]

    for level in levels:
        plot_danger_levels(*level, plt, light)

    steps = [['2021-01-12', 'Geen aanpassingen'],
             ['2021-01-20', 'Avondklok 9 uur'], ['2021-02-02', 'Scholen open'],
             ['2021-02-23', 'Beetje versoepelen'],
             ['2021-03-08', 'Beetje versoepelen'],
             ['2021-03-23', 'Avondklok 10 uur'],
             ['2021-04-13', 'Stappenplan gemaakt'],
             ['2021-04-28', 'Stap 1: Terrassen'],
             ['2021-05-18', 'Stap 2: Buiten locaties'],
             ['2021-06-05', 'Stap 3: Horeca 10 + binnencultuur'],
             ['2021-06-26', 'Stap 4: Minder voorwaarden + disco'],
             ['2021-07-09', 'Oeps: Stop met feesten'],
             ['2021-08-30', 'Hoger onderwijs weer open'],
             ['2021-09-25', 'Einde 1.5 meter en feest tot 12'],
             ['2021-11-06', 'Meer Mondkapjes & CoronaCheck'],
             ['2021-11-12', 'Alles dicht om 8 uur'],
             ['2021-11-28', 'Alles dicht om 5 uur'],
             ['2021-12-19', 'Lockdown'], ['2022-01-15', 'Winkels Open'],
             ['2022-01-26', 'Alles tot 10 open'],
             ['2022-02-18', 'Horeca tot 1 uur'],
             ['2022-02-25', 'Bijna geen maatregelen']]

    for step in steps:
        plot_steps_gov(*step, plt, light, factor=50)

    ggd_data = get_ggd_data()

    ax.plot(ggd_data['Date_of_statistics'],
            ggd_data['Tested_positive'],
            'r',
            label='GGD data')

    ax.set_ylim(bottom=0, top=100_000)
    ax.set_ylabel('Cases per day')
    plt.title(
        f'COVID-19 Cases and IC occupation plus stappenplan: {per_covid}%')
    plt.xlim(pd.to_datetime('2021-01-01'), pd.to_datetime('2022-04-01'))

    ax.legend(loc='upper left')

    ax = plt.subplot(313)  # IC Plot

    ICs = get_ic_cases(data)

    ax.plot(ICs['date'], ICs['value'], label='IC occupation', color='r')
    ax.plot(ICs['date'][:-3],
            ICs['average'][3:],
            label='Average IC occupation',
            color='r',
            linewidth=3)
    ic_prediction = infection_predictor(ICs, data, shift=3)
    ax.plot(ic_prediction['date'],
            ic_prediction['value'],
            'r+',
            label='IC prediction')

    plt.title(f'COVID-19 IC occupation')
    plt.xlim(pd.to_datetime('2021-01-01'), pd.to_datetime('2022-04-01'))

    ax.set_ylabel('IC occupation per day', color='r')
    ax.set_ylim(0, 1000)
    ax.set_xlabel('Date')
    ax.tick_params(axis='y', colors='red')

    ic_cap = data['intensive_care_lcps']['last_value']

    ax.axhline(1073 - ic_cap['beds_occupied_non_covid'] - 188,
               color='r',
               linestyle='--',
               label='ICs for COVID w/ BOSS')

    ax.axhline(1073 - ic_cap['beds_occupied_non_covid'],
               color='r',
               linestyle='--',
               linewidth=2,
               label='ICs for COVID w/o BOSS')

    ax.legend(loc='upper left')

    plt.tight_layout()
    if light:
        plt.savefig('results_light.svg')
    else:
        plt.savefig('results_dark.svg')


data = download_data()
plot_save(data, light=True)
plot_save(data, light=False)
