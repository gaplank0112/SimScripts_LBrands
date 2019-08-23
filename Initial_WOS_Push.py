""" Initial WOS Push reads through the forecast files, finds the first date with any forecast value,
sums and rounds up the first WOS (weeks) of forecast and sets an event on the calendar to drop the order at
lead time + 7 day prior to the first forecast date with a value."""

import sys
import datetime
import math
import sim_server
import utilities_LBrands
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main():
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'Initial WOS push called at %s' % sim_server.NowAsString())

    # create a dictionary to hold the results by datetime. We only want to schedule one event per datetime, not
    # multiple calls on the same date.
    wos_orders_dict = dict()

    # loop through the sites and products
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:
            debug_obj.trace(med, ' Reviewing site %s product %s for WOS push'
                            % (site_product_obj.site.name, site_product_obj.product.name))

            # get the forecast dictionary for this site product. If it empty, skip and move to the next site product
            forecast_dict = site_product_obj.getcustomattribute('forecast_dict')
            empty_dict = False
            if utilities_LBrands.is_empty(forecast_dict):
                debug_obj.trace(med, ' The forecast dictionary is empty. Skipping this site-product')
                empty_dict = True
                continue

            # get the first snapshot date
            first_snapshot_date = site_product_obj.getcustomattribute('first_snapshot_date')

            # get the first forecast date determined during initialization
            first_forecast = site_product_obj.getcustomattribute('first_forecast_date')

            # get the target WOS and multiply by 7 (WOS is assumed to be in weeks).
            # sum the forecasted values from the first forecast date to first forecast date + wos days. round up.
            target_wos = float(site_product_obj.getcustomattribute('target_WOS')) * 7.0
            target_wos -= 1.0
            forecast_quantity = utilities_LBrands.get_forecast_values(site_obj.name, site_product_obj.product.name,
                                                                      first_snapshot_date, first_forecast, target_wos)
            wos_order_quantity = math.ceil(sum(forecast_quantity))

            # if the wos_order_quantity = 0.0, skip this site product
            if wos_order_quantity == 0.0:
                debug_obj.trace(med, ' The calculated WOS push quantity was 0.0 units. Skipping this site-product')
                continue

            # calculate a target date to have product arrive 7 days prior to first forecast
            # calculate when to drop the order at the source as target - lead time so the product can arrive around
            # the target date
            lead_time = float(site_product_obj.getcustomattribute('lead_time'))
            target_date = first_forecast - datetime.timedelta(days=7.0)
            order_date_raw = target_date - datetime.timedelta(days=lead_time)
            order_date = order_date_raw.replace(hour=0, minute=0, second=0, microsecond=0)

            # adjust the order date if it is less than the current date so that the order will drop immediately
            current_date = datetime.datetime.utcfromtimestamp(sim_server.Now()) + datetime.timedelta(seconds=1)
            if order_date < current_date:
                order_date = current_date

            debug_obj.trace(med, ' WOS push order scheduled. Forcast Qty %s, order quantity: %s, '
                                 'first forecast date %s, target arrival date %s, lead time %s, order drop date %s' %
                            (sum(forecast_quantity), wos_order_quantity, first_forecast, target_date,
                             lead_time, order_date))

            # collect the wos order details in the wos order dictionary
            if order_date in wos_orders_dict:
                # wos_orders_dict[order_date].append([site_product_obj,wos_order_quantity])
                wos_orders_dict[order_date].append([site_product_obj.site.name, site_product_obj.product.name,
                                                    wos_order_quantity])
            else:
                # wos_orders_dict[order_date] = [site_product_obj, wos_order_quantity]
                wos_orders_dict[order_date] = [[site_product_obj.site.name, site_product_obj.product.name,
                                               wos_order_quantity]]

            # if we are writing validation data, record it here
            write_validation_bool = model_obj.getcustomattribute('write_validation')
            if write_validation_bool is True:
                validation_data_list = [sim_server.NowAsString(), site_obj.name, site_product_obj.product.name,
                                        empty_dict, first_snapshot_date, first_forecast, target_wos, forecast_quantity,
                                        sum(forecast_quantity),
                                        wos_order_quantity, lead_time, target_date, order_date_raw, order_date]
                record_validation(validation_data_list)

    model_obj.setcustomattribute('wos_orders_dict', wos_orders_dict)

    for order_date_key in wos_orders_dict.keys():
        order_date = datetime.datetime.strftime(order_date_key, '%m/%d/%Y %H:%M:%S')
        sim_server.ScheduleCustomEvent('DropOrder', order_date, [order_date_key])

    debug_obj.trace(low, 'Initial WOS Push complete')


def record_validation(data_list):
    validation_data = model_obj.getcustomattribute('WOS_push_data')
    if not validation_data:
        validation_data.append(['date_time', 'skuloc', 'item_nbr', 'empty_dict_bool', 'first_snapshot_date',
                                'first_forecast_date', 'target_wos_days', 'forecast_values', 'forecast_quantity',
                                'wos_order_quantity',
                                'lead_time', 'target_date', 'order_date_raw', 'order_date'])
    validation_data.append(data_list)
    model_obj.setcustomattribute('WOS_push_data', validation_data)