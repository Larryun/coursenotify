import setuptools


setuptools.setup(
    name="cn_v2",
    version="1.2.00",
    author="CourseNotify",
    author_email="",
    description="Course Notify V1.2",
    long_description="Course Manager",
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    python_requires='>=3.4',
    install_requires=[
        "pymongo>=3.10.1",
        "requests>=2.22.0",
        "beautifulsoup4>=4.7.1",
        "PyYAML==5.3.1",
    ]
)
