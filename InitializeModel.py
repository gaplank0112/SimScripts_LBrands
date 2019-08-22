""" InitializeModel sets custom attributes on the model object and each site-product with defaults.
Then we read in external data files and apply any specific information to those custom attributes for
access later in the simulation"""

__author__ = "Greg Plank (LLamasoft)"
__copyright__ = "2019 07 24"
__credits__ = ["Srikanth Tondukulam, Tim Wolfer, Timothy Shaughnessy"]
__version__ = "1.0.0"
__status__ = "Production"

import sys
import datetime
import csv
import sim_server
import utilities_LBrands
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 5, 9
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
    default_target_wos = global_variable_dict['DEFAULT TARGET WOS']
    write_daily_inventory_bool = bool(global_variable_dict['OUTPUT DAILY INVENTORY'])
    write_validation_bool = bool(global_variable_dict['OUTPUT IP VALIDATION'])

    # set custom attributes on the model object
    model_obj.setcustomattribute('daily_inventory', [])  # a container for inventory information
    model_obj.setcustomattribute('validation_data', [])
    model_obj.setcustomattribute('write_daily_inventory', write_daily_inventory_bool)
    model_obj.setcustomattribute('write_validation', write_validation_bool)
    model_obj.setcustomattribute('model_folder', get_model_folder())
    model_obj.setcustomattribute('log_error', [])
    model_obj.setcustomattribute('z_score_table', add_z_score_table())

    # set custom attributes on each site-product
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:
            site_product_obj.setcustomattribute('forecast_dict', {})
            site_product_obj.setcustomattribute('end_state_probability', default_end_state_probability)
            site_product_obj.setcustomattribute('service_level', default_service_level)
            site_product_obj.setcustomattribute('target_WOS', default_target_wos)
            site_product_obj.setcustomattribute('IP_check', True)

    # create the lead time dictionary from transportation/mode times for lookup later
    lead_times_dict = get_dict_lead_times()

    # read in the forecast file and add to a dictionary on each site-product key=date, value=quantity
    global_forecast_dict = {}
    global_variable = 'FORECAST FILE'
    datafile = check_global_variable(global_variable_dict, global_variable)

    if datafile != 0:
        datafile = check_relative_path(datafile)
        if check_datafile(datafile, 'r', global_variable) is True:
            global_forecast_dict = import_forecast(global_variable, datafile)
    # read in end state probability overrides
    end_state_override = {}
    global_variable = 'OVERRIDE ENDSTATE PROB'
    datafile = check_global_variable(global_variable_dict, global_variable)
    if datafile != 0:
        datafile = check_relative_path(datafile)
        if check_datafile(datafile, 'r', global_variable) is True:
            end_state_override = import_end_state_override(global_variable, datafile)

    # read in service level overrides
    service_level_override = {}
    global_variable = 'OVERRIDE SERVICE LEVEL'
    datafile = check_global_variable(global_variable_dict, global_variable)
    if datafile != 0:
        datafile = check_relative_path(datafile)
        if check_datafile(datafile, 'r', global_variable) is True:
            service_level_override = import_service_level_override(global_variable, datafile)

    # read in target wos overrides
    target_wos_override = {}
    global_variable = 'OVERRIDE WOS TARGET'
    datafile = check_global_variable(global_variable_dict, global_variable)
    if datafile != 0:
        datafile = check_relative_path(datafile)
        if check_datafile(datafile, 'r', global_variable) is True:
            target_wos_override = import_wos_override(global_variable, datafile)

    # apply the custom data dictionaries
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:
            apply_site_product_data('forecast_dict', site_product_obj, global_forecast_dict)
            apply_site_product_data('end_state_probability', site_product_obj, end_state_override)
            apply_site_product_data('service_level', site_product_obj, service_level_override)
            apply_site_product_data('target_WOS', site_product_obj, target_wos_override)

            lead_time_mean, lead_time_stddev = get_lead_time(site_product_obj,lead_times_dict)
            site_product_obj.setcustomattribute('lead_time', lead_time_mean)
            site_product_obj.setcustomattribute('lead_time_stddev', lead_time_stddev)

            # add the first forecast date for access later
            first_snapshot_date, first_forecast_date = get_first_forecast(site_product_obj)
            site_product_obj.setcustomattribute('first_snapshot_date', first_snapshot_date)
            site_product_obj.setcustomattribute('first_forecast_date', first_forecast_date)

    debug_obj.trace(low, 'Initialize Model complete')


def get_model_folder():
    input_data = model_obj.modelpath
    for i in range(2):
        a = input_data.rfind('\\')
        input_data = input_data[:a]
    return input_data


