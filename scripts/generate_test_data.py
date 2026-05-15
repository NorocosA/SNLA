"""Generate test_data.sav for SNLA P0 verification.

Creates a small SPSS .sav dataset with 4 variables and 30 cases:
  - gender  (Numeric, 1=Male 2=Female, value labels)
  - score   (Numeric, test scores 60-100)
  - class   (String, class names A/B/C)
  - age     (Numeric, 18-25)

This is the canonical P0 test dataset used by verify_spss.py
and all subsequent integration tests.
"""
import os, sys, random
import pyreadstat
import pandas as pd

random.seed(42)

# Generate 30 cases
n = 30
genders = [1, 2] * 15  # balanced: 15 male, 15 female
random.shuffle(genders)

# Score: males ~78, females ~84 (small real difference)
scores = []
ages = []
for g in genders:
    if g == 1:
        scores.append(round(random.gauss(78, 8), 1))
        ages.append(random.randint(18, 24))
    else:
        scores.append(round(random.gauss(84, 7), 1))
        ages.append(random.randint(18, 25))
# Clamp scores to [60, 100]
scores = [max(60, min(100, s)) for s in scores]

# Class assignments (A/B/C)
classes = ["A", "B", "C"] * 10
random.shuffle(classes)

df = pd.DataFrame({
    "gender": genders,
    "score": scores,
    "class": classes,
    "age": ages,
})

# Write .sav with metadata
outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "fixtures")
os.makedirs(outdir, exist_ok=True)
outpath = os.path.join(outdir, "test_data.sav")

pyreadstat.write_sav(
    df,
    outpath,
    column_labels=["Gender", "Test Score", "Class Name", "Age"],
    variable_value_labels={
        "gender": {1: "Male", 2: "Female"},
    },
    variable_measure={"gender": "nominal", "score": "scale", "class": "nominal", "age": "scale"},
)

print(f"Created: {outpath}")
print(f"  Cases: {len(df)}")
print(f"  Variables: {list(df.columns)}")
print(f"  Gender distribution: {df['gender'].value_counts().to_dict()}")
print(f"  Score range: {df['score'].min():.1f} - {df['score'].max():.1f}")
print(f"  Mean score by gender:")
print(f"    Male:   {df[df['gender']==1]['score'].mean():.1f}")
print(f"    Female: {df[df['gender']==2]['score'].mean():.1f}")
print(f"  Classes: {df['class'].value_counts().to_dict()}")
