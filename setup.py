from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as _f:
    long_description = _f.read()

extras = {
    "extras": ["python-dotenv>=1.0.0", "toml>=0.10.2"],
}

setup(
    name="basecfg",
    version="0.1.0",
    author="Ove Ragnar Oddløkken",
    author_email="post@rykroken.net",
    description="Configuration management",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
)
