from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.multioutput import MultiOutputRegressor
import pickle, os
import numpy as np
from importer import model_dir


class Modeller:
    def __init__(self, model_name = None, modelType = None):
        if modelType != None and model_name!=None:
            if model_name=="model_1" and modelType=="regressor":
                self.model = MultiOutputRegressor(XGBRegressor(objective="reg:squarederror",
                n_estimators = 600, max_depth = 7))
            elif model_name=="model_2" and modelType=="classifier":
                self.model = XGBClassifier()#base_score=0.5, booster='gbtree', gamma=0,
            #   importance_type='gain', learning_rate=0.300000012, max_depth=10,
            #   n_estimators=1000, objective='multi:softprob', num_class=3,
            #   tree_method='exact')
        else:
            raise ValueError("Model Type and name cannot be None")

    def __repr__(self):
        return f"Model Selected: {self.model}"

    def fit(self, train_x, train_y):
        return self.model.fit(train_x, train_y)

    def predict(self, test_x):
        return self.model.predict(test_x) 

    #save the model with the name given by the user
    def save_model(self, model_name = None):
        if model_name!=None:
            with open(f"{model_dir}{model_name}.pickle", "ab") as f:
                pickle.dump(self.model, f)
        else:
            raise ValueError("Model Name cannot be None")

    #loads two model. One is created for ohlc prediction and the other model is to predict the targeted action
    def load_model(self, model_name = None):
        if model_name!=None:
            if f"{model_name}.pickle" in os.listdir(model_dir):
                with open(f"{model_dir}{model_name}.pickle", "rb") as f:
                    self.model = pickle.load(f)
            else:
                return f"Model not present in path: {model_dir}"
        else:
            raise ValueError("Model name cannot be None")

    def show_accuracy(self, actuals, predictions):
        return np.sqrt(mean_squared_error(actuals, predictions))

