
import os
try:
    path = r"\\.\c:\Users\henri\Projets\ragkit\NUL"
    if os.path.exists(path):
        os.remove(path)
        print("Deleted NUL")
    else:
        print("File not found via extended path")
        # Try standard path just in case, though risky
        # os.remove("NUL") 
except Exception as e:
    print(f"Error: {e}")
