"""Help files for vaccine data."""
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt


def get_vaccinations(data):
    """Get_all estimated vaccinations."""
    prev = 0
    vaccinations = []
    dates = []
    for row in data['vaccine_administered_total']['values']:
        current = row['estimated']
        dates.append(date.fromtimestamp(row['date_unix']))
        vaccinations.append(current - prev)
        prev = current

    df = pd.DataFrame(list(zip(dates, vaccinations)),
                      columns=['date', 'value'])
    df['date'] = df['date'].astype('datetime64[ns]')
    return df


def get_target(data, df):
    """Estimate the target for everyone who wants first jab."""
    adults = 14_000_000
    week_window = 6

    brand = {'astra_zeneca': 0,
             'bio_n_tech_pfizer': 0,
             'janssen': 0,
             'moderna': 0}

    for row in data['vaccine_delivery_per_supplier']['values']:
        for key in brand:
            brand[key] = brand[key] + row[key]

    per_janssen = brand['janssen'] / sum(brand.values())

    test_data = data['tested_overall']['values']

    had_covid = 0

    for row in test_data:
        had_covid = sum(row['infected'])

    per_covid = 0.8 * had_covid / adults

    support_rivm = data['vaccine_vaccinated_or_support']['last_value']['percentage_average']
    url = "https://data.rivm.nl/covid-19/COVID-19_gedrag.csv"

    data = pd.read_csv(url, sep=';')

    data = data[data['Wave'] == max(data['Wave'])]
    data = data[data['Region_name'] == 'Nederland']
    data = data[data['Subgroup_category'] == 'Alle']
    data = data[data['Indicator_category'] == 'Vaccinatiebereidheid']

    positive = int(data[data['Indicator'] == 'Ja']['Value'])
    negative = int(data[data['Indicator'] == 'Nee']['Value'])

    support_wouter = positive / (positive + negative)

    full_group = int(adults * (2 - per_janssen - per_covid))
    group_wouter = int(full_group * support_wouter)
    group_rivm = int(full_group * support_rivm / 100)

    last_period = int(sum(df[-15:-1]['value']) * week_window / 2)

    first_wouter = group_wouter - last_period
    first_rivm = group_rivm - last_period

    return first_wouter, first_rivm, group_wouter, group_rivm


def vaccination_prediction(df, target, type='exponential'):
    """Predict the future vaccinations, uses only simple models."""
    last_week = df['value'][-8:-1].sum()
    week_before = df['value'][-15:-8].sum()

    def weekly_growth(df):
        """Predict growth in a basic way, needs to be improved."""
        growth = last_week / week_before
        return growth

    def weekly_model(df):
        """Create a model of weekly vaccinations."""
        weekly = [0 for _ in range(7)]

        for index, value in enumerate(df['value']):
            weekly[index % 7] += value

        for x in range(7):
            weekly[x] /= df['value'].sum()

        return weekly

    current_vac = df['value'].sum()
    current_index = len(df)
    current_day = df['date'].iloc[-1]
    growth = weekly_growth(df)
    weekly = weekly_model(df)

    target_wouter, target_rivm, full_wouter, full_rivm = target

    # exponential prediction
    prediction = pd.DataFrame(columns=['date', 'value', 'region'])
    while full_wouter > (prediction['value'].sum() + current_vac):
        next_day = current_day + pd.Timedelta(days=1)
        day_index = len(prediction) + current_index
        weeks = (day_index - current_index + 1) / 7
        if type == 'exponential':
            day_est = last_week * (growth)**(weeks) * weekly[day_index % 7]
        elif type == 'linear':
            day_est = (last_week + (last_week - week_before) * weeks) *\
                      weekly[day_index % 7]
        elif type == 'no_growth':
            day_est = last_week * weekly[day_index % 7]
        else:
            raise NotImplementedError

        if target_rivm > (prediction['value'].sum() + current_vac):
            region = 'rivm'
        elif target_wouter > (prediction['value'].sum() + current_vac):
            region = 'wouter'
        elif full_rivm > (prediction['value'].sum() + current_vac):
            region = 'rivm full'
        else:
            region = 'wouter full'

        if day_index > 300:
            break

        prediction.loc[day_index - current_index] = [next_day, day_est, region]
        current_day = prediction['date'].iloc[-1]

    return prediction


def get_hugo(df, target):
    """Get current prediction and vaccination targets."""
    current_vac = df['value'].sum()
    hugo = {}
    target_wouter, target_rivm, full_wouter, full_rivm = target
    # hugo['days_may'] = pd.date_range(start=df['date'].iloc[-1],
    #                                  end='2021-05-31')
    # hugo['vacs_may'] = [(100e5 - current_vac) /
    #                     (x := len(hugo['days_may']))] * x
    hugo['days_june'] = pd.date_range(start=df['date'].iloc[-1],
                                      end='2021-07-07')
    hugo['vacs_june_rivm'] = [(target_rivm - current_vac) /
                              (x := len(hugo['days_june']))] * x
    hugo['vacs_june_wouter'] = [(target_wouter - current_vac) /
                                (x := len(hugo['days_june']))] * x

    hugo['days_last'] = pd.date_range(start='2021-07-07',
                                      end='2021-09-01')
    hugo['vacs_last_set'] = [(full_rivm - target_rivm) /
                             (x := len(hugo['days_last']))] * x

    return hugo


def get_week_planning(data):
    """Find how many vaccinations are scheduled."""
    planned = data['vaccine_administered_planned']['values'][0]
    begin_week = date.fromtimestamp(planned['date_start_unix'])
    end_week = date.fromtimestamp(planned['date_end_unix'])
    days = pd.date_range(start=begin_week, end=end_week)
    vacs_plan = [planned['doses']/len(days)] * len(days)
    return pd.DataFrame(list(zip(days, vacs_plan)),
                        columns=['date', 'value'])


def get_deliveries(data):
    """Get deliveries of vaccinations and past and future."""
    delivered = data['vaccine_delivery']['values']
    days = []
    vacs = []
    prev = 0
    for row in delivered:
        begin_delivered = date.fromtimestamp(row['date_start_unix'])
        end_delivered = date.fromtimestamp(row['date_end_unix'])
        days.extend(pd.date_range(start=begin_delivered, end=end_delivered))
        current = row['total']
        vacs.extend([(current - prev)/7] * 7)
        prev = current
    previous_deliveries = pd.DataFrame(list(zip(days, vacs)),
                                       columns=['date', 'value'])

# Estimated deliveries
    deliver_estimate = data['vaccine_delivery_estimate']['values']
    days = []
    vacs = []
    for row in deliver_estimate:
        begin_delivered = date.fromtimestamp(row['date_start_unix'])
        end_delivered = date.fromtimestamp(row['date_end_unix'])
        days.extend(pd.date_range(start=begin_delivered, end=end_delivered))
        current = row['total']
        vacs.extend([(current - prev)/7] * 7)
        prev = current
    future_deliveries = pd.DataFrame(list(zip(days, vacs)),
                                     columns=['date', 'value'])

    return previous_deliveries, future_deliveries
