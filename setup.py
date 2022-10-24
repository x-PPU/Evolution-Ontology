# import
import codecs
import os.path
import setuptools


def read(rel_path):
    """Read a code file
    """
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    """Fetch the version of package by parsing the __init__ file
    """
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


# fetch readme for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sparql_query_viz",
    # version="0.0.6",
    version=get_version("sparql_query_viz/__init__.py"),
    author="Maximilian Mayerhofer",
    author_email="mayerhofermaximilian@googlemail.com",
    description="sparql_query_viz - your interactive ontology visualization and SPARQL querying tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.lrz.de/maximilianmayerhofer/SPARQL-Query-Viz",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    package_data={'': ['datasets/*', 'assets/*', 'datasets/ontologies/*',
                       'datasets/queries/*', 'datasets/templates/*']},
    include_package_data=True,
    install_requires=['dash>=2.0.0',
                      'visdcc>=0.0.40',
                      'pandas>=1.3.5',
                      'dash_core_components>=2.0.0',
                      'dash_html_components>=2.0.0',
                      'dash_bootstrap_components>=0.11.1',
                      'dash_daq>=0.5.0',
                      'ontor>=0.3.0'],
)
