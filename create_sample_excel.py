"""
Create a sample Excel file for testing the batch video generation.
"""
import pandas as pd

# Sample data
data = {
    'image': [
        r'C:\Users\admin\Downloads\216646f51cb893e6caa9.jpg',
        r'C:\Users\admin\Downloads\216646f51cb893e6caa9.jpg',
        r'C:\Users\admin\Downloads\216646f51cb893e6caa9.jpg',
    ],
    'prompt': [
        'A gentle breeze moves through the scene, causing subtle movements',
        'The camera slowly zooms in while the subject remains still',
        'Soft ambient lighting changes gradually in the background',
    ]
}

df = pd.DataFrame(data)
df.to_excel('sample_jobs.xlsx', index=False)
print("Created: sample_jobs.xlsx")
print(df)
