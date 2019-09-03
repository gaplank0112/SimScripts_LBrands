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
    write_data(data_field, datafile, write_bool, 'wb', ',')

    write_bool = model_obj.getcustomattribute('write_validation')
    datafile = model_obj.getcustomattribute('model_folder') + '\\' + 'Validation.csv'
    data_field = 'validation_data'
    write_data(data_field, datafile, write_bool, 'wb', ',')

    write_bool = model_obj.getcustomattribute('write_validation')
    datafile = model_obj.getcustomattribute('model_folder') + '\\' + 'WOS_push.csv'
    data_field = 'WOS_push_data'
    write_data(data_field, datafile, write_bool, 'wb', ',')

    # write anything from the script error log
    write_bool = True
    datafile = model_obj.modelpath + '\\' + 'SIMERROR.TXT'
    data_field = 'log_error'
    write_data(data_field, datafile, write_bool, 'ab', '\t')

    debug_obj.trace(low, 'OnModelEndActions complete')


def write_data(data_field, datafile, write_bool, mode, separator):
    f = open(datafile, "w")
    f.truncate()
    f.close()
    if write_bool is True:
        data_list = model_obj.getcustomattribute(data_field)
        with open(datafile, mode) as writeFile:
            writer = csv.writer(writeFile, delimiter=separator)

            for list_element in data_list:
                writer.writerow(list_element)


