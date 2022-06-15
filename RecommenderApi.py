import joblib
import json
from flask import Flask, request

import pandas as pd


app = Flask(__name__)


def loading_data(outliers = True):
    
    try:
        data = joblib.load("3_recommendations_for_9974_products.joblib")
    
        print("Successfuly imported necessary file for recommendation.")

    except:
        raise Exception("Could not load the necessary dictionary for making recommendations ! Please check the file.")
    
    if outliers:
        try:
            outliers = joblib.load("outliers.joblib")
        
            print("Outliers successfully loaded.")
        
        except:
            raise Exception("Outliers could not loaded successfully.")
            
    
    return data, outliers
        
class Recommender:
    
    def __init__(self, data, outliers, prod_list, n = 3):
        
        self.data = data
        self.outliers = outliers
        self.prod_list = prod_list
        self.n = n
        
    # Input Validation : : :

    def input_validation(self):
        
        cart = list(set(self.prod_list))
        
        for product in cart:
            
            if product not in self.data.keys():
                
                cart.remove(product)
                
                print(f"{product} is not included in the recommendation dataframe.", 
                      "Removed from the cart list for recommendations.")
                
            if product in self.outliers:
                
                print(f"{product} is in outliers list. There are no recommendations for them for now !")
                
        if len(cart) == 0:
            
            raise Exception("Cart is empty. Please add items for obtaining recommendations.")
            
        self.cart = cart
            

    def recommend(self):
    
        # recommender metodu yukarda bir input_validation yapıldığını assume ediyor !!! aldığı prod_list parametresi ordan
        # çıkmış / valide edilmiş olmalı...
        
        self.final_recoms = {}
        self.prods = []
        self.recoms = []
        self.scores = []
        self.index = []
        
        for i in range(self.n):
        
            for product in list(set(self.cart)):
            
                recommendations = self.data.get(product, "NA")
            
                recom = recommendations.get(i, "NA")
                score = recommendations.get(f"score_{i}", 0)
                
                self.index.append(i)
                self.prods.append(product)
                self.recoms.append(recom)
                self.scores.append(score)
                
            i += 1
            
        self.results = { "Index" : self.index, 
                    "Products" : self.prods,
                    "Recommendations": self.recoms,
                    "Scores" : self.scores
                      }
        
        df = pd.DataFrame(self.results).set_index("Index")
        
        # recommendationlar hali hazırda sepette bulunan ürünlerden farklı olsunlar !
        
        df = df[~df["Recommendations"].isin(list(set(self.cart)))]
        
        # LIFT SCORE a göre yukardan aşağıya sıralayalım.
        
        df.sort_values("Scores", ascending = False, inplace = True)
        
        self.final_recommendations = df.copy()
        
        df = df[:10][["Recommendations", "Scores"]]
        

        for index,row in df[:10][["Recommendations", "Scores"]].iterrows():
    
            self.final_recoms.update( { row["Recommendations"] : row["Scores"]  } )
        
        results_json = json.dumps(self.final_recoms, ensure_ascii = False)
        
        return results_json
    
@app.route("/", methods = ["POST", "GET"])
def hello():
    return "Hello HepsiBurada. This is Furkan."


@app.route("/pred", methods = ["POST", "GET"])
def main():
    
    requested_data = request.get_json(force=True)
    
    cart_products = []
    
    for key in requested_data.keys():
        
        cart_products.append(requested_data[key])

    data, outliers = loading_data(outliers = True)
    
    recommender_obj = Recommender(data = data, outliers = outliers, prod_list = cart_products, n = 3)
    
    recommender_obj.input_validation()
    
    results = recommender_obj.recommend()
    
    return results
    


if __name__ == "__main__":
    
    app.run("127.0.0.1", debug = True,  port=8080) 