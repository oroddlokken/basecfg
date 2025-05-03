from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as _f:
    long_description = _f.read()

extras = {
    "extras": ["python-dotenv>=1.0.0", "toml>=0.10.2"],
}

setup(
    name="voecfg",
    version="0.2.0",
    author="Ove Ragnar Oddløkken",
    author_email="post@rykroken.net",
    description="Configuration management",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
