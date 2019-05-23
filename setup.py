import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="interec",
    version="1.0.0",
    author="Raveen Savinda Rathnayake",
    author_email="raveen.s.r@gmail.com",
    description="A package for integrator recommendation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RAVEENSR/interec",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License 2.0",
        "Operating System :: OS Independent",
    ],
)
