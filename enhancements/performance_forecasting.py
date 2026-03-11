# from sklearn.linear_model import LinearRegression
# import numpy as np

# class PerformanceForecast:

#     def forecast(self, months, scores):

#         X = np.array(months).reshape(-1,1)
#         y = np.array(scores)

#         model = LinearRegression()
#         model.fit(X,y)

#         future_month = [[max(months)+1]]

#         prediction = model.predict(future_month)

#         return prediction