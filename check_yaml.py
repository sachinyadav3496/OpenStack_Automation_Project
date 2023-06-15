import yaml
from yaml import SafeLoader
import os 

DIR_PATH = "output"
errors = []
if __name__ == "__main__":
    for path, dirs, files in os.walk(DIR_PATH):
        for fname in files:
            fp = open(os.path.join(path, fname))
            try:
                data = yaml.load(fp, SafeLoader)
                print(fname, "is correct")
            except:
                errors.append(fname)
    if errors:
        print("\nErorr Files:\n")
        print(*errors, sep='\n')
