import pandas as pd

# Read CSV
df = pd.read_csv("sample_equipment_data.csv")

print("Full Data:")
print(df)

# Total equipment
total = len(df)

# Averages
avg_flow = df["Flowrate"].mean()
avg_pressure = df["Pressure"].mean()
avg_temp = df["Temperature"].mean()

# Type distribution
type_dist = df["Type"].value_counts()

print("\nSummary:")
print("Total equipment:", total)
print("Average Flowrate:", avg_flow)
print("Average Pressure:", avg_pressure)
print("Average Temperature:", avg_temp)
print("Type Distribution:")
print(type_dist)
