from setuptools import setup, find_packages
import pathlib
import pkg_resources

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with pathlib.Path('requirements.txt').open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

setup(
    name='sysdiagnose',
    version='0.1.0',

    author='EC-DIGIT-CSIRC',
    # author_email='your.email@example.com',

    url='https://github.com/EC-DIGIT-CSIRC/sysdiagnose',
    description='A tool for sysdiagnose parsing and analysis',
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=find_packages(),
    py_modules=['sysdiagnose'],
    entry_points={
        'console_scripts': [
            'sysdiagnose=sysdiagnose:main',
        ],
    },
    install_requires=install_requires,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: EUPL 1.2',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)
