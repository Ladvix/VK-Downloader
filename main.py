import time
import requests
from typing import Dict, Optional
from config import VK_APPS

class VkDownloader():
    def __init__(self):
        self.base_url = 'https://vkvideo.ru/'
        self.api_url = 'https://api.vkvideo.ru/'
        self.auth_service_url = 'https://login.vk.com'
        self.api_ver = '5.275'
        self.app_id = VK_APPS['web']['client_id']
        self.client_id = VK_APPS['video_web']['client_id']
        self.client_secret = VK_APPS['video_web']['client_secret']
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'

        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
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
        self.get_anonym_token()

    def get_anonym_token(self) -> Optional[str]:
        response = self.session.post(
            self.auth_service_url,
            params={
                'act': 'get_anonym_token'
            }, 
            data={
                'version': 1,
                'app_id': self.app_id,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scopes': 'audio_anonymous,video_anonymous,photos_anonymous,profile_anonymous',
                'isApiOauthAnonymEnabled': False
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data['data']['access_token']
            return self.access_token
        else:
            print(f'[{response.status_code}] Unknown error when receiving anonym token')
            return None

    def get_video_data(
        self,
        video_id: str,
        video_fields: Optional[str] = 'files,image,is_favorite,subtitles,timeline_thumbs,trailer,volume_multiplier'
    ) -> Optional[Dict]:
        if not self.access_token:
            print('[!] This method requires authorization')
            return None

        response = self.session.post(
            f'{self.api_url}/method/video.getByIds',
            params={
                'v': self.api_ver,
                'client_id': self.client_id
            }, 
            data={
                'videos': video_id,
                'video_fields': video_fields,
                'access_token': self.access_token
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data['response']['items']
        else:
            print(response.text)
            print(f'[{response.status_code}] Unknown error when receiving video data')
            return None

    def download_video(
        self,
        video_id: str,
        quality: Optional[str] = None,
        video_fields: Optional[str] = None,
        output_filename: Optional[str] = None
    ) -> bool:
        if video_fields:
            video_data = self.get_video_data(video_id, video_fields)
        else:
            video_data = self.get_video_data(video_id)

        if 'files' in video_data[0]:
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
                    return False

            url = video_data[0]['files'][quality]
            response = self.session.get(url, stream=True)
            downloaded_bytes = 0
            size = int(response.headers.get('Content-Length'))/1024**2
            time_start = time.perf_counter()
            with open(output_filename if output_filename else f'video_{video_id}.mp4', 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)

                        elapsed_time = time.perf_counter() - time_start
                        mb = downloaded_bytes / (1024 * 1024)
                        speed = mb / elapsed_time if elapsed_time > 0 else 0
                        print(f'[i] {mb:.2f}/{size:.2f} MB | Speed: {speed:.2f} MB/s', end='\r', flush=True)
        else:
            print('[-] Server did not send links to the video')

if __name__ == '__main__':
    downloader = VkDownloader()
    downloader.download_video('-168455361_456256684')