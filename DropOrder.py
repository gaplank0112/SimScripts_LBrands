""" Drop Order is an internally scheduled event. On the date the event is triggered, we get the list
of order details that was generated for this date from the Initial WOS Push script. Loop through the list
of order details and drop the order"""

import sys
import sim_server
import utilities_LBrands
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main(order_date_key):
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'Drop Order called at %s' % sim_server.NowAsString())

    # get the wos orders dictionary from the model object
    wos_orders_dict = model_obj.getcustomattribute('wos_orders_dict')

    # get the orders for just this date
    wos_orders_list = wos_orders_dict[order_date_key]

    # loop through and drop orders
    for order_details in wos_orders_list:
        site_name, product_name, order_qty = order_details
        try:
            new_order = sim_server.CreateOrder(product_name, order_qty, site_name)
            debug_obj.trace(med, ' Initial push order of %s units placed for %s, %s'
                            % (order_qty, site_name, product_name))
            new_order.ordernumber = new_order.ordernumber + ' Initial WOS push'.lstrip()
        except:
            debug_obj.trace(1, ' Initial push order failed for %s %s at %s'
                            % (site_name, product_name, sim_server.NowAsString()))
            utilities_LBrands.log_error(' Initial push order failed for %s %s at %s'
                                        % (site_name, product_name, sim_server.NowAsString()))

    debug_obj.trace(low, 'Drop Order complete')
