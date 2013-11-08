from setuptools import setup, find_packages

setup(
    name = "pamietacz",
    version = "0.2.0",
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools', 'markdown==2.3.1', 'pygments==1.6', 'lxml', 'Pillow', 'django==1.6.0'],
)
