#!/usr/bin/env python3

import subprocess
import os
import argparse
from pathlib import Path
from cryptography.fernet import Fernet
import shlex
import sys

def writeOnes(file, block_size, count):
    subprocess.run(f"tr '\\0' '\\377' < /dev/zero | dd bs={block_size} count={count} of={file} > /dev/null 2>&1 &", shell=True)

def writeZeros(file, block_size, count):
    subprocess.run(f"dd if=/dev/zero of={file} bs={block_size} count={count} > /dev/null 2>&1 &", shell=True)

def writeRand(file, block_size, count):
    subprocess.run(f"dd if=/dev/urandom bs={block_size} count={count} of={file} > /dev/null 2>&1 &", shell=True)

def main():
    parser = argparse.ArgumentParser(description="Secure deletion program")

    parser.add_argument('-r', '-R', '--recursive', action="store_true", help="Recursive delete file and folders")
    parser.add_argument("path", default=argparse.SUPPRESS, nargs="?")

    parser.add_argument('-f', '--force', action="store_true", help="Ignore nonexistent files and arguments, never prompt")
    parser.add_argument('-i', action="store_true", help="Prompt before every removal")
    parser.add_argument('-v', '--verbose', action="store_true", help="Explain whats happening")
    parser.add_argument('-c', '-C', '--count', type=int, help="Change the number of iterations")

    args = parser.parse_args()

    iterations = 6

    files = []

    if os.geteuid() != 0:
        # Re-launch the script with sudo if not already running as root
        os.execvp("sudo", ["sudo"] + sys.argv)

    if args.count != None:
        iterations = args.count

    if args.recursive:
        path = Path(args.recursive)
        originalPath = path
        files = [str(file) for file in path.rglob('*') if file.is_file()]
    else:
        files.append(Path(args.path))

    # -- Encryption ---
    for file in files:

        if os.path.exists(file):

            delete = True
            if args.verbose:
                print("Starting Process")

            if args.i:
                confirmed = False
                while not confirmed:
                    confirm = input(f"Would you like to delete {file}? [y/n] >> ")
                    if confirm == "y":
                        confirmed = True
                    elif confirm == "n":
                        confirmed = True
                        delete = False
                    else:
                        print("Invalid response")

            if delete:
                fernet = Fernet(Fernet.generate_key())
                
                if args.verbose:
                    print("Encrypting File")
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

                for i in range(iterations):
                    if args.verbose:
                        print(f"\n Iteration {i + 1}/{iterations}\n")
                        print("Writing Zeros")
                        writeZeros(file, block_size, count)
                        print("Writing Ones")
                        writeOnes(file, block_size, count)
                        print("Writing Randoms")
                        writeRand(file, block_size, count)
                    else:
                        writeZeros(file, block_size, count)
                        writeOnes(file, block_size, count)
                        writeRand(file, block_size, count)
                
                if args.force:
                    subprocess.run(f"rm -f {file}", shell=True)
                else:
                    subprocess.run(f"rm {file}", shell=True)
                
                if args.verbose:
                    print("\nFile removed")

        else:
            print(f"{file} does not exist")

    if args.recursive:
        print(args.recursive)
        if args.force:
            subprocess.run(f"rm -rf {originalPath}", shell=True)
        else:
            subprocess.run(f"rm -r {originalPath}", shell=True)

    if args.verbose:
        print("Process Complete")

if __name__ == "__main__":
    main()
