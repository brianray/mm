from setuptools import setup, find_packages


setup(
    name='Marmir',
    version="0.1",
    description='Marmir: makes spreadsheets easy',
    author='Brian Ray',
    author_email='brianhray@gmail.com',
    maintainer='Brian Ray',
    maintainer_email='brianhray@gmail.com',
    url='https://github.com/brianray/mm',
    long_description="Python power spreadsheets on steroids",
    #      license="Brian Ray", TBD
    platforms=["any"],
    packages=find_packages(),
    include_package_data=True,
)