import sys
import sim_server
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main():
    for site_obj in model_obj.sites:
        for site_product_obj in site_obj.products:
            daily_inventory = model_obj.getcustomattribute('daily_inventory')
            daily_inventory.append(
                [sim_server.NowAsString(), site_product_obj.site.name, site_product_obj.product.name,
                 site_product_obj.inventory])
            model_obj.setcustomattribute('daily_inventory', daily_inventory)

    sim_server.ScheduleCustomEvent('InventoryReport','24 HR','')