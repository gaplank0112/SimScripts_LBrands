import csv
import datetime


def import_forecast(datafile):
    forecast_dict = {}

    with open(datafile) as ForecastFile:
        csv_t = csv.reader(ForecastFile)

        for row in csv_t:
            site = row[1]
            sku = row[2]
            forecast_date = datetime.datetime.strptime(row[4],"%m/%d/%Y %I:%M:%S %p")
            forecast_value = float(row[5])

            if site in forecast_dict:
                pass
            else:
                forecast_dict[site] = {}

            if sku in forecast_dict[site]:
                pass
            else:
                forecast_dict[site][sku] = {}

            if forecast_date in forecast_dict[site][sku]:
                pass
            else:
                forecast_dict[site][sku][forecast_date] = forecast_value

    return forecast_dict


def forecast_sum(site, product, start_date, forecast_window, forecast_dict):
    end_date  = start_date.timedelta(days = forecast_window)
    date_keys = forecast_dict[site][product].keys()
    date_range = []
    for n in date_keys:
        if start_date < n < end_date:
            date_range.append(n)

    forecast_sum = 0.0
    for n in date_range:
        if n in forecast_dict[site][product]:
            value = forecast_dict[site][product][n]
            forecast_sum += forecast_dict[site][product][n]
        else:
            value = 'null'
        print n, value

    return forecast_sum


