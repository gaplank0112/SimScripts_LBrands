"""utilities_LBrands contains a collection of internal utilities that perform simple actions available for
multiple scripts."""

import sys
import datetime
import sim_server
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def list_stddev(data_list):
    st_dev = 0
    if len(data_list) <= 1:
        return 0
    mean = sum(data_list) / len(data_list)
    for el in data_list:
        st_dev += (el - mean)**2
    st_dev = (st_dev / (len(data_list))) ** .5
    return st_dev


def list_mean(data_list):
    if len(data_list) == 0:
        return 0
    return sum(data_list) / len(data_list)


def get_forecast_values(site_name, product_name, start_date, forecast_window):
    # get the site_product
    site_obj = get_site(site_name)
    site_product_obj = site_obj.getsiteproduct(product_name)

    # calculate the end date as start date + forecast window
    end_date = start_date + datetime.timedelta(days=forecast_window)

    # get the forecast_dict for the site_product
    forecast_dict = site_product_obj.getcustomattribute('forecast_dict')

    # get the list of dates in the dictionary (keys) and then collect the dates between start and end
    value_list = []
    date_keys = forecast_dict.keys()
    for n in date_keys:
        if start_date <= n <= end_date:
            value = forecast_dict[n]
            value_list.append(value)

    return value_list


def get_site(site_name):
    for site in model_obj.sites:
        if site.name == site_name:
            return site


def log_error(error_string):
    log_error_list = model_obj.getcustomattribute('log_error')
    log_error_list.append([0, 1, 1, error_string])
    model_obj.setcustomattribute('log_error', log_error_list)


def is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


def z_score_lookup(p_score):
    z_score_table = model_obj.getcustomattribute('z_score_table')
    if z_score_table[p_score]:
        return z_score_table[p_score]
    else:
        return 0.0
