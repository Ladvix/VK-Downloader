# VK-Downloader

A simple async media downloader from the website vk.ru

> [!IMPORTANT]
> Currently, only video downloads are supported.

## Install

```bash
git clone https://github.com/Ladvix/vk-downloader.git
cd vk-downloader
pip install -r requirements.txt
```

## Usage

```python
import asyncio
from src.downloader import VkDownloader

async def main():
    async with VkDownloader() as dl:
        await dl.download_video('') # Paste here video_id

if __name__ == '__main__':
    asyncio.run(main())
```

> [!IMPORTANT]
> By default, the video is downloaded in the best quality.

## Configuration

In the config.py contains the IDs and secrets of official VK clients. You can create your own app and use its ID and secret.

```python
VK_APPS = {
    'web': {
        'client_id': 6287487,
        'client_secret': 'QbYic1K3lEV5kTGiqlq2'
    },
    'mvk': {
        'client_id': 7879029,
        'client_secret': 'aR5NKGmm03GYrCiNKsaw'
    },
    'messenger': {
        'client_id': 51745158,
        'client_secret': 'IjjCNl4L4Tf5QZEXIHKK'
    },
    'video_web': {
        'client_id': 52461373,
        'client_secret': 'o557NLIkAErNhakXrQ7A'
    },
    'video_mvk': {
        'client_id': 52649896,
        'client_secret': 'WStp4ihWG4l3nmXZgIbC'
    }
}
```