from pathlib import Path
from setuptools import setup, find_packages


def get_requirements() -> dict:
    reqs_path: Path = Path(__file__).resolve().parent / 'requirements.txt'

    with reqs_path.open('r') as f_reqs:
        reqs = [line.strip() for line in f_reqs]

    return {'install_requires': reqs}


setup(
    name='log_analyser',
    packages=find_packages(),
    **get_requirements()
)
