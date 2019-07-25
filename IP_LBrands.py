""" IP_LBrands is an inventory policy script. It incorporates a safety stock calculation to determine the
reorder point and a lead time forecast calculation to determine reorder up to. Inventory position is calculated
from on hand - current order qty (if any) + due-in(total, not limited by lead time - due-out(total, not limited
 by lead time) - forecasted demand over lead time. In addition, the remaining forecast is summed and compared
 against an end state probabiltiy value to determine if orders will be generated regardless of inventory position."""

import sys
import datetime
import math
import sim_server
import utilities_LBrands
sys.path.append("C:\\Python26\\SCG_64\\Lib")


low, med, high = 2, 5, 9
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
        debug_obj.trace(med, 'This site product %s-%s has no forecast. Skipping review'
                        % (site_product_obj.site.name, site_product_obj.product.name))
        return None

    # record the site, product, datetime, on hand inventory for daily output
    if model_obj.getcustomattribute('write_daily_inventory') is True:
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
    end_state_probability = float(site_product_obj.getcustomattribute('end_state_probability'))

    lt_demand_values = utilities_LBrands.get_forecast_values(site_name, product_name, current_date_dt, lead_time)
    lt_forecast_demand_sum = sum(lt_demand_values)

    offset_start = current_date_dt + datetime.timedelta(days=forecast_offset)
    lt_forecast_values = utilities_LBrands.get_forecast_values(site_name, product_name, offset_start, lead_time)
    lt_forecast_sum = sum(lt_forecast_values)
    lt_forecast_mean = utilities_LBrands.list_mean(lt_forecast_values)
    lt_forecast_stddev = utilities_LBrands.list_stddev(lt_forecast_values)

    rem_forecast_values = utilities_LBrands.get_forecast_values(site_name, product_name, current_date_dt, 9999.0)
    rem_forecast_sum = sum(rem_forecast_values)
    rem_forecast_mean = utilities_LBrands.list_mean(rem_forecast_values)
    rem_forecast_stddev = utilities_LBrands.list_stddev(rem_forecast_values)

    # compute the reorder point using standard safety stock formula. Round answer to nearest integer
    service_level = float(site_product_obj.getcustomattribute('service_level'))
    z = utilities_LBrands.z_score_lookup(service_level)
    ss_raw = z * math.sqrt((lead_time_mean * rem_forecast_stddev**2) + (rem_forecast_mean * lead_time_stddev)**2)
    reorder_point = round(ss_raw)

    # compute the order up to level (max) as sum of forecasted demand during lead time. Round answer to ceiling integer
    order_up_to = math.ceil(lt_forecast_sum)

    # calculate future inventory position. Inputs: on hand, due-in, due-out, current date, forecast over lead time
    inventory_position_raw = on_hand - order_quantity + due_in - due_out - lt_forecast_demand_sum
    inventory_position = round(inventory_position_raw)

    # replenish decision: if inventory position <= min (calc'ed reorder point) AND
    #    total remaining forecast > end state probability then
    #    trigger replenishment
    # if replenishment triggered, calc replenishment order: max - inventory position
    replenish_order = False
    if inventory_position <= reorder_point:
        if rem_forecast_sum > end_state_probability:
            replenish_order = True

    replenishment_quantity = None
    if replenish_order is True:
        replenishment_quantity = float(reorder_point - inventory_position)
        replenishment_quantity = math.ceil(replenishment_quantity)
        if replenishment_quantity > 0.0:
            debug_obj.trace(med, '  Need replenishment: %s units of %s for %s'
                            % (replenishment_quantity, product_name, site_name))
            try:
                sim_server.CreateOrder(product_name, replenishment_quantity, site_name)
                debug_obj.trace(med, ' Replenishment order of %s units placed' % replenishment_quantity)
            except:
                debug_obj.trace(1, ' Replenishment order failed for %s units %s %s at %s'
                                % (replenishment_quantity, site_obj.name, product_obj.name, sim_server.NowAsString()))
                utilities_LBrands.log_error('Replenishment order failed for %s units %s %s at %s'
                                            % (replenishment_quantity, site_obj.name, product_obj.name,
                                               sim_server.NowAsString()))
    else:
        debug_obj.trace(med, ' No replenishment required at this time')

    # if we are writing validation data, record it here
    write_validation_bool = model_obj.getcustomattribute('write_validation')
    if write_validation_bool is True:
        validation_data_list = [sim_server.NowAsString(), site_name, product_name, on_hand, due_in, due_out,
                                lt_forecast_demand_sum, inventory_position_raw, inventory_position, lead_time,
                                lead_time_mean, lead_time_stddev, rem_forecast_mean, rem_forecast_stddev,
                                service_level, z, ss_raw, reorder_point, lt_forecast_sum, order_up_to,
                                rem_forecast_sum, end_state_probability, replenish_order, replenishment_quantity]
        record_validation(validation_data_list)


def record_on_hand_inventory(site_product_obj):
    daily_inventory = model_obj.getcustomattribute('daily_inventory')
    if not daily_inventory:
        daily_inventory.append(['date_time', 'skuloc', 'item_nbr', 'on_hand'])
    daily_inventory.append([sim_server.NowAsString(), site_product_obj.site.name, site_product_obj.product.name,
                            site_product_obj.inventory])
    model_obj.setcustomattribute('daily_inventory', daily_inventory)


def record_validation(data_list):
    validation_data = model_obj.getcustomattribute('validation_data')
    if not validation_data:
        validation_data.append(['date_time', 'skuloc', 'item_nbr', 'on_hand', ' due_in', ' due_out',
                                'lt_forecast_demand_sum', 'inventory position raw' 'inventory_position', 'lead_time',
                                'lead_time_mean', 'lead_time_stddev', 'rem_forecast_mean', 'rem_forecast_stddev',
                                'service_level', 'z', 'ss_raw', 'reorder_point', 'lt_forecast_sum', 'order_up_to',
                                'rem_forecast_sum', 'end_state_probability', ' replenish_order',
                                'replenishment_quantity'])
    validation_data.append(data_list)
    model_obj.setcustomattribute('validation_data', validation_data)


# ----------------------- Example s,S script ------------------------


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
        debug_obj.trace(low, ' No replenishment required at this time')
