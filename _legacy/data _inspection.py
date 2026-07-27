import pandas as pd

# Loading the dataset
df = pd.read_csv('sample_data_review.csv')

# Inspect structure

print("Dataset shape:", df.shape)
print("\nColumn names:", df.columns.tolist())
print("\nFirst 3 reviews:")
print(df.head(3))
print("\nData types:")
print(df.dtypes)

df.columns = ['user_id', 'product_id', 'rating', 'timestamp']
print(df.head(3))