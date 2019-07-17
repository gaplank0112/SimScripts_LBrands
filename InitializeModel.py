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
    global_data = get_gv()

    # set custom attributes on the model object
    model_obj.setcustomattribute('daily_inventory', [])  # a container for inventory information
    model_obj.setcustomattribute('validation_data', [])
    model_obj.setcustomattribute('write_daily_inventory', True)

    # set custom attributes on each site-product
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:
            site_product_obj.setcustomattribute('forecast_dict', {})

    # read in the forecast file and add to a dictionary on each site-product key=date, value=quantity
    datafile = get_forecast_path(global_data)
    global_forecast_dict = import_forecast(datafile)
    apply_forecast(global_forecast_dict)

    # read in the parameters file and add custom attributes
    # read the transport time and add as a custom attribute = lead time


def get_gv():
    data_global_variables = model_obj.modelpath + '\\' + 'GlobalVariable.txt'
    try:
        global_input = open(data_global_variables)
        csv_t = csv.reader(global_input, delimiter=',')
        global_data = []
        for row in csv_t:
            global_data.append(row)
    except IOError:
        debug_obj.trace(1, 'Error: No global variable file. Ensure one line of Global Variable table = '
                           'GV, String, @Table:GlobalVariable, 999999')
        debug_obj.trace(1, 'Error: No global variable file. Ensure one line of Global Variable table = '
                           'GV, String, @Table:GlobalVariable, 999999', 'SIMERROR.txt')
        end_run = model_obj.sites('EndModel')  # this effectively 'fails' the sim by trying to access a null object
    return global_data


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
                debug_obj.trace(1,'Warning: No forecast for site %s product %s'
                                % (site_obj.name, site_product_obj.product.name))
                debug_obj.trace(1,'Warning: No forecast for site %s product %s'
                                % (site_obj.name, site_product_obj.product.name), 'SIMERROR.txt')
                forecast_dict = None

            if forecast_dict is not None:
                site_product_obj.setcustomattribute('forecast_dict', forecast_dict)
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
        debug_obj.trace(1, 'DELETE col idx %s, %s, %s, %s' % (site_col, product_col, date_col, qty_col))

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


''' Scratch bits
    datafile = "C:\\Users\\greg.plank\\OneDrive - LLamasoft, Inc\\SCG\\Projects\\201907 LBrands\\Models\\" \
    "ExampleModel\\simulated engineered jun 19_v1 (Converted)_NetSimData\\FacilityHistoricalForecast.txt"
    forecast_dict = utilities_LBrands.import_forecast(datafile)
    
    start_date = dt(2018, 10, 1, 0, 0)
    end_date = dt(2018, 11, 15, 0, 0)
    forecast_window = 30
    site = '0005'
    product = '23974525'
    
    print utilities_LBrands.forecast_sum(site,product,start_date,forecast_window,forecast_dict)
    '''





