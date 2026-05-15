"""Test SPSS syntax execution via built-in Python 3.4."""
import spss, spssaux, os, sys

data_path = r'D:/Projects/SPSS Natural Language Assistant(SNLA)/data/fixtures/test_data.sav'
outdir = r'D:/Projects/SPSS Natural Language Assistant(SNLA)/p0_output'
os.makedirs(outdir, exist_ok=True)

# Route OMS output to XML
xml_path = os.path.join(outdir, 'frequencies_test.xml')

oms_syntax = """
OMS /SELECT TABLES /DESTINATION FORMAT=OXML OUTFILE='{}'.
GET FILE='{}'.
FREQUENCIES VARIABLES=gender.
OMSEND.
""".format(xml_path, data_path)

print("Submitting syntax...")
spss.Submit(oms_syntax)
print("Done. Checking output...")

# Check if XML was created
if os.path.exists(xml_path):
    size = os.path.getsize(xml_path)
    print(f"XML output: {xml_path} ({size} bytes)")
    with open(xml_path, 'r') as f:
        content = f.read()
        print(f"Content preview: {content[:500]}")
else:
    print(f"XML NOT created at {xml_path}")
    # Check for .lst output
    lst = os.path.join(outdir, 'frequencies_test.lst')
    if os.path.exists(lst):
        print(f"Found LST: {lst}")
    # Check SPSS working directory
    print(f"SPSS output file: {spss.GetOutputFile()}")
