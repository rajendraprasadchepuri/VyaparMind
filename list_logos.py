import os
import glob

files = glob.glob("assets/uploads/*logo*")
files.sort(key=os.path.getmtime, reverse=True)

print("Latest Uploaded Logos:")
for f in files[:5]:
    print(f"{f} - {os.path.getmtime(f)}")
