from importer import DataImporter, data_dir, model_dir
from manager import DataManager
from models import Modeller
from datetime import date, datetime
import pandas as pd
import os

class Scheduler:

    def __init__(self):
        self.importer = DataImporter('crypto')
        self.manager = DataManager()
        self.regressor = Modeller(model_name="model_1", modelType="regressor")
        self.classifier = Modeller(model_name="model_2", modelType="classifier")
        self.todays_filename, self.hourly_filename = self.importer.todays_filenames()


    def is_weekday(self):
        if date.today().weekday()==5 or date.today().weekday()==6:
            return True
        return False
    
    def get_time(self):
        hr = str(int(datetime.now().hour))
        minute = str(int(datetime.now( ).minute))
        if len(hr)==1:
            hr = "0" + hr
        if len(minute)==1:
            minute = "0" + minute 
        return f"{hr}:{minute}"
        

    def collect_realtime(self, hourly=False):
        if hourly:
            return self.importer.download(hourly=hourly)
        return self.importer.download(hourly)

    def update_master(self):
        main_data = pd.read_csv(f"{data_dir}master.csv")
        data = pd.read_csv(f"{data_dir}{self.todays_filename}.csv").sort_values(by="timestamp", ascending=True)
        main_data = main_data.append(data, ignore_index=True)
        main_data.drop_duplicates(inplace=True)
        main_data.to_csv("master.csv", index=False)

    
    def retrain_model_1(self):
        data = self.manager.read_data(filename=self.hourly_filename)
        train_x, train_y = self.manager.normal_split(data, targetCol = ['open(t+1)','high(t+1)','low(t+1)','close(t+1)'])
        self.regressor.load_model(model_name = "model_1")
        self.regressor.fit(train_x, train_y)
        self.regressor.save_model(model_name = "model_1")
        print("Model 1 trained!")

    def retrain_model_2(self):
        data = self.manager.make_target(self.manager.read_data(filename=self.hourly_filename))
        train_x, train_y = self.manager.normal_split(data, targetCol = ['target'])
        self.classifier.load_model(model_name = "model_2")
        self.classifier.fit(train_x, train_y)
        self.classifier.save_model(model_name = "model_2")
        print('Model 2 trained!')

    def initialize(self, filename=None):
        if filename!=None:
            self.manager.initial_train_on_master(filename=filename)
        else:
            raise ValueError("Filename must be given")   
    
if __name__=="__main__":
    player = Scheduler()
    if ("model_1.pickle") not in os.listdir(model_dir):
        player.initialize(filename="master.csv")
    # if not player.is_weekday():
    if player.get_time()=="09:53":
            print("Extracting Intraday...", flush=True)
            player.collect_realtime()
            print("Extracted!!")
    else:
        print("Extracting Hourly Intraday...", flush=True)
        player.collect_realtime(hourly=True)
        print("Extracted!!")
        print("Retraining model....")
        player.retrain_model_1()
