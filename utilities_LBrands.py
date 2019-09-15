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


def get_forecast_values(site_name, product_name, snapshot_date, start_date, forecast_window):
    # get the site_product
    site_obj = get_site(site_name)
    site_product_obj = site_obj.getsiteproduct(product_name)

    # calculate the end date as start date + forecast window
    end_date = start_date + datetime.timedelta(days=forecast_window)

    # get the forecast_dict for the site_product
    forecast_dict = site_product_obj.getcustomattribute('forecast_dict')

    # find the snapshot date to match the input date (may be a range)
    snapshot_dates = forecast_dict.keys()
    snapshot_dates = sorted(snapshot_dates)
    forecast_snapshot_dt = snapshot_dates[-1] # by default, we pick the forecast from the last snapshot date

    for n in range(1,len(snapshot_dates)):
        if snapshot_dates[n-1] <= snapshot_date < snapshot_dates[n]:
            forecast_snapshot_dt = snapshot_dates[n-1]
            break

    # get the forecast values for the given snapshot date
    try:
        forecast_dict = forecast_dict[forecast_snapshot_dt]
    except:
        msg = 'No forecast found for site %s product %s snapshot date %s' % (site_name, product_name,
                                                                             forecast_snapshot_dt)
        debug_obj.trace(low, msg)
        log_error(msg)

    # get the list of dates in the dictionary (keys) and then collect the dates between start and end
    value_list = []
    date_keys = forecast_dict.keys()
    for n in date_keys:
        if start_date <= n <= end_date:
            value = forecast_dict[n]
            value_list.append(value)
    debug_obj.trace(1, '%s, %s, %s, %s, %s, %s' % (sim_server.NowAsString(), site_product_obj.site.name,
                                                   site_product_obj.product.name, start_date,
                                                   end_date, len(value_list)))
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


def get_datetime(dt):
    date_dict = model_obj.getcustomattribute('date_dict')
    if dt in date_dict:
        return date_dict[dt]

    else:
        fmts = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y"
        ]
        for fmt in fmts:
            try:
                date_dict[dt] = datetime.datetime.strptime(dt,fmt)
                model_obj.setcustomattribute('date_dict', date_dict)
                return datetime.datetime.strptime(dt,fmt)
            except ValueError:
                pass

    return datetime.datetime(1970,1,1)