def get_lead_time(site_product_obj, lead_times_dict):
    # this only works for locations that are not make sites. We will need something else for them
    if site_product_obj.sourcingpolicy >= 12:
        return 0.0, 0.0

    lead_times = []
    for source_obj in site_product_obj.sources:
        source_name = source_obj.sourcesite.name
        destination_name = site_product_obj.site.name
        try:
            for lane_name in lead_times_dict[source_name][destination_name].keys():
                if site_product_obj.product.name in lane_name:
                    lt_mean, lt_stddev = lead_times_dict[source_name][destination_name][lane_name]
                    return lt_mean, lt_stddev
            # if we didn't return something that is product specific, we have to try generic lane
            generic_lane_name = source_name + '_' + destination_name + '_'
            if lead_times_dict[source_name][destination_name][generic_lane_name] is not None:
                lt_mean, lt_stddev = lead_times_dict[source_name][destination_name][generic_lane_name]
                return lt_mean, lt_stddev
            else:
                return 0.0, 0.0
        except:
            return 0.0, 0.0

    return 0.0, 0.0


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
        utilities_LBrands.log_error('Error: No global variable file. Ensure one line of Global Variable table = '
                                    '''GV, String, @Table:GlobalVariable, 999999''')
        model_obj.sites('EndModel')  # this effectively 'fails' the sim by trying to access a null object

    return global_variable_dict


def import_forecast(global_variable, datafile):
    global_forecast_dict = {}
    # open the forecast file
    with open(datafile) as ExternalFile:
        csv_t = csv.reader(ExternalFile)
        # set the expected column names
        column_names = ['skuloc', 'item_nbr', 'start_dt', 'dfu_total_forecast_qty', 'snapshot_dt']
        # get the column numbers based on header names
        header = next(csv_t)
        if check_header_name(global_variable, header, column_names) is True:
            site_col = header.index(column_names[0])
            product_col = header.index(column_names[1])
            date_col = header.index(column_names[2])
            qty_col = header.index(column_names[3])
            snap_col = header.index(column_names[4])

            # Get the forecast values by row.
            for row in csv_t:
                debug_obj.trace(1, ' DELETE %s' % row[site_col])
                site = row[site_col].zfill(4)  # zfill adds leading zeros
                debug_obj.trace(1, ' DELETE %s' % row[product_col])
                sku = row[product_col]
                debug_obj.trace(1, ' DELETE %s' % row[snap_col])
                snapshot_dt = utilities_LBrands.get_datetime(row[snap_col])
                debug_obj.trace(1, ' DELETE %s' % row[date_col])
                forecast_date = utilities_LBrands.get_datetime(row[date_col])
                debug_obj.trace(1, ' DELETE %s' % row[qty_col])
                forecast_value = float(row[qty_col])

                if site in global_forecast_dict:
                    pass
                else:
                    global_forecast_dict[site] = {}

                if sku in global_forecast_dict[site]:
                    pass
                else:
                    global_forecast_dict[site][sku] = {}

                if snapshot_dt in global_forecast_dict[site][sku]:
                    pass
                else:
                    global_forecast_dict[site][sku][snapshot_dt] = {}

                if forecast_date in global_forecast_dict[site][sku][snapshot_dt]:
                    pass
                else:
                    global_forecast_dict[site][sku][snapshot_dt][forecast_date] = forecast_value

        else:
            debug_obj.trace(1, 'There is a problem with the headers in the forecast file. Expecting to find headers: '
                               ' skuloc, item_nbr, start_dt, dfu_total_forecast_qty, snapshot_dt')
            utilities_LBrands.log_error('Error: There is a problem with the headers in the forecast file. '
                                        'Expecting to find headers: '
                                        ' skuloc, item_nbr, start_dt, dfu_total_forecast_qty, snapshot_dt')

    return global_forecast_dict


def import_end_state_override(global_variable, datafile):
    global_end_state_override = {}
    # open the end state override
    with open(datafile) as ExternalFile:
        csv_t = csv.reader(ExternalFile)

        # set the expected column names
        column_names = ['skuloc', 'item_nbr', 'end_state_prob']

        # get the column numbers based on header names
        header = next(csv_t)
        if check_header_name(str(global_variable), header, column_names) is True:
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


def import_service_level_override(global_variable, datafile):
    global_service_level_override = {}
    # open the service level override and read in the information to the dictionary
    with open(datafile) as ExternalFile:
        csv_t = csv.reader(ExternalFile)

        # set the expected column names
        column_names = ['skuloc', 'item_nbr', 'service_level']

        # get the column numbers based on header names
        header = next(csv_t)
        if check_header_name(global_variable, header, column_names) is True:
            site_col = header.index(column_names[0])
            product_col = header.index(column_names[1])
            service_level_col = header.index(column_names[2])

            # get the service level overrides and store them in the dictionary
            for row in csv_t:
                site = row[site_col].zfill(4)  # zfill adds leading zeros
                sku = row[product_col]
                service_level_col = float(row[service_level_col])

                if site in global_service_level_override:
                    pass
                else:
                    global_service_level_override[site] = {}

                if sku in global_service_level_override[site]:
                    pass
                else:
                    global_service_level_override[site][sku] = service_level_col

        return global_service_level_override


