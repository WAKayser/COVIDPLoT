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
    df = df.sort_values(by='date')
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
    df = df.interpolate()
    df['average'] = df['value'].rolling(window=7).mean()

    return df


def infection_predictor(df, end, data, shift=0):
    """Predict the number of patients with a to simple R like calculation."""
    new_vax = data['vaccine_administered_planned']['values'][0]
    per_vax_new = 1 - (new_vax['doses'] * 3 / 2 / 15_200_000)

    weekly_change = df['average'].iloc[-1] / df['average'].iloc[-8]
    daily_change = weekly_change**(1/7) * per_vax_new**(1/7)

    freshness = date.fromtimestamp(data['variants']['last_value']['date_end_unix'])
    variant_data = data['variants']['last_value']['delta_percentage'] / 100

    gap = date.today() - freshness
    weeks_old = (gap.days / 7) - 1

    # percentage of extra delta variant estimated by end of 3 week prediction
    now_delta = min(variant_data + 0.15 * weeks_old, 1)
    soon_delta = min(now_delta + (3 * 0.2), 1)

    raw_r = daily_change / (1.5**(1/7) * now_delta + (1-now_delta))
    delta_change = raw_r * (1.5**(1/7) * soon_delta + (1-soon_delta))

    current_day = df['date'].iloc[-(1+shift)]
    value = df['average'].iloc[-1]
    delta = df['average'].iloc[-1]

    prediction = pd.DataFrame(columns=['date', 'value', 'delta'])
    for _ in range(21):
        current_day = current_day + pd.Timedelta(days=1)
        value *= daily_change
        delta *= delta_change
        prediction.loc[len(prediction)] = [current_day, value, delta]

    return prediction


def plot_steps_gov(date, text, plt, light, factor=1, alpha=0.5):
    """Help function for plotting opening steps."""
    if light:
        plt.axvline(nice_date := pd.to_datetime(date), color='tab:blue')
        plt.text(nice_date + pd.Timedelta(days=1), 50*factor, text,
                 rotation=90,
                 bbox={'facecolor': "white",
                       'linewidth': 0,
                       'alpha': alpha},
                 color='tab:blue', size='small')
    else:
        plt.axvline(nice_date := pd.to_datetime(date), color='w')
        plt.text(nice_date + pd.Timedelta(days=1), 50*factor, text,
                 rotation=90,             
                 bbox={'facecolor': "black",
                       'linewidth': 0,
                       'alpha': alpha},
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
