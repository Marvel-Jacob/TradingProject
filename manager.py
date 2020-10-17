from importer import data_dir, historical_data_dir
from models import Modeller
import pandas as pd
import numpy as np
import pyautogui

class DataManager:  
    
    def __init__(self):
        self.regressor = Modeller(model_name="model_1", modelType="regressor")
        self.classifier = Modeller(model_name="model_2", modelType="classifier")
        self.hashmap = {"Buy":0,"Sell":1,"Hold":-1}

    #function to categorize data to buy, sell, hold
    def _bucket(self, row):
        # row is in ohlc format
        #o-0, h-1, l-2, c-3, no-4, nh-5, nl-6, nc-7
        # if row[0]<row[4] and row[3]<row[7] and row[4]<row[7] and row[0]<row[3]:
        #     return self.hashmap["Buy"]
        # elif row[0]>row[4] and row[3]>row[7] and row[4]>row[7] and row[0]>row[3]:
        #     return self.hashmap["Sell"]
        # elif row[3]>row[0] and abs(row[3]-row[0])<=0.1 and abs(row[0]-row[2])>=0.3:
        #     return self.hashmap["Buy"]
        # elif row[3]<row[0] and abs(row[3]-row[0])<=0.1 and abs(row[0]-row[2])>=0.3:
        #     return self.hashmap["Sell"]
        # else:
        #     return self.hashmap["Hold"]
        if np.mean(row[4:8])>np.mean(row[0:4]) and row[7]>row[3]:
            return self.hashmap["Buy"]
        elif np.mean(row[4:8])<np.mean(row[0:4]) and row[7]<row[3]:
            return self.hashmap["Sell"]
        else:
            return self.hashmap["Hold"]
    
    def get_key(self, value):
        for key, dict_value in self.hashmap.items():
            if dict_value == value:
                return key
        return "Key not found"

    #function to create a target column in the data as a label for the model to predict
    def make_target(self, data,  columns = ['open(t)','high(t)','low(t)','close(t)','open(t+1)','high(t+1)','low(t+1)','close(t+1)']):
        data['target'] = data[columns].apply(lambda x: self._bucket(x), axis=1)
        return data

    #driver function to read the data and process the data within this function
    def read_data(self, filename = None):
        data = pd.read_csv(f"{data_dir}{filename}", index_col = "timestamp", parse_dates=True).sort_index(ascending=True)
        # data = data.resample("Min").ffill() #uncomment if reinitializing master.csv
        data[['open(t+1)','high(t+1)','low(t+1)','close(t+1)']] = data[['open(t)','high(t)','low(t)','close(t)']].shift(-1)
        data.dropna(inplace = True)
        return data

    def read_current_data(self, filename = None):
        data = pd.read_csv(f"{data_dir}{filename}", index_col = "timestamp", parse_dates=True).sort_index(ascending=True)
        return data

    def add_prediction_on_dataset(self, data, pred):
        data[['open(t+1)','high(t+1)','low(t+1)','close(t+1)']] = pred
        return data
        
        
    #function to split the data into train and test for the model
    def train_test_split(self, data, targetCol = None, train_size = None):
        if train_size!=None and train_size!=None:
            limit = int(data.shape[0]*(train_size/100))
            train_x, train_y = data[:limit].drop(targetCol, axis=1),  data[:limit][targetCol]
            test_x, test_y = data[limit:].drop(targetCol, axis=1), data[limit:][targetCol]
            return train_x, train_y, test_x, test_y 
        else:
            raise ValueError("Target column and train size cannot be None")

    def normal_split(self, data, targetCol = None):
        if targetCol!=None:
            if len(targetCol)!=1:
                train_x, train_y = data.drop(targetCol, axis=1),  data[targetCol]
            else:
                train_x, train_y = data.drop(targetCol, axis=1),  np.array(data[targetCol]).ravel()
            return train_x, train_y
        else:
            raise ValueError("Target column cannot be None")
    
    #reads the master file and initilizes the models in the models directory to use later on for real time
    #predictions
    def initial_train_on_master(self, filename=None): 
        if filename!=None:
            print("Initiating Model training from historical data...", flush=True)
            data = self.read_data(filename = filename)
            train_x, train_y = self.normal_split(data, targetCol=["open(t+1)","high(t+1)","low(t+1)","close(t+1)"])
            print("Training the model now...", end=" ", flush=True)
            self.regressor.fit(train_x, train_y)
            self.regressor.save_model(model_name = "model_1")
            print("Trained!!", flush=True)
            data = self.make_target(data)
            data.to_csv(f'{data_dir}changed master data.csv', index=False) # line to check the file after process            
            # train_x, train_y = self.normal_split(data, targetCol=["target"])
            # self.classifier.fit(train_x, train_y)
            # self.classifier.save_model(model_name = "model_2")
            print("Task Completed!")
        else:
            raise ValueError("Filename cannot be None")
    
import time
class Autogui:
    def __init__(self):
        self.gui = pyautogui

    def locate(self):
        time.sleep(5)
        x, y = self.gui.position()
        return x, y

    def move(self, status):
        if status=="Buy":
            click_area = [1264, 496]
            self.gui.click(click_area) 
        elif status=="Sell":
            click_area = [1266, 558]
            self.gui.click(click_area)
        else:
            return "on Hold"
       
