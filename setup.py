from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="flextabs",
    version="0.2.0",
    author="MS-32154",
    author_email="msttoffg@gmail.com",
    description="A flexible and extensible tab manager widget for tkinter applications built on top of ttk.Notebook",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MS-32154/flextabs",
    packages=find_packages(),
    python_requires=">=3.8",
    keywords="tkinter, ttk, Notebook, tabs, gui, widget, interface",
    install_requires=[
        "Pillow",
    ],
    project_urls={
        "Bug Reports": "https://github.com/MS-32154/flextabs/issues",
        "Source": "https://github.com/MS-32154/flextabs",
    },
)
