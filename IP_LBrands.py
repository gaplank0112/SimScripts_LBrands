import sys
import sim_server
import utilities_LBrands
import datetime
sys.path.append("C:\\Python26\\SCG_64\\Lib")


low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main(site_obj, product_obj, order_quantity):
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'IP_LBrands called for %s %s at %s'
                    % (site_obj.name, product_obj.name, sim_server.NowAsString()))

    # get the site product object. All the data is on this object
    site_product_obj = site_obj.getsiteproduct(product_obj.name)

    # if there was no forecast loaded for this site - product, skip the review
    if site_product_obj.getcustomattribute('IP_check') is False:
        return

    # record the site, product, datetime, on hand inventory for daily output
    record_on_hand_inventory(site_product_obj)

    # record the parameters for validation output
    current_date_dt = datetime.datetime.utcfromtimestamp(sim_server.Now())
    site_name = site_product_obj.site.name
    product_name = site_product_obj.product.name
    on_hand = site_product_obj.inventory
    due_in = site_product_obj.currentorderquantity
    due_out = site_product_obj.backorderquantity
    lead_time = float(site_product_obj.getcustomattribute('lead_time'))
    forecast_offset = lead_time
    end_state_probability = site_product_obj.getcustomattribute('end_state_probability')
    forecast_dict = site_product_obj.getcustomattribute('forecast_dict')
    lead_time_forecast = sum_lead_time_forecast(site_name, product_name, current_date_dt,
                                                forecast_offset, lead_time)
    forecast_remaining = sum_remaining_forecast(site_name, product_name, current_date_dt)
    debug_obj.trace(1,'DELETE %s, %s, %s, %s, %s, %s, %s, %s, %s, %s'
                    % (sim_server.NowAsString(), site_name, product_name, on_hand, due_in, due_out, lead_time,
                       end_state_probability, lead_time_forecast, forecast_remaining))

    # compute the reorder point using standard safety stock formula. Inputs: forecast, lead time
    #   Round answer to nearest integer
    # compute the order up to level (max) as sum of forecasted demand during lead time
    #   wed ... lead time 7 day.  offset of lead of lead time / forecast over 7 days from offset
    #   Round answer to ceiling integer
    # calculate future inventory position. Inputs: on hand, due-in, due-out, current date,
    #    forecast over lead time
    # calculate the total remaining forecast quantity over the remainder of the horison. Inputs: current date, forecast
    # replenish decision: if inventory position <= min (calc'ed reorder point) AND
    #    total remaining forecast > end state probability OR max (calculated reorder up to) then
    #    trigger replenshiment
    # if replenishment triggered, calc replenishment order: max - inventory position

    #TODO: Remove this when IP policy is complete
    main_ss(site_obj,product_obj,order_quantity)


def sum_lead_time_forecast(site_name, product_name, start_date, offset, lead_time):
    offset_start = start_date + datetime.timedelta(days=offset)
    return utilities_LBrands.forecast_sum(site_name, product_name, offset_start, lead_time)


def sum_remaining_forecast(site_name, product_name, start_date):
    return utilities_LBrands.forecast_sum(site_name, product_name, start_date, 9999.0)


def main_ss(site_obj, product_obj, order_quantity):
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'IP_ss called for %s %s at %s'
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
        debug_obj.trace(1, 'DELETE  new order bool = %s' % new_order)
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

