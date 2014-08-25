from setuptools import setup

setup(
    name="master",
    version="0.0.0",
    packages=["master"],
    install_requires=[
        "buildbot==0.8.9",
        "psycopg2"
    ]
)
