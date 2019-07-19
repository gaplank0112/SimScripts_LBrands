import sys
import sim_server
import utilities_LBrands
import datetime
import math
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
    lt_values = [lead_time]  # If we want the model to calculate 'real', we will need to capture those values
    lead_time_mean = utilities_LBrands.list_mean(lt_values)
    lead_time_stddev = utilities_LBrands.list_stddev(lt_values)
    forecast_offset = lead_time
    end_state_probability = site_product_obj.getcustomattribute('end_state_probability')
    forecast_dict = site_product_obj.getcustomattribute('forecast_dict')
    lead_time_demand_values = get_lead_time_demand(site_name, product_name, current_date_dt, lead_time)
    lead_time_demand_sum = sum(lead_time_demand_values)
    lt_forecast_values = get_lead_time_forecast(site_name, product_name, current_date_dt, forecast_offset, lead_time)
    lt_forecast_sum = sum(lt_forecast_values)
    lt_forecast_mean = utilities_LBrands.list_mean(lt_forecast_values)
    lt_forecast_stddev = utilities_LBrands.list_stddev(lt_forecast_values)
    rem_forecast_values = get_remaining_forecast(site_name, product_name, current_date_dt)
    rem_forecast_sum = sum(rem_forecast_values)
    rem_forecast_mean = utilities_LBrands.list_mean(rem_forecast_values)
    rem_forecast_stddev = utilities_LBrands.list_stddev(rem_forecast_values)

    debug_obj.trace(1,'DELETE %s, %s, %s, %s, %s, %s, %s, %s'
                    % (current_date_dt, site_name, product_name, on_hand, due_in, due_out, lead_time,
                       end_state_probability))
    debug_obj.trace(1,'DELETE lead time forecast %s' % lt_forecast_values)
    debug_obj.trace(1,'DELETE %s, %s, %s'
                    % (lt_forecast_sum, lt_forecast_mean, lt_forecast_stddev))
    debug_obj.trace(1,'DELETE rem forecast %s' % rem_forecast_values)
    debug_obj.trace(1,'DELETE %s' % rem_forecast_sum)


    # compute the reorder point using standard safety stock formula. Inputs: forecast, lead time
    #   Round answer to nearest integer
    z = 1.64485  # TODO: find a way to calculate z from service level probability
    ss_raw = z * math.sqrt((lead_time_mean * rem_forecast_stddev**2) + (rem_forecast_mean * lead_time_stddev)**2)
    reorder_point = round(ss_raw)
    debug_obj.trace(1,'DELETE ss1 %s, reorder point %s' % (ss_raw, reorder_point))

    # compute the order up to level (max) as sum of forecasted demand during lead time
    #   Round answer to ceiling integer
    order_up_to = math.ceil(lt_forecast_sum)
    debug_obj.trace(1,'DELETE lt sum %s, order up to %s' % (lt_forecast_sum, order_up_to))

    # calculate future inventory position. Inputs: on hand, due-in, due-out, current date,
    #    forecast over lead time
    basic_inventory_position = on_hand + due_in - due_out
    sim_inventor_position = site_product_obj.inventoryposition
    ck = (basic_inventory_position == sim_inventor_position)
    inventory_position = on_hand + due_in - due_out - lead_time_demand_sum
    debug_obj.trace(1,'DELETE basic ip %s, sim ip %s, NoDiff: %s, Lbrands ip %s'
                    % (basic_inventory_position, sim_inventor_position, ck, inventory_position ))

    # calculate the total remaining forecast quantity over the remainder of the horizon. Inputs: current date, forecast
    remaining_gt_end_prob = rem_forecast_sum > end_state_probability
    debug_obj.trace(1,'DELETE rem sum %s, end state %s, ck %s' % (rem_forecast_sum, end_state_probability,
                                                                  remaining_gt_end_prob))

    # replenish decision: if inventory position <= min (calc'ed reorder point) AND
    #    total remaining forecast > end state probability OR max (calculated reorder up to) then
    #    trigger replenishment
    # if replenishment triggered, calc replenishment order: max - inventory position
    replenish_order = False
    ck1 = (inventory_position <= reorder_point)
    ck2 = (rem_forecast_sum > end_state_probability)
    ck3 = (rem_forecast_sum > reorder_point) # TODO delete this
    debug_obj.trace(1,'DELETE %s, %s, %s ' % (ck1, ck2, ck3))
    if inventory_position <= reorder_point:
        if rem_forecast_sum > end_state_probability:
            debug_obj.trace(1,'CREATE AN ORDER 1')
            replenish_order = True
        # elif rem_forecast_sum > order_up_to:
        #     debug_obj.trace(1,'CREATE AN ORDER 2')
        #     replenish_order = True

    if replenish_order == True:
        replenishment_quantity = float(reorder_point - inventory_position)
        replenishment_quantity = math.ceil(replenishment_quantity)
        debug_obj.trace(high, '  Need replenishment: % units of %s for %s'
                        % (replenishment_quantity, product_name, site_name))
        new_order = sim_server.CreateOrder(product_name, replenishment_quantity, site_name)
        if new_order is not None:
            debug_obj.trace(high, ' Replenishment order of %s units placed' % replenishment_quantity)
        else:
            debug_obj.trace(1, ' Replenishment order failed for %s %s at %s'
                            % (site_obj.name, product_obj.name, sim_server.NowAsString()))
            # debug_obj.errorlog('Replenishment order failed for %s %s at %s'                       SCGX only
            #                    % (site_obj.name, product_obj.name, sim_server.NowAsString()))
    else:
        debug_obj.trace(high, ' No replenishment required at this time')

    # if we are writing validation data, record it here
    write_validation_bool = model_obj.getcustomattribute('write_validation')
    if write_validation_bool is True:
        validation_data_list = [sim_server.NowAsString(),site_name, product_name, on_hand, due_in, due_out, lead_time,
                                forecast_offset, end_state_probability, lt_forecast_sum, lt_forecast_mean,
                                lt_forecast_stddev, rem_forecast_sum, ss_raw, reorder_point, order_up_to]
        record_validation(validation_data_list)


