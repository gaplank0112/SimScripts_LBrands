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
    model_obj.setcustomattribute('log_error',[])

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

    # read in end state probability overrides
    global_variable = 'OVERRIDE ENDSTATE PROB'
    datafile = check_global_variable(global_variable_dict, global_variable)
    datafile = check_relative_path(datafile)
    if datafile != 0:
        if check_datafile(datafile,'r','OVERRIDE ENDSTATE PROB') is True:
            end_state_override = import_end_state_override(global_variable,datafile)
            apply_end_state_override(end_state_override)

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
    # this only works for locations that are not make sites. We will need something else for them
    if site_product_obj.sourcingpolicy >= 12:
        return 0.0

    lead_times = []
    for source_obj in site_product_obj.sources:
        source_name = source_obj.sourcesite.name
        destination_name = site_product_obj.site.name
        for lane_obj in model_obj.lanes:
            if lane_obj.source.name == source_name:
                if lane_obj.destination.name == destination_name:
                    if lane_obj.modes is not None:
                        for mode_obj in lane_obj.modes:
                            lead_times.append(mode_obj.transportationtime.valueinseconds)

    if len(lead_times) == 0:
        return 0.0
    else:
        return (sum(lead_times) / len(lead_times)) / 86400.0  # calculated average in days


def get_gv():
    global_variable_dict = {}
    data_global_variables = model_obj.modelpath + '\\' + 'GlobalVariable.txt'

    try:
        global_input = open(data_global_variables)
        csv_t = csv.reader(global_input, delimiter=',')
        for row in csv_t:
            global_variable_dict[row[1].upper()] = row[3]
    except IOError as e:
        debug_obj.trace(1, 'Error: No global variable file. Ensure one line of Global Variable table = '
                           'GV, String, @Table:GlobalVariable, 999999')
        utilities_LBrands.log_error('Error: No global variable file. Ensure one line of Global Variable table = '
                                    '''GV, String, @Table:GlobalVariable, 999999''')
        end_run = model_obj.sites('EndModel')  # this effectively 'fails' the sim by trying to access a null object

    return global_variable_dict


    # TODO check for 'relative data path'. Look for the input file in same folder as the model.
    # return "C:\\Users\\greg.plank\\OneDrive - LLamasoft, Inc\\SCG\\Projects\\" \
    #           "201907 LBrands\\Data\\3 sample SKUs forecast.csv"


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


def import_end_state_override(global_variable, datafile):
    global_end_state_override = {}
    # open the end state override
    with open(datafile) as EndStateOverride:
        csv_t = csv.reader(EndStateOverride)

        # set the expected column names
        column_names = ['skuloc','item_nbr','end_state_prob']

        # get the column numbers based on header names
        header = next(csv_t)
        if check_header_name(str(global_variable),header,column_names) is True:
            site_col = header.index(column_names[0])
            product_col = header.index(column_names[1])
            qty_col = header.index(column_names[2])

            # Get the end state probabilities
            for row in csv_t:
                site = row[site_col].zfill(4)  # zfill adds leading zeros
                sku = row[product_col]
                qty_col = float(row[qty_col])

                if site in global_end_state_override:
                    pass
                else:
                    global_end_state_override[site] = {}

                if sku in global_end_state_override[site]:
                    pass
                else:
                    global_end_state_override[site][sku] = qty_col

    return global_end_state_override


def apply_end_state_override(global_end_state_override):
    # loop through site products and apply end state to custom attribute if there is an override
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:

            try:
                end_state_override = global_end_state_override[site_obj.name][site_product_obj.product.name]
            except:
                end_state_override = None

            if end_state_override is not None:
                site_product_obj.setcustomattribute('end_state_probability', end_state_override)
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

        # Get the forecast values by row.
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


def check_global_variable(dict, variable_name):
    if variable_name in dict.keys():
        return dict[variable_name]
    else:
        debug_obj.trace(1,'Warning: Did not find reference to variable named %s in '
                          'Global Variables name list. Skipping application of this variable.' % variable_name)
        utilities_LBrands.log_error('Warning: Did not find reference to variable named %s in Global '
                                    'Variables name list. Skipping application of this variable.' % variable_name)
        return 0


def check_datafile(filepath, mode, variable_name):
    ''' Check if a file exists and is accessible. '''
    try:
        f = open(filepath, mode)
        f.close()
    except IOError as e:
        debug_obj.trace(1, 'Warning: Could not find the file path %s reference in global variable %s. Skipping'
                           'application of this variable.' % (filepath, variable_name))
        utilities_LBrands.log_error('Warning: Could not find the file path %s reference in global variable %s. Skipping'
                                    'application of this variable.' % (filepath, variable_name))
        return False

    return True


def check_relative_path(datafile):
    if '..\\' in datafile:  # the user entered a relative path starting from the model location:
        datafile = str.replace(datafile,'..','')
        return model_obj.getcustomattribute('model_folder') + datafile
    else:
        return datafile


def check_header_name(file_name, header, values):
    for i in values:
        if i not in header:
            debug_obj.trace(1,'Warning: Could not find the header value %s in external file %s. Skipping '
                              'application of this data.' % (i, file_name))
            utilities_LBrands.log_error('Warning: Could not find the header value %s in external file %s. Skipping '
                                        'application of this data.' % (i, file_name))
            return False

    return True








