import sys
import utilities_LBrands
import datetime
import csv
import sim_server
sys.path.append("C:\\Python26\\SCG_64\\Lib")

low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main():
    debug_obj.trace(low, '-'*30)
    debug_obj.trace(low, 'OnModelEndActions called at %s' % sim_server.NowAsString())

    # get the daily inventory data. If output set to True, write out data
    write_daily_inventory = model_obj.getcustomattribute('write_daily_inventory')
    if write_daily_inventory is True:
        daily_inventory = model_obj.getcustomattribute('daily_inventory')
        # TODO: write to same folder as the model location
        datafile = "C:\\Users\\greg.plank\\OneDrive - LLamasoft, Inc\\SCG\\Projects\\201907 LBrands\\Models\\" \
                   "ExampleModel\\simulated engineered jun 19_v1 (Converted)_NetSimData\\Daily_Inventory.txt"
        with open(datafile, 'wb') as writeFile:
            writer = csv.writer(writeFile)
            # TODO: add header row

            for list_element in daily_inventory:
                writer.writerow(list_element)