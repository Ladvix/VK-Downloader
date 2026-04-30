import asyncio
from src.downloader import VkDownloader

async def main():
    async with VkDownloader() as dl:
        await dl.download_video('-231263435_456240163') # Paste here video_id

if __name__ == '__main__':
    asyncio.run(main())