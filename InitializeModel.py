import sys
import utilities_LBrands
import datetime
import csv
import sim_server
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()
dt = datetime.datetime
d = datetime.date
td = datetime.timedelta
t = datetime.time


def main():
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'Initialize model called at %s' % sim_server.NowAsString())

    # read the global variables file.
    global_variable_dict = get_gv()

    # read and store default service level and end state probability from global variables
    default_end_state_probability = global_variable_dict['DEFAULT ENDSTATE PROBABILITY']
    default_service_level = global_variable_dict['DEFAULT SERVICE LEVEL']
    write_daily_inventory_bool = bool(global_variable_dict['OUTPUT DAILY INVENTORY'])
    write_validation_bool = bool(global_variable_dict['OUTPUT IP VALIDATION'])

    # set custom attributes on the model object
    model_obj.setcustomattribute('daily_inventory', [])  # a container for inventory information
    model_obj.setcustomattribute('validation_data', [])
    model_obj.setcustomattribute('write_daily_inventory', write_daily_inventory_bool)
    model_obj.setcustomattribute('write_validation', write_validation_bool)
    model_obj.setcustomattribute('model_folder', get_model_folder())

    # set custom attributes on each site-product
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:
            site_product_obj.setcustomattribute('forecast_dict', {})
            lead_time = get_lead_time(site_product_obj)
            site_product_obj.setcustomattribute('lead_time',lead_time)
            site_product_obj.setcustomattribute('end_state_probability', default_end_state_probability)
            site_product_obj.setcustomattribute('service_level', default_service_level)
            site_product_obj.setcustomattribute('IP_check', True)

    # read in the forecast file and add to a dictionary on each site-product key=date, value=quantity
    datafile = global_variable_dict['FORECAST FILE']
    global_forecast_dict = import_forecast(datafile)
    apply_forecast(global_forecast_dict)

    # read in the parameters file and add custom attributes
    # read the transport time and add as a custom attribute = lead time

    debug_obj.trace(low,'Initialize Model complete')


def get_model_folder():
    input_data = model_obj.modelpath
    for i in range(2):
        a = input_data.rfind('\\')
        input_data = input_data[:a]
    return input_data


def get_lead_time(site_product_obj):
    lead_times = []
    # TODO: Find a way to get transportation time input

    # for source_obj in site_product_obj.sources:
    #     debug_obj.trace(1,"DELETE here 1 %s" % source_obj.transportationlane)
    #     # debug_obj.trace(1,"DELETE here 1 %s" % source_obj.transportationlane.name)
    #     debug_obj.trace(1,"DELETE here 1 %s" % source_obj.transportationlanename)
    #     lane_obj = source_obj.transportationlane
    #     debug_obj.trace(1,"DELETE here 2")
    #     for mode_obj in lane_obj.modes:
    #         debug_obj.trace(1,"Mode obj %s " % mode_obj.name)
    #         # lead_times.append(mode_obj.transportationtime)
    #         debug_obj.trace(1, "DELETE here 3 time %s" % mode_obj.transportationtime)
    # return sum(lead_times) / len(lead_times)  # calculated average
    return 7.0


def get_gv():
    global_variable_dict = {}
    data_global_variables = model_obj.modelpath + '\\' + 'GlobalVariable.txt'

    try:
        global_input = open(data_global_variables)
        csv_t = csv.reader(global_input, delimiter=',')
        for row in csv_t:
            global_variable_dict[row[1].upper()] = row[3]
    except IOError:
        debug_obj.trace(1, 'Error: No global variable file. Ensure one line of Global Variable table = '
                           'GV, String, @Table:GlobalVariable, 999999')
        end_run = model_obj.sites('EndModel')  # this effectively 'fails' the sim by trying to access a null object

    return global_variable_dict


def get_forecast_path(global_data):
    for a in global_data:
        for b in a:
            if 'FORECAST' in b.upper():
                data_path = a[3]
                return data_path

    debug_obj.trace(1, 'Error: No global variable with "forecast" in the name so no data path discovered. Ending sim.')
    debug_obj.trace(1, 'Error: No global variable with "forecast" in the name so no data path discovered. Ending sim.'
                    , 'SIMERROR.txt')
    end_run = model_obj.sites('EndModel')  # this effectively 'fails' the sim by trying to access a null object

    # TODO check for 'relative data path'. Look for the input file in same folder as the model.
    # return "C:\\Users\\greg.plank\\OneDrive - LLamasoft, Inc\\SCG\\Projects\\" \
    #           "201907 LBrands\\Data\\3 sample SKUs forecast.csv"

    return 0


def apply_forecast(global_forecast_dict):
    # loop through site products and apply forecasts to custom attribute
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:

            try:
                forecast_dict = global_forecast_dict[site_obj.name][site_product_obj.product.name]
            except:
                # set the inventory check boolean to False because we will skip review of this site-product
                site_product_obj.setcustomattribute('IP_check',False)
                forecast_dict = None

            if forecast_dict is not None:
                site_product_obj.setcustomattribute('forecast_dict', forecast_dict)
    return 0


def import_end_state_override():
    # TODO: import end state overrides
    return 0


def apply_end_state_override():
    # TODO: apply end state overrides
    return 0


def import_service_level_override():
    # TODO: import service level overrides
    return 0


def apply_service_level_override():
    # TODO: apply service level overrides
    return 0


def import_forecast(datafile):
    global_forecast_dict = {}
    # open the forecast file
    with open(datafile) as ForecastFile:
        csv_t = csv.reader(ForecastFile)

        # get the column numbers based on header names
        header = next(csv_t)
        site_col = header.index('skuloc')
        product_col = header.index('item_nbr')
        date_col = header.index('start_dt')
        qty_col = header.index('dfu_total_forecast_qty')

        # Get the forecast values by row. Table assumed to be in format
        for row in csv_t:
            site = row[site_col].zfill(4)  # zfill adds leading zeros
            sku = row[product_col]
            forecast_date = datetime.datetime.strptime(row[date_col], "%m/%d/%Y")
            forecast_value = float(row[qty_col])

            if site in global_forecast_dict:
                pass
            else:
                global_forecast_dict[site] = {}

            if sku in global_forecast_dict[site]:
                pass
            else:
                global_forecast_dict[site][sku] = {}

            if forecast_date in global_forecast_dict[site][sku]:
                pass
            else:
                global_forecast_dict[site][sku][forecast_date] = forecast_value

    return global_forecast_dict







