import subprocess
import os
import argparse
import configparser
from pathlib import Path
from cryptography.fernet import Fernet
import shlex

def main():
    config = configparser.ConfigParser()
    config.read("settings.ini") # iterations

    parser = argparse.ArgumentParser(description="Secure deletion program")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', type=str)
    group.add_argument("path", default=argparse.SUPPRESS, nargs="?")

    args = parser.parse_args()

    iterations = int(config["DEFAULT"]["Iterations"])

    files = []

    if args.r != None:
        path = Path(args.r)
        files = [str(file) for file in path.rglob('*') if file.is_file()]
    else:
        files.append(Path(args.path))

    # -- Encryption ---
    for file in files:

        if os.path.exists(file):

            fernet = Fernet(Fernet.generate_key())

            with open(file, 'rb') as f:
                original = f.read()

            encrypted = fernet.encrypt(original)

            with open(file, 'wb') as f:
                f.write(encrypted)

            # --- Deletion ---

            file_size = os.path.getsize(file)

            if file_size == 0:
                exit()

            block_size = 4096
            count = (file_size + block_size - 1) // block_size

            for _ in range(iterations):
                subprocess.run(f"dd if=/dev/zero of={shlex.quote(file)} bs={block_size} count={count}", shell=True) # > /dev/null 2>&1 &
                print(1)

        else:
            print(f"{file} does not exist")

if __name__ == "__main__":
    main()
