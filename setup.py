from setuptools import setup, find_packages

setup(
    python_requires=">=3.10",
    name="code_quality_analyzer",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "astroid",
        "networkx",
        "pyyaml",
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "analyze_code_quality=code_quality_analyzer.main:analyze_project",
        ],
    },
    author="Karthik Shivashankar",
    author_email="karthik13sankar@outlook.com",
    description="A tool to detect code smells, architectural smells, and structural smells in Python projects",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/KarthikShivasankar/code_quality_analyzer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        'dev': [
            'pytest',
            'sphinx',
            'sphinx-rtd-theme',
        ],
        # Optional ML extras for SPN/DETR-style training.
        'ml': [
            # PyTorch + SciPy: pin to versions with reliable Python 3.12 wheels.
            'torch>=2.4.0',
            'transformers>=4.41.0',
            'tokenizers>=0.15.0',
            'scipy>=1.13.0',
            'numpy>=1.26.4',
            'tqdm>=4.66.0',
        ],
    },
)