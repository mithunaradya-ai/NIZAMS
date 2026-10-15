from pathlib import Path

from setuptools import find_packages, setup


LONG_DESCRIPTION_PATH = Path(__file__).parent / "PYPI_DESCRIPTION.md"


setup(
    name="bhashini-client-sdk",
    version="0.2.4",
    description="Python SDK for Bhashini inference APIs with unified support for ASR, NMT, TTS, OCR, NER, speaker services, normalization, and image-language workflows.",
    long_description=LONG_DESCRIPTION_PATH.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Nidhi Jha",
    url="https://github.com/bhashini-dibd/Bhashini-client-python-library.git",
    license="MIT",
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    install_requires=[
        "requests>=2.25.0",
        "websockets>=12.0",
        "openpyxl>=3.1.0",
    ],
    python_requires=">=3.8",
    keywords=[
        "bhashini",
        "asr",
        "nmt",
        "tts",
        "ocr",
        "ner",
        "translation",
        "speech",
    ],
    project_urls={
        "Homepage": "https://github.com/bhashini-dibd/Bhashini-client-python-library.git",
        "Source": "https://github.com/bhashini-dibd/Bhashini-client-python-library.git",
        "Issues": "https://github.com/bhashini-dibd/Bhashini-client-python-library.git",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