def import_wos_override(global_variable, datafile):
    global_wos_override = {}
    # open the wos override and read in the information to the dictionary
    with open(datafile) as ExternalFile:
        csv_t = csv.reader(ExternalFile)

        # set the expected column names
        column_names = ['skuloc', 'item_nbr', 'target_wos']

        # get the column numbers based on header names
        header = next(csv_t)
        if check_header_name(global_variable, header, column_names) is True:
            site_col = header.index(column_names[0])
            product_col = header.index(column_names[1])
            wos_override = header.index(column_names[2])

            # get the wos overirdes and store them in the dictionary
            for row in csv_t:
                site = row[site_col].zfill(4)  # zfill adds leading zeros
                sku = row[product_col]
                wos_override = row[wos_override]

                if site in global_wos_override:
                    pass
                else:
                    global_wos_override[site] = {}

                if sku in global_wos_override[site]:
                    pass
                else:
                    global_wos_override[site][sku] = wos_override

    return global_wos_override


def apply_site_product_data(attribute_name, site_product_obj, input_dict):
    try:
        custom_data = input_dict[site_product_obj.site.name][site_product_obj.product.name]
        site_product_obj.setcustomattribute(attribute_name, custom_data)
    except:
        if attribute_name == 'forecast_dict':  # we can skip the inventory review if there's no forecast
            site_product_obj.setcustomattribute('IP_check', False)


def check_global_variable(data_dict, variable_name):
    if variable_name in data_dict.keys():
        if data_dict[variable_name]:         # if the variable data is populated with a path
            return data_dict[variable_name]
        else:                                # if the variable data is blank, just skip this
            return 0
    else:
        debug_obj.trace(1, 'Warning: Did not find reference to variable named %s in '
                        'Global Variables name list. Skipping application of this variable.' % variable_name)
        utilities_LBrands.log_error('Warning: Did not find reference to variable named %s in Global '
                                    'Variables name list. Skipping application of this variable.' % variable_name)
        return 0


def check_datafile(filepath, mode, variable_name):
    # Check if a file exists and is accessible.
    try:
        f = open(filepath, mode)
        f.close()
    except IOError:
        debug_obj.trace(1, 'Warning: Could not find the file path %s reference in global variable %s. Skipping '
                           'application of this variable.' % (filepath, variable_name))
        utilities_LBrands.log_error('Warning: Could not find the file path %s reference in global variable %s. Skipping'
                                    'application of this variable.' % (filepath, variable_name))
        return False

    return True


def check_relative_path(datafile):
    if '..\\' in datafile:  # the user entered a relative path starting from the model location:
        datafile = str.replace(datafile, '..', '')
        return model_obj.getcustomattribute('model_folder') + datafile
    else:
        return datafile


def check_header_name(file_name, header, values):
    for i in values:
        if i not in header:
            debug_obj.trace(1, 'Warning: Could not find the header value %s in external file %s. Skipping '
                            'application of this data.' % (i, file_name))
            utilities_LBrands.log_error('Warning: Could not find the header value %s in external file %s. Skipping '
                                        'application of this data.' % (i, file_name))
            return False

    return True


def add_z_score_table():
    z_score_table = dict()
    z_score_table[99.0] = 2.33
    z_score_table[98.0] = 2.05
    z_score_table[95.0] = 1.65
    z_score_table[90.0] = 1.28
    z_score_table[85.0] = 1.04
    z_score_table[50.0] = 0.00
    return z_score_table


def get_first_forecast(site_product_obj):
    # get the forecast dictionary for this site product. If it empty, apply the model start time
    forecast_dict = site_product_obj.getcustomattribute('forecast_dict')
    if utilities_LBrands.is_empty(forecast_dict):
        first_snapshot = model_obj.starttime
        first_date = model_obj.starttime

    # get the list of snapshot dates. use the earliest to get the first forecast list
    snapshot_list = forecast_dict.keys()
    if len(snapshot_list) == 0:
        first_snapshot = model_obj.starttime
        first_date = model_obj.starttime
    else:
        snapshot_list = sorted(snapshot_list)
        first_snapshot = snapshot_list[0]

        # get the list of dates with a forecast and then find the earliest date with a forecast
        first_forecast = forecast_dict[first_snapshot]
        date_list = first_forecast.keys()
        date_list = sorted(date_list)
        first_date = date_list[0]

    return first_snapshot, first_date


def get_dict_lead_times():
    lanes_dict = {}
    for lane_obj in model_obj.lanes:

        if lane_obj.modes is not None:
            mode_lead_times = []
            for mode_obj in lane_obj.modes:
                # sample the transport time field in case it is stochastic
                for i in [10001]:
                    mode_lead_times.append(mode_obj.transportationtime.valueinseconds)
        else:
            mode_lead_times = [0.0]

        lead_time_mean = utilities_LBrands.list_mean(mode_lead_times) / 86400.0  # time in days
        lead_time_stddev = utilities_LBrands.list_stddev(mode_lead_times) / 86400.0  # time in days

        if lane_obj.source.name in lanes_dict:
            pass
        else:
            lanes_dict[lane_obj.source.name] = {}

        if lane_obj.destination.name in lanes_dict[lane_obj.source.name]:
            pass
        else:
            lanes_dict[lane_obj.source.name][lane_obj.destination.name] = {}

        lanes_dict[lane_obj.source.name][lane_obj.destination.name][lane_obj.name] \
            = (lead_time_mean, lead_time_stddev)

    return lanes_dict
