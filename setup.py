from setuptools import setup, find_packages

setup(
    name="laptop-life-saver",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "psutil",
        "pywin32",
        "WMI",
        "supabase",
        "python-dotenv",
    ],
)
