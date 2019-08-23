"""On Model End Actions executes a series of custom outputs."""

import sys
import csv
import sim_server
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main():
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'OnModelEndActions called at %s' % sim_server.NowAsString())

    # get the daily inventory data. If output set to True, write out data
    write_bool = model_obj.getcustomattribute('write_daily_inventory')
    datafile = model_obj.getcustomattribute('model_folder') + '\\' + 'Daily_Inventory.csv'
    data_field = 'daily_inventory'
    f = open(datafile, "w")
    f.truncate()
    f.close()
    if write_bool is True:
        data_list = model_obj.getcustomattribute(data_field)
        with open(datafile, 'wb') as writeFile:
            writer = csv.writer(writeFile, delimiter=',')

            for list_element in data_list:
                writer.writerow(list_element)

    write_validation_bool = model_obj.getcustomattribute('write_validation')
    if write_validation_bool is True:
        validation_data = model_obj.getcustomattribute('validation_data')
        datafile = model_obj.getcustomattribute('model_folder') + '\\' + 'Validation.csv'
        write_data(validation_data, datafile, 'wb', ',')

        validation_data = model_obj.getcustomattribute('WOS_push_data')
        datafile = model_obj.getcustomattribute('model_folder') + '\\' + 'WOS_push.csv'
        write_data(validation_data, datafile, 'wb', ',')

    # write anything from the script error log
    error_log = model_obj.getcustomattribute('log_error')
    datafile = model_obj.modelpath + '\\' + 'SIMERROR.TXT'
    if error_log:
        write_data(error_log, datafile, 'ab', '\t')

    debug_obj.trace(med, 'OnModelEndActions complete')


def write_data(data_list, target_file, mode, separator):
    with open(target_file, mode) as writeFile:
        writer = csv.writer(writeFile, delimiter=separator)

        for list_element in data_list:
            writer.writerow(list_element)
