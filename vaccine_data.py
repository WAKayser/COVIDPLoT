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
    df = df.set_index("date")
    df = df.resample("D").mean()
    df = df.fillna(value=0)
    return df


def get_target(data, df):
    """Estimate the target for everyone who wants first jab."""
    adults = 14_000_000
    week_window = 4

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
        if date.fromtimestamp(row['date_unix']).year == 2021:
            if date.fromtimestamp(row['date_unix']).month > 1:
                had_covid += row['infected']

    per_covid = 0.8 * had_covid / adults

    support_rivm = data['vaccine_vaccinated_or_support']['last_value']['percentage_average']
    # url = "https://data.rivm.nl/covid-19/COVID-19_gedrag.csv"

    # data = pd.read_csv(url, sep=';')

    # data = data[data['Wave'] == max(data['Wave'])]
    # data = data[data['Region_name'] == 'Nederland']
    # data = data[data['Subgroup_category'] == 'Alle']
    # data = data[data['Indicator_category'] == 'Vaccinatiebereidheid']

    # positive = int(data[data['Indicator'] == 'Ja']['Value'])
    # negative = int(data[data['Indicator'] == 'Nee']['Value'])

    # # support_wouter = positive / (positive + negative)
    # support_wouter = 0.943

    full_group = int(adults * (2 - per_janssen - per_covid))
    group_wouter = int(full_group * support_rivm / 100)
    group_rivm = int(full_group * support_rivm / 100)

    last_period = int(sum(df[-29:-1]['value']))

    first_wouter = group_wouter - last_period
    # first_rivm = group_rivm - last_period
    adults_full = group_wouter

    kids_full = group_wouter + (0.7 * 2 * 1_200_000)
    # full_rivm = group_rivm + (0.72 * 2 * 1_200_000)

    return first_wouter, adults_full, kids_full


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
    current_day = df.index.max()
    growth = weekly_growth(df)
    weekly = weekly_model(df)

    first_wouter, adults_full, kids_full = target

    # exponential prediction
    prediction = pd.DataFrame(columns=['date', 'value', 'region'])
    while kids_full > (prediction['value'].sum() + current_vac):
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

        if first_wouter > (prediction['value'].sum() + current_vac):
            region = 'first'
        elif adults_full > (prediction['value'].sum() + current_vac):
            region = 'adults'
        else:
            region = 'kids'

        if day_index > 300:
            break

        if day_est < 0:
            break

        prediction.loc[day_index - current_index] = [next_day, day_est, region]
        current_day = prediction['date'].iloc[-1]

    return prediction


def get_hugo(df, target):
    """Get current prediction and vaccination targets."""
    current_vac = df['value'].sum()
    hugo = {}
    first, adults, kids = target

    hugo['days_last'] = pd.date_range(start=df.index.max(),
                                      end='2021-09-01')
    hugo['vacs_last'] = [(adults - current_vac) /
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
