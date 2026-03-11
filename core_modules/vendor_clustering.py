# import pandas as pd
# from sklearn.cluster import KMeans

# class VendorClustering:

#     def cluster_vendors(self, data):

#         X = data[['financial_score','delivery_score','quality_score']]

#         model = KMeans(n_clusters=3)

#         data['cluster'] = model.fit_predict(X)

#         return data