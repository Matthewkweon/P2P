from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Include frontend files in package_data
def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

frontend_files = package_files('src/p2p_chat/frontend')

setup(
    name="p2p-chat",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A simple asynchronous P2P chat application with web frontend",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/p2p-chat",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "p2p_chat": frontend_files,
    },
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
        "websockets",
    ],
    entry_points={
        "console_scripts": [
            "p2p-chat-server=p2p_chat.server:main_entry",
            "p2p-chat-client=p2p_chat.client:main_entry",
            "p2p-chat-api=p2p_chat.message_api:main_entry",
            "p2p-chat-thermometer=p2p_chat.services.thermometer:main_entry",
            "p2p-chat-websocket=p2p_chat.websocket_bridge:main_entry",
            "p2p-chat-web=p2p_chat.web_server:main_entry",
        ],
    },
)