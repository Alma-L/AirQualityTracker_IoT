import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import OneClassSVM
from sklearn.cluster import KMeans

def run_ml_algorithm(df, algorithm="random-forest"):
    required_cols = ["pm2_5", "pm10", "temp", "humidity"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df_ml = df[required_cols].fillna(0)
    anomalies = pd.DataFrame()

    try:
        if algorithm == "random-forest":
            model = RandomForestRegressor(random_state=42)
            X = df_ml.drop(columns=['pm2_5'])
            y = df_ml['pm2_5']
            model.fit(X, y)
            preds = model.predict(X)
            df_temp = df.copy()
            df_temp['pred'] = preds
            df_temp['anomaly'] = abs(df_temp['pm2_5'] - df_temp['pred']) > 2 * df_temp['pm2_5'].std()
            anomalies = df_temp[df_temp['anomaly']].copy()

        elif algorithm == "svm":
            if len(df_ml) < 5:
                return []
            model = OneClassSVM(nu=0.05, kernel='rbf', gamma='scale')
            model.fit(df_ml)
            df_temp = df.copy()
            df_temp['anomaly'] = model.predict(df_ml)
            anomalies = df_temp[df_temp['anomaly'] == -1].copy()

        elif algorithm == "kmeans":
            if len(df_ml) < 2:
                return []
            model = KMeans(n_clusters=2, random_state=42, n_init=10)
            model.fit(df_ml)
            df_temp = df.copy()
            df_temp['cluster'] = model.labels_
            cluster_sizes = df_temp['cluster'].value_counts()
            anomaly_cluster = cluster_sizes.idxmin()
            anomalies = df_temp[df_temp['cluster'] == anomaly_cluster].copy()

        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        if 'timestamp' in df.columns:
            anomalies['timestamp'] = anomalies['timestamp'].astype(str)
        else:
            anomalies['timestamp'] = [None]*len(anomalies)

        return anomalies.to_dict('records')

    except Exception as e:
        print(f"ML algorithm error: {e}")
        return []
