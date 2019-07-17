import sys
import sim_server
sys.path.append("C:\\Python26\\SCG_64\\Lib")


low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main_LBrands(site_obj, product_obj, order_quantity):
    i = 0
    # record the site, product, datetime, on hand inventory for end model output
    # record the parameters for end model output (validation)


def main(site_obj, product_obj, order_quantity):
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'IP_LBrands called for %s %s at %s'
                    % (site_obj.name, product_obj.name, sim_server.NowAsString()))

    # get the site product object. All the data is on this object
    site_product_obj = site_obj.getsiteproduct(product_obj.name)

    # record the on hand inventory
    record_on_hand_inventory(site_product_obj)

    # change the order quantity to 0.0 if there was no order during this review
    if order_quantity is None:
        order_quantity = 0.0

    reorder_point = site_product_obj.reorderpoint
    reorder_up_to = site_product_obj.reorderupto
    on_hand_quantity = site_product_obj.inventory
    due_in_quantity = site_product_obj.currentorderquantity
    due_out_quantity = site_product_obj.backorderquantity
    inventory_position = on_hand_quantity + due_in_quantity - due_out_quantity - order_quantity

    if inventory_position <= reorder_point:
        replenishment_quantity = float(reorder_up_to - inventory_position)
        debug_obj.trace(high, '  Need replenishment: % units of %s for %s'
                        % (replenishment_quantity, product_obj.name, site_obj.name))
        new_order = sim_server.CreateOrder(product_obj.name, replenishment_quantity, site_obj.name)
        if new_order is True:
            debug_obj.trace(low, ' Replenishment order of %s units placed' % replenishment_quantity)
        else:
            debug_obj.trace(low, ' Replenishment order failed')
            # debug_obj.errorlog('Replenishment order failed for %s %s at %s'                       SCGX only
            #                    % (site_obj.name, product_obj.name, sim_server.NowAsString()))
    else:
        debug_obj.trace(low,' No replenishment required at this time')


def record_on_hand_inventory(site_product_obj):
    daily_inventory = model_obj.getcustomattribute('daily_inventory')
    daily_inventory.append([sim_server.NowAsString(), site_product_obj.site.name, site_product_obj.product.name,
                            site_product_obj.inventory])
    model_obj.setcustomattribute('daily_inventory', daily_inventory)
