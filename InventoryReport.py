import sys
import sim_server
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()

def main():
    for site_obj in model_obj.sites:
        for product_obj in site_obj.products:
            debug_obj.trace(1,'%s,%s,%s,%s' % (sim_server.NowAsString(), site_obj.name,
                                               product_obj.product.name,product_obj.inventory))