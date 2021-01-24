from setuptools import setup, find_packages

setup(
    name="vlt",
    version="0.0.1",
    author="Michael Green",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},   

    entry_points={
        'console_scripts': ['vlt=vlt.app:main']
    },
)