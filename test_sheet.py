import pandas as pd

# Your Student Google Sheet ID (from the link you gave me)
sheet_id = "16kjwgjWoiZ6kmFJHd2AkZfIYZz99hZY6GxsfXU8CGUM"

# This is the magic URL format to read a Google Sheet as CSV
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

print("Connecting to your live Google Sheet...")

try:
    # Pandas reads the web link directly into a table (DataFrame)
    df = pd.read_csv(url)
    
    print(f"✅ Success! Loaded {len(df)} students from the live sheet.")
    print("\nHere are the first 5 students:")
    print(df[['student_name', 'roll_no', 'section']].head())
    
except Exception as e:
    print("❌ Failed to connect. Make sure the sheet is shared as 'Anyone with the link can view'.")
    print("Error:", e)