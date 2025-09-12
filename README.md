# Advanced-F1-Telemetry-Modeling-Driver-Style-Classification


📌 Descrition :- 

This project uses F1 telemetry data to model race performance and classify driver behavior with machine learning. By analyzing speed, throttle, braking, and gear data, we uncover unique driving styles and predict lap times. The system provides insights into sector performance, tire wear, and strategy optimization.




🚀 Features :-

1. Compare multiple drivers using telemetry metrics
2. Segment laps into sectors for detailed analysis
3. Cluster driving styles (Late Brakers, Smooth Cornering, Aggressive)
4. Predict lap times using regression models
5. Visualize speed, throttle, brake zones, and driver profiles
6. Generate reports linking style to car setup and tire usage



⚙️ Tech Stack :-

1. Python
2. FastF1 – telemetry data API
3. Scikit-learn – clustering & regression
4. Matplotlib / Seaborn – visualization
5. NumPy & Pandas – data handling




📊 Applications :-

1. Identifying braking and cornering patterns across drivers
2. Measuring lap time gains and losses by driving strategy
3. Predicting tire wear impact from driver style
4. Supporting engineers in race strategy decisions




✅ Future Work

1. Real-time telemetry streaming integration
2. Deep learning-based lap time prediction
3. Incorporation of track and weather conditions




📂 Workflow

1. Setup – Install required libraries and enable FastF1 cache.
2. Data Collection – Load race sessions, select drivers, and fastest laps.
3. Feature Engineering – Extract telemetry (speed, throttle, brake, rpm, gear) and compute derived metrics like acceleration and aggression index.
4. Clustering – Normalize features and classify driver behavior using KMeans/Hierarchical methods.
5. Lap Time Prediction – Train a RandomForestRegressor to estimate lap times from telemetry-derived features.
6. Visualization – Sector-wise comparisons and radar charts for driver profiles.
7. Reporting – Summarize sector gains/losses and connect driving styles with car performance.