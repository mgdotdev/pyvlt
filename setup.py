from setuptools import setup, find_packages

def read_requirements(requirements_file_path):
    """Return dependencies from a requirements file as a list.

    Read a requirements '.txt' file, where dependencies are separated by a new line.
    Removes all comments and options for pip, and return as a list of dependencies.

    :return:    requirements
    :rtype:     list
    """
    with open(requirements_file_path, 'r') as f:
        data = f.readlines()
    data = [i[: i.find("#")] if "#" in i else i for i in data]
    data = [i.strip() for i in data if i.strip()]
    data = [i for i in data if not i.startswith("-")]
    return data

setup(
    author="Michael Green",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        'console_scripts': ['vlt=vlt.app:main']
    }, 
    include_package_data=True,
    install_requires=read_requirements("requirements.txt"),
    name="vlt",     
    packages=find_packages(where="src"),
    package_data={"": ['*.txt']},
    package_dir={"": "src"},   
    python_requires='>=3.8',
    tests_require=read_requirements("requirements_testing.txt"),
    version="0.0.1",
)