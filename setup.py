from setuptools import setup, find_packages

setup(
    name='docent',
    version='0.0.1',
    description=("Install python scripts into a virtualenv, "
                 "then expose them outside of the virtualenv"),
    zip_safe=False,
    classifiers=[
        "Development Status :: 1 - Pre-Alpha"
    ],
    packages=['docent'],
    entry_points={
        'console_scripts': [
            'docent = docent:main'
        ]
    }
)