def get_lead_time_forecast(site_name, product_name, start_date, offset, lead_time):
    offset_start = start_date + datetime.timedelta(days=offset)
    return utilities_LBrands.get_forecast_values(site_name, product_name, offset_start, lead_time)


def get_remaining_forecast(site_name, product_name, start_date):
    return utilities_LBrands.get_forecast_values(site_name, product_name, start_date, 9999.0)


def get_lead_time_demand(site_name, product_name, start_date, forecast_window):
    return utilities_LBrands.get_forecast_values(site_name, product_name, start_date, forecast_window)


def main_ss(site_obj, product_obj, order_quantity):
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'IP_ss called for %s %s at %s'
                    % (site_obj.name, product_obj.name, sim_server.NowAsString()))

    # get the site product object. All the data is on this object
    site_product_obj = site_obj.getsiteproduct(product_obj.name)

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
        if new_order is not None:
            debug_obj.trace(low, ' Replenishment order of %s units placed' % replenishment_quantity)
        else:
            debug_obj.trace(1, ' Replenishment order failed for %s %s at %s'
                            % (site_obj.name, product_obj.name, sim_server.NowAsString()))
            # debug_obj.errorlog('Replenishment order failed for %s %s at %s'                       SCGX only
            #                    % (site_obj.name, product_obj.name, sim_server.NowAsString()))
    else:
        debug_obj.trace(low,' No replenishment required at this time')


def record_on_hand_inventory(site_product_obj):
    daily_inventory = model_obj.getcustomattribute('daily_inventory')
    daily_inventory.append([sim_server.NowAsString(), site_product_obj.site.name, site_product_obj.product.name,
                            site_product_obj.inventory])
    model_obj.setcustomattribute('daily_inventory', daily_inventory)


def record_validation(data_list):
    validation_data = model_obj.getcustomattribute('validation_data')
    validation_data.append(data_list)
    model_obj.setcustomattribute('validation_data', validation_data)
