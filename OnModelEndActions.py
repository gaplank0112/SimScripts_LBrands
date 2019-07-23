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
    write_daily_inventory_bool = model_obj.getcustomattribute('write_daily_inventory')
    if write_daily_inventory_bool is True:
        daily_inventory = model_obj.getcustomattribute('daily_inventory')
        datafile = model_obj.getcustomattribute('model_folder') + '\\' + 'Daily_Inventory.txt'
        write_data(daily_inventory, datafile, 'wb', ',')

    write_validation_bool = model_obj.getcustomattribute('write_validation')
    if write_validation_bool is True:
        validation_data = model_obj.getcustomattribute('validation_data')
        datafile = model_obj.getcustomattribute('model_folder') + '\\' + 'Validation.txt'
        write_data(validation_data, datafile, 'wb',',')

    # write anything from the script error log
    error_log = model_obj.getcustomattribute('log_error')
    datafile = model_obj.modelpath + '\\' + 'SIMERROR.TXT'
    if error_log:
        write_data(error_log,datafile, 'a', '\t')


def write_data(data_list, target_file, mode, separator):
    with open(target_file, mode) as writeFile:
        writer = csv.writer(writeFile, delimiter=separator)

        for list_element in data_list:
            writer.writerow(list_element)



