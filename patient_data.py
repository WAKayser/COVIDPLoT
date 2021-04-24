"""Help files for patient data."""
from datetime import date
import pandas as pd


def get_covid_cases(data):
    """Get all infections tested."""
    covid = data['tested_overall']['values']

    infection = []
    dates = []

    for row in covid:
        dates.append(date.fromtimestamp(row['date_unix']))
        infection.append(row['infected'])

    df = pd.DataFrame(list(zip(dates, infection)),
                      columns=['date', 'value'])
    df['date'] = df['date'].astype('datetime64[ns]')
    df['average'] = df['value'].rolling(window=7).mean()
    return df


def get_ic_cases(data):
    """Get all patients on the IC."""
    covid = data['intensive_care_lcps']['values']

    patient = []
    dates = []

    for row in covid:
        dates.append(date.fromtimestamp(row['date_unix']))
        patient.append(row['beds_occupied_covid'])

    df = pd.DataFrame(list(zip(dates, patient)),
                      columns=['date', 'value'])
    df['date'] = df['date'].astype('datetime64[ns]')
    df['average'] = df['value'].rolling(window=7).mean()
    return df


def infection_predictor(df, end):
    """Predict the number of patients with a to simple R like calculation."""
    weekly_change = df['average'].iloc[-1] / df['average'].iloc[-8]
    daily_change = weekly_change**(1/7)
    current_day = df['date'].iloc[-1]
    current_value = df['average'].iloc[-1]

    prediction = pd.DataFrame(columns=['date', 'value'])
    while current_day < end:
        current_day = current_day + pd.Timedelta(days=1)
        current_value *= daily_change
        prediction.loc[len(prediction)] = [current_day] + [current_value]

    return prediction


def plot_steps_gov(date, text, plt, light):
    """Help function for plotting opening steps."""
    if light:
        plt.axvline(nice_date := pd.to_datetime(date), color='tab:blue')
        plt.text(nice_date + pd.Timedelta(days=1), 50, text,
                 rotation=90, bbox={'facecolor': "white", 'linewidth': 0},
                 color='tab:blue', size='small')
    else:
        plt.axvline(nice_date := pd.to_datetime(date), color='w')
        plt.text(nice_date + pd.Timedelta(days=1), 50, text,
                 rotation=90, bbox={'facecolor': "black", 'linewidth': 0},
                 color='w', size='small')


def plot_danger_levels(value, text, plt, light):
    """Plot the danger levels of covid."""
    if light:
        plt.axhline(value, color='k')
        plt.text(pd.to_datetime('2021-01-02'), value + 150, text,
                 color='k')
    else:
        plt.axhline(value, color='w')
        plt.text(pd.to_datetime('2021-01-02'), value + 150, text,
                 color='w')
