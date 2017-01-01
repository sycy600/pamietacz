from setuptools import setup, find_packages

setup(
    name = "pamietacz",
    version = "0.2.0",
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = [
    'setuptools',
    'markdown==2.3.1',
    'pygments==1.6',
    'lxml==3.2.3',
    'Pillow==2.1.0'
    ]
)
