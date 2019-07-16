import utilities_LBrands
import datetime
import sys
import sim_server
sys.path.append("C:\Python26\SCG_64\Lib")


low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()
dt = datetime.datetime
d = datetime.date
td = datetime.timedelta
t = datetime.time


def main():
    # set the path for sim input tables
    # read the global variables file and get path for external inputs
    # read in the forecast file and add to a dictionary on each site-product key=date, value=quantity
    # read in the parameters file and add custom attributes
    # read the tranport time and add as a custome attribute = lead time



    datafile = "C:\\Users\\greg.plank\\OneDrive - LLamasoft, Inc\\SCG\\Projects\\201907 LBrands\\Models\\ExampleModel\\simulated engineered jun 19_v1 (Converted)_NetSimData\\FacilityHistoricalForecast.txt"
    forecast_dict = utilities_LBrands.import_forecast(datafile)
    model_obj.setcustomattribute('forecast_dict',forecast_dict)

    sim_server.ScheduleCustomEvent('InventoryReport', )




    ''' Scratch bits
    datafile = "C:\\Users\\greg.plank\\OneDrive - LLamasoft, Inc\\SCG\\Projects\\201907 LBrands\\Models\\ExampleModel\\simulated engineered jun 19_v1 (Converted)_NetSimData\\FacilityHistoricalForecast.txt"
    forecast_dict = utilities_LBrands.import_forecast(datafile)
    
    start_date = dt(2018, 10, 1, 0, 0)
    end_date = dt(2018, 11, 15, 0, 0)
    forecast_window = 30
    site = '0005'
    product = '23974525'
    
    print utilities_LBrands.forecast_sum(site,product,start_date,forecast_window,forecast_dict)
    '''





