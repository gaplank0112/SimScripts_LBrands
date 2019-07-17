import sys
import sim_server
import datetime
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def forecast_sum(site_name, product_name, start_date, forecast_window):
    debug_obj.trace(high, 'Sum forecast utility called at %s' % sim_server.NowAsString())
    # calculate the end date as start date + forecast window
    end_date = start_date + datetime.timedelta(days=forecast_window)

    # get the forecast_dict for the site_product
    site_obj = get_site(site_name)
    site_product_obj = site_obj.getsiteproduct(product_name)
    forecast_dict = site_product_obj.getcustomattribute('forecast_dict')

    # get the list of dates in the dictionary (keys) and then collect the dates between start and end
    date_keys = forecast_dict.keys()
    date_range = []
    for n in date_keys:
        if start_date < n < end_date:
            date_range.append(n)

    # loop collected dates in forecast dictionary and sum the values
    forecast_summed = 0.0
    for n in date_range:
        if n in forecast_dict:
            value = forecast_dict[n]
            forecast_summed += forecast_dict[n]
        else:
            value = 'null'
        debug_obj.trace(high, '  Forecast values %s %s %s %s' % (n, site_name, product_name, value))

    return forecast_summed


def get_site(site_name):
    for site in model_obj.sites:
        if site.name == site_name:
            return site

