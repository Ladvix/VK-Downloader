import asyncio
from src.downloader import VkDownloader

async def main():
    async with VkDownloader() as dl:
        await dl.download_video('-236331347_456239111') # Paste here video_id

if __name__ == '__main__':
    asyncio.run(main())