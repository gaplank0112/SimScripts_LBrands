import sys
import utilities_LBrands
import datetime
import math
import sim_server
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()

def main():
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:
            current_date = datetime.datetime.utcfromtimestamp(sim_server.Now())
            forecast_dict = site_product_obj.getcustomattribute('forecast_dict')
            date_list = forecast_dict.keys
            date_list = sorted(date_list)
            first_forecast = date_list[0]
            target_WOS = site_product_obj.getcustomattribute('target_WOS')
            wos_order_quantity = utilities_LBrands.get_forecast_values(site_obj.name, site_product_obj.product.name,
                                                                 first_forecast,target_WOS)
            wos_order_quantity = math.ceil(sum(wos_order_quantity))
            lead_time = site_product_obj.getcustomattribute('lead_time')
            target_date = first_forecast - datetime.timedelta(days=7)
            order_date = target_date - datetime.timedelta(days=lead_time)
            if order_date < current_date:
                order_date = current_date
            wos_order = sim_server.CreateOrder(site_product_obj.product.name, wos_order_quantity, site_obj.name)
            if wos_order is not None:
                debug_obj.trace(low, ' Replenishment order of %s units placed' % wos_order_quantity)
            else:
                debug_obj.trace(1, ' Replenishment order failed for %s %s at %s'
                                % (site_obj.name, site_product_obj.product.name, sim_server.NowAsString()))


