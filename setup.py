from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="xbox-photo-sorter",
    version="0.1.0",
    author="Azkiw",
    description="Fast photo sorting application using Xbox controller",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Azkiw/xbox-photo-sorter",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Multimedia :: Graphics :: Viewers",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "xbox-photo-sorter=xbox_photo_sorter.__main__:main",
        ],
    },
)
