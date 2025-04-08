from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="p2p-chat",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A simple asynchronous P2P chat application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/p2p-chat",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "asyncio",
        "httpx",
        "fastapi",
        "uvicorn",
        "motor",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "p2p-chat-server=p2p_chat.server:main_entry",
            "p2p-chat-client=p2p_chat.client:main_entry",
            "p2p-chat-api=p2p_chat.message_api:main_entry",
            "p2p-chat-thermometer=p2p_chat.services.thermometer:main_entry",
        ],
    },
)