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


def get_target(data):
    brand = {'astra_zeneca': 0,
             'bio_n_tech_pfizer': 0,
             'janssen': 0,
             'moderna': 0}

    for row in data['vaccine_delivery_per_supplier']['values']:
        for key in brand:
            brand[key] = brand[key] + row[key]

    per_janssen = brand['janssen'] / sum(brand.values())

    support = data['vaccine_support']['last_value']['percentage_average']
    adults = 14_000_000
    last_month = 6_000_000

    total = (adults * (2 - per_janssen) * support / 100) - last_month
    return total


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

    # exponential prediction
    prediction = pd.DataFrame(columns=['date', 'value'])
    while target > (prediction['value'].sum() + current_vac):
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

        prediction.loc[day_index - current_index] = [next_day] + [day_est]
        current_day = prediction['date'].iloc[-1]

        if day_index > 500:
            break
    return prediction


def get_hugo(df, target):
    """Get current prediction and vaccination targets."""
    current_vac = df['value'].sum()
    hugo = {}
    # hugo['days_april'] = pd.date_range(start=df['date'].iloc[-1],
    #                                    end='2021-04-30')
    # hugo['vacs_april'] = [(50e5 - current_vac) /
    #                       (x := len(hugo['days_april']))] * x
    # hugo['days_may'] = pd.date_range(start='2021-05-01', end='2021-05-31')
    hugo['days_may'] = pd.date_range(start=df['date'].iloc[-1] , end='2021-05-31')
    hugo['vacs_may'] = [(100e5 - current_vac) / (x := len(hugo['days_may']))] * x
    hugo['days_june'] = pd.date_range(start='2021-06-01', end='2021-06-30')
    hugo['vacs_june'] = [(target - 110e5) / (x := len(hugo['days_june']))] * x
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
