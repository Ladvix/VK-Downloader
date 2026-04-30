import time
import httpx
import asyncio
from typing import Dict, Optional
from .config import VK_APPS

class VkDownloader():
    def __init__(self):
        self.base_url = 'https://vkvideo.ru'
        self.api_url = 'https://api.vkvideo.ru'
        self.auth_service_url = 'https://login.vk.com'
        self.api_ver = '5.275'
        self.app_id = VK_APPS['web']['client_id']
        self.client_id = VK_APPS['video_web']['client_id']
        self.client_secret = VK_APPS['video_web']['client_secret']
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'
        self.token_expired_at = 0
        self._lock = asyncio.Lock()

        self.chunk_size = 10 * 1024**2
        self.semaphore = asyncio.Semaphore(10)

        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        }

        self.media_qualities = ['mp4_2160', 'mp4_1440', 'mp4_1080', 'mp4_720', 'mp4_480', 'mp4_360', 'mp4_240', 'mp4_144']
        self.access_token = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=None)
        await self.get_anonym_token()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.aclose()

    async def _check_token(self):
        if not self.access_token or time.time() >= self.token_expired_at:
            async with self._lock:
                if not self.access_token or time.time() >= self.token_expired_at:
                    await self.get_anonym_token()
    
    def _print_progress(self, current, total, start_time):
        elapsed = time.perf_counter() - start_time
        mb = current / 1024**2
        total_mb = total / 1024**2
        speed = mb / elapsed if elapsed > 0 else 0
        print(f'[i] {mb:.2f}/{total_mb:.2f} MB | Speed: {speed:.2f} MB/s', end='\r', flush=True)

    async def get_anonym_token(self) -> Optional[str]:
        params = {
            'act': 'get_anonym_token'
        }
        data = {
            'version': 1,
            'app_id': self.app_id,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scopes': 'audio_anonymous,video_anonymous,photos_anonymous,profile_anonymous',
            'isApiOauthAnonymEnabled': False
        }

        try:
            response = await self.client.post(self.auth_service_url, params=params, data=data)

            if response.status_code == 200:
                data = response.json()
                self.access_token = data['data']['access_token']
                self.token_expired_at = data['data'].get('expired_at', 0) 
                return self.access_token
            else:
                print(f'[{response.status_code}] Unknown error when receiving anonym token')
                return None

        except httpx.HTTPError as e:
            print(f'[-] Error receiving anonym token: {e}')
            return

    async def get_video_data(
        self,
        video_id: str,
        video_fields: Optional[str] = 'files,image,is_favorite,subtitles,timeline_thumbs,trailer,volume_multiplier'
    ) -> Optional[Dict]:
        if not self.access_token:
            print('[!] This method requires authorization')
            return None
        else:
            await self._check_token()

        params = {
            'v': self.api_ver,
            'client_id': self.client_id
        }
        data={
            'videos': video_id,
            'video_fields': video_fields,
            'access_token': self.access_token
        }

        try:
            response = await self.client.post(f'{self.api_url}/method/video.getByIds', params=params, data=data)

            if response.status_code == 200:
                data = response.json()
                return data['response']['items']
            else:
                print(response.text)
                print(f'[{response.status_code}] Unknown error when receiving video data')
                return None

        except httpx.HTTPError as e:
            print(f'[-] Error getting video data: {e}')
            return

    async def get_video_source_url(
        self,
        video_id: str,
        video_fields: Optional[str] = None,
        quality: Optional[str] = None
    ) -> Optional[str]:
        if video_fields:
            video_data = await self.get_video_data(video_id, video_fields)
        else:
            video_data = await self.get_video_data(video_id)

        if not video_data:
            return None

        if not quality:
            media_qualities = video_data[0]['files'].keys()
            for q in self.media_qualities:
                if q in media_qualities:
                    quality = q
                    break
        else:
            if quality.endswith('p'): quality = quality[:-1]
            if not quality.startswith('mp4_'): quality = f'mp4_{quality}'
            if quality not in self.media_qualities:
                print('[-] Incorrect media quality')
                return None

        if 'files' in video_data[0]:
            url = video_data[0]['files'][quality]
            return url
        else:
            print('[-] Server did not send links to the video')
            return None

    async def download_video_bytes(
        self,
        url: str,
        start: str,
        end: str,
        output_filename: str,
        progress: Dict
    ):
        headers = self.headers.copy()
        headers['Range'] = f'bytes={start}-{end}'

        async with self.semaphore:
            async with self.client.stream('GET', url, headers=headers) as response:
                with open(output_filename, 'rb+') as f:
                    f.seek(start)
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            f.write(chunk)
                            progress['current'] += len(chunk)
                            self._print_progress(
                                progress['current'],
                                progress['total_size'],
                                progress['start_time']
                            )

    async def download_video(
        self,
        video_id: str,
        video_fields: Optional[str] = None,
        quality: Optional[str] = None,
        output_filename: Optional[str] = None,
        mode: Optional[str] = None
    ):
        url = await self.get_video_source_url(video_id, video_fields, quality)
        if not url: return

        try:
            if not mode:
                async with self.client.stream('GET', url) as response:
                    downloaded_bytes = 0
                    total_size = int(response.headers.get('Content-Length'))/1024**2
                    time_start = time.perf_counter()

                    output_filename = output_filename if output_filename else f'video_{video_id}.mp4'
                    with open(output_filename, 'wb') as f:
                        async for chunk in response.aiter_bytes():
                            if chunk:
                                f.write(chunk)
                                downloaded_bytes += len(chunk)

                                elapsed_time = time.perf_counter() - time_start
                                mb = downloaded_bytes / (1024 * 1024)
                                speed = mb / elapsed_time if elapsed_time > 0 else 0
                                print(f'[i] {mb:.2f}/{total_size:.2f} MB | Speed: {speed:.2f} MB/s', end='\r', flush=True)
            
            elif mode == 'quick':
                response = await self.client.head(url)
                total_size = int(response.headers.get('Content-Length'))
                progress = {
                    'current': 0,
                    'total_size': total_size,
                    'start_time': time.perf_counter()
                }

                output_filename = output_filename if output_filename else f'video_{video_id}.mp4'
                with open(output_filename, 'wb') as f:
                    f.truncate(total_size)

                tasks = []
                for start in range(0, total_size, self.chunk_size):
                    end = min(start + self.chunk_size - 1, total_size - 1)
                    tasks.append(self.download_video_bytes(url, start, end, output_filename, progress))

                results = await asyncio.gather(*tasks)

        except httpx.HTTPError as e:
            print(f'\n[-] Error downloading video: {e}')
            return

    async def stream_video(
        self,
        video_id: str,
        video_fields: Optional[str] = None,
        quality: Optional[str] = None,
        reconnect_every_mb: int = 10
    ):
        url = await self.get_video_source_url(video_id, video_fields, quality)
        if not url: return

        response = await self.client.head(url)
        total_size = int(response.headers.get('Content-Length', 0))

        current_byte = 0
        chunk_limit = reconnect_every_mb * 1024**2

        try:
            while current_byte < total_size:
                end_byte = min(current_byte + chunk_limit - 1, total_size - 1)
                headers = self.headers.copy()
                headers['Range'] = f'bytes={current_byte}-{end_byte}'

                async with self.client.stream('GET', url, headers=headers) as response:
                    bytes_in_this_connection = 0

                    async for chunk in response.aiter_bytes():
                        if chunk:
                            yield chunk
                            current_byte += len(chunk)
                            bytes_in_this_connection += len(chunk)

                            if bytes_in_this_connection >= chunk_limit:
                                break

        except httpx.HTTPError as e:
            print(f'[-] Error streaming video: {e}')
            return