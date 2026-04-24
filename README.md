# VK-Downloader

A simple media downloader from the website vk.ru

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
from vk_downloader.main import VkDownloader

downloader = VkDownloader()
downloader.download_video(
    video_id='...', 
    output_filename='video.mp4',
    quality='2160p' # 2160p -> 1440p -> 1080p -> 720p -> 480p -> 360p -> 240p -> 144p
)
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