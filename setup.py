from setuptools import setup, find_packages
import os

setup(
    name='solarpv-analytics-etl-pipeline',
    url='https://github.com/ayosamuel/solarpv-analytics-etl-pipeline',
    author='Ayokunle Samuel',
    author_email='70694811+ayosamuel@users.noreply.github.com',
    packages=find_packages(include=['etl', 'etl.*']),
    install_requires=[
        'numpy>=1.20.0',
        'pandas>=1.3.0',
        'openpyxl>=3.0.0',      # Excel export support
        'matplotlib>=3.3.0',    # Basic plotting
        'seaborn>=0.11.0',      # Enhanced visualizations
        'plotly>=5.0.0',        # Interactive charts
        'scikit-learn>=1.0.0'   # ML algorithms
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'jupyter>=1.0.0',
            'ipython>=7.0.0'
        ]
    },
    version='2.0.0',
    license='MIT',
    description='ETL pipeline for solar plant analytics with integrated ML and visualization',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
    keywords='solar energy analytics etl pipeline machine-learning visualization',
    entry_points={
        'console_scripts': [
            'ibv-demo=test_complete_pipeline:main',
        ],
    },
)
