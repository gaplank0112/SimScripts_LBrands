"""Inventory Report allows us to set a scheduled capture of inventory on hand data."""

import sys
import time
import sim_server
sys.path.append("C:\\Python26\\SCG_64\\Lib")
import IP_LBrands

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main():
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'Inventory report called at %s' % sim_server.NowAsString())
    start_time = time.time()
    daily_inventory = model_obj.getcustomattribute('daily_inventory')
    if not daily_inventory:
        daily_inventory.append(['date_time', 'skuloc', 'item_nbr', 'on_hand'])

    custom_IP_list = model_obj.getcustomattribute('custom_IP_list')

    for site_product_obj in custom_IP_list:
        # debug_obj.trace(1, 'DELETE %s, %s' % (site_product_obj.site.name, site_product_obj.product.name))
        IP_LBrands.main(site_product_obj.site, site_product_obj.product, 0)
        daily_inventory.append(
            [sim_server.NowAsString(), site_product_obj.site.name, site_product_obj.product.name,
             site_product_obj.inventory])

    model_obj.setcustomattribute('daily_inventory', daily_inventory)
    debug_obj.trace(low, 'Inventory report complete in %s seconds' % (time.time() - start_time))
