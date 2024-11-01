import os
import venv
import subprocess

# Define the virtual environment directory
venv_dir = os.path.join(os.getcwd(), "nosqlvenv")

# Create the virtual environment
venv.create(venv_dir, with_pip=True)
print(f"Virtual environment created at {venv_dir}")

# Install dependencies from requirements.txt
subprocess.run([os.path.join(venv_dir, "Scripts", "pip"), "install", "-r", "requirements.txt"])
print("All dependencies installed.")
