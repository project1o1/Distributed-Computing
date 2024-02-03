from constants import PORT
import tensorflow as tf
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


    
# load data
df = pd.read_csv('./dataset/train.csv')

# Extract features and target variable
X = df.drop(['Weight', 'Index'], axis=1).to_numpy().reshape(-1, 1)  # Features
y = df['Height']  # Target variable

# Clean and transform string data to numerical values
# le = LabelEncoder()
# X['Sex'] = le.fit_transform(X['Sex'])
# X['Cabin'] = le.fit_transform(X['Cabin'])
# X['Embarked'] = le.fit_transform(X['Embarked'])

epochs = 5


model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(32, input_shape=(X.shape[1],), activation='relu'),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(1)
])
model.compile(optimizer='adam', loss='mse', metrics=['mae'])
print(model.evaluate(X, y))

model.fit(X, y, epochs=epochs)

print(model.evaluate(X, y))

# model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])