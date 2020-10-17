from importer import DataImporter, model_dir
from manager import DataManager, Autogui
from models import Modeller
import os, time
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")
importer = DataImporter('crypto')
manager = DataManager()
regressor = Modeller(model_name="model_1", modelType="regressor")
classifier = Modeller(model_name="model_2", modelType="classifier")
player = Autogui()

def get_time():
    now = datetime.now()    
    hr, minute, sec = str(int(now.hour)), str(int(now.minute)), str(int(now.second))
    if len(hr)==1:
        hr = "0" + hr
    if len(minute)==1:
        minute = "0" + minute 
    if len(sec)==1:
        sec = "0" + sec
    return f"{hr}:{minute}:{sec}"

def driver_program():
    start_time = time.time()
    print("Updating current.csv.......", end="", flush=True)
    importer.download_current_data()
    print("Updated!!")
    curr_value = manager.read_current_data(filename="current.csv")
    if "model_1.pickle" in os.listdir(model_dir):
        regressor.load_model(model_name = "model_1")
        model_1_pred = regressor.predict(curr_value)
    else:
        print(f"Model not present in path: {model_dir}")
    curr_value = manager.add_prediction_on_dataset(curr_value, model_1_pred)
    action_value = manager.make_target(curr_value)['target'][0]
    # if "model_2.pickle" in os.listdir(model_dir):
    #     classifier.load_model(model_name = "model_2")
    #     model_2_pred = classifier.predict(curr_value)
    # else:
    #     print(f"Model not present in path: {model_dir}")
    
    #Display or perform action here
    action = manager.get_key(action_value)
    print(f"{action} at time: {get_time()}")
    player.move(action)

    #time to sleep
    end_time = time.time()
    sleep_time = round(60-(end_time-start_time),2)
    time.sleep(sleep_time) 

if __name__=="__main__":
    while True:
        driver_program()
              
