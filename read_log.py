import os

log_file = "Resume_Unknown.log"

if os.path.exists(log_file):
    print(f"📖 Analyzing {log_file} structural compilation notes...\n" + "="*50)
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    # Grab and print compilation errors or missing package markers
    errors_found = False
    for line in lines:
        if line.startswith("!") or "Error" in line or "Fatal" in line:
            print(line.strip())
            errors_found = True
            
    if not errors_found:
        print("No explicit fatal lines flagged. Printing the last 20 lines of processing metadata:")
        for line in lines[-20:]:
            print(line.strip())
    print("="*50)
else:
    print(f"❌ Could not locate {log_file} in your active workspace folder. Make sure the file exists!")