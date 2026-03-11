# import pandas as pd
# from sklearn.ensemble import RandomForestClassifier

# class VendorRiskModel:

#     def __init__(self):
#         self.model = RandomForestClassifier(n_estimators=100)

#     def train(self, data):
#         X = data[['financial_score', 'compliance_score', 'delivery_score']]
#         y = data['risk_level']

#         self.model.fit(X, y)

#     def predict(self, vendor):
#         return self.model.predict(vendor)