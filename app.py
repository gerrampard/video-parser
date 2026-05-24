#!/usr/bin/env python3
"""
视频解析下载 Gradio 应用
支持抖音、哔哩哔哩、小红书、快手、好看视频的解析下载和在线播放
"""

import os
import time
import random
import string
import base64
import requests
import subprocess
import tempfile
import gradio as gr
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ==================== 认证相关 ====================

class VigenereCipher:
    """用于 API 认证的加密类"""

    def __init__(self, timestamp):
        self.key = self.timestamp_to_letters(timestamp)

    @staticmethod
    def timestamp_to_letters(timestamp):
        digits_to_letters = 'abcdefghijklmnopqrstuvwxyz'
        result = ''
        for char in timestamp:
            if char.isdigit():
                index = int(char)
                if 0 <= index < len(digits_to_letters):
                    result += digits_to_letters[index]
                else:
                    result += 'a'
            else:
                result += 'a'
        return result

    def vigenere_encrypt(self, text):
        encrypted = []
        key_index = 0
        for char in text:
            if char.isalpha():
                shift = 65 if char.isupper() else 97
                key_char = self.key[key_index % len(self.key)].lower()
                key_shift = ord(key_char) - 97
                encrypted_char = chr((ord(char) - shift + key_shift) % 26 + shift)
                encrypted.append(encrypted_char)
                key_index += 1
            else:
                encrypted.append(char)
        return ''.join(encrypted)


def generate_complex_text(length=32):
    """生成随机字符串用于认证"""
    characters = string.ascii_letters
    return ''.join(random.choice(characters) for _ in range(length))


def get_auth_headers(client_id: str = "gradio-client"):
    """生成带有认证信息的请求头"""
    timestamp = str(int(time.time() * 1000))
    original_text = generate_complex_text()
    cipher = VigenereCipher(timestamp)
    encrypted_text = cipher.vigenere_encrypt(original_text)

    return {
        'X-Timestamp': timestamp,
        'X-GCLT-Text': original_text,
        'X-EGCT-Text': encrypted_text,
        'WX-OPEN-ID': client_id,
        'Content-Type': 'application/json'
    }


# ==================== URL 处理 ====================

def clean_url(url: str) -> str:
    """清理 URL，只保留必要的参数"""
    parsed = urlparse(url)

    # 小红书链接处理
    if 'xiaohongshu.com' in parsed.netloc:
        query_params = parse_qs(parsed.query)
        essential_params = {}
        if 'xsec_token' in query_params:
            essential_params['xsec_token'] = query_params['xsec_token'][0]
        if 'xsec_source' in query_params:
            essential_params['xsec_source'] = query_params['xsec_source'][0]
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if essential_params:
            clean_url += '?' + urlencode(essential_params)
        return clean_url

    # 快手链接处理
    if 'kuaishou.com' in parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    return url


def detect_platform(url: str) -> str:
    """根据 URL 自动检测平台"""
    url_lower = url.lower()
    if 'douyin.com' in url_lower or 'iesdouyin.com' in url_lower:
        return "抖音"
    elif 'bilibili.com' in url_lower or 'b23.tv' in url_lower:
        return "哔哩哔哩"
    elif 'xiaohongshu.com' in url_lower or 'xhslink.com' in url_lower:
        return "小红书"
    elif 'kuaishou.com' in url_lower:
        return "快手"
    elif 'haokan.baidu.com' in url_lower:
        return "好看视频"
    return "自动检测"


# ==================== API 调用 ====================

# Qwen3-VL API 配置（从环境变量读取）
QWEN_API_BASE_URL = os.getenv('QWEN_API_BASE_URL', 'https://api-inference.modelscope.cn/v1')
QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
QWEN_MODEL_ID = os.getenv('QWEN_MODEL_ID', 'Qwen/Qwen3-VL-8B-Instruct')
MAX_FRAMES = int(os.getenv('MAX_FRAMES', '6'))  # 提取帧数


class VideoClient:
    """视频解析下载客户端"""

    def __init__(self, server_url: str = "http://127.0.0.1:5001"):
        self.server_url = server_url.rstrip('/')
        self.download_dir = os.path.join(os.path.dirname(__file__), "downloads")
        self.cache_dir = os.path.join(os.path.dirname(__file__), "cache")
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    def download_cover(self, cover_url: str, video_id: str, referer: str = None) -> Optional[str]:
        """
        下载封面图片到本地缓存

        Returns:
            本地文件路径或 None
        """
        if not cover_url:
            return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
        }
        if referer:
            headers['Referer'] = referer

        # 生成缓存文件名
        safe_id = "".join(c for c in video_id if c.isalnum())[:30] or "cover"
        cache_path = os.path.join(self.cache_dir, f"{safe_id}_cover.jpg")

        # 如果已经缓存过，直接返回
        if os.path.exists(cache_path):
            return cache_path

        try:
            response = requests.get(cover_url, headers=headers, timeout=30)
            response.raise_for_status()

            with open(cache_path, 'wb') as f:
                f.write(response.content)

            return cache_path
        except Exception as e:
            print(f"下载封面失败: {e}")
            return None

    def parse_video(self, video_url: str) -> Tuple[bool, dict, str]:
        """
        解析视频链接

        Returns:
            (success, data, message)
        """
        api_url = f"{self.server_url}/api/parse"
        clean_video_url = clean_url(video_url)
        payload = {"text": clean_video_url}

        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=get_auth_headers(),
                timeout=60
            )
            result = response.json()

            if result.get('succ') or result.get('retcode') == 200:
                data = result.get('data', {})
                return True, data, "解析成功"
            else:
                return False, {}, result.get('retdesc', '解析失败')

        except requests.exceptions.ConnectionError:
            return False, {}, "无法连接到服务器，请确保后端服务正在运行 (端口 5001)"
        except requests.exceptions.Timeout:
            return False, {}, "请求超时，请稍后重试"
        except Exception as e:
            return False, {}, f"解析出错: {str(e)}"

    def get_download_url(self, video_url: str, video_id: str) -> Optional[str]:
        """获取下载链接"""
        api_url = f"{self.server_url}/api/download"
        payload = {
            "video_url": video_url,
            "video_id": video_id
        }

        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=get_auth_headers(),
                timeout=60
            )
            result = response.json()

            if result.get('succ') or result.get('retcode') == 200:
                return result.get('data', {}).get('download_url')
            return None
        except:
            return None

    def download_file(self, url: str, filename: str, referer: str = None,
                      progress_callback=None) -> Tuple[bool, str, str]:
        """
        下载文件到本地

        Returns:
            (success, filepath, message)
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        if referer:
            headers['Referer'] = referer

        filepath = os.path.join(self.download_dir, filename)

        try:
            response = requests.get(url, headers=headers, stream=True, timeout=180)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = downloaded_size / total_size
                            progress_callback(progress)

            size_mb = os.path.getsize(filepath) / 1024 / 1024
            return True, filepath, f"下载完成 ({size_mb:.1f} MB)"

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return False, "", f"下载失败: {str(e)}"

    def merge_video_audio(self, video_path: str, audio_path: str,
                          output_path: str) -> Tuple[bool, str]:
        """使用 ffmpeg 合并视频和音频"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # 删除临时文件
                os.remove(video_path)
                os.remove(audio_path)
                return True, "合并成功"
            else:
                return False, f"合并失败: {result.stderr}"
        except FileNotFoundError:
            return False, "未安装 ffmpeg，请先安装 ffmpeg"


# ==================== Gradio 界面函数 ====================

# 全局客户端实例
client = VideoClient()

# 存储当前解析的视频信息
current_video_info = {}


def parse_video(url: str, platform: str) -> Tuple[str, str, str, str, str]:
    """
    解析视频

    Returns:
        (status_message, title, cover_image, video_url, platform_detected)
    """
    global current_video_info

    if not url or not url.strip():
        return "请输入视频链接", "", None, "", ""

    url = url.strip()

    # 自动检测平台
    if platform == "自动检测":
        detected = detect_platform(url)
        if detected == "自动检测":
            detected = "未知平台"
        platform = detected

    success, data, message = client.parse_video(url)

    if success:
        current_video_info = data
        current_video_info['original_url'] = url

        title = data.get('title', '无标题')
        cover_url = data.get('cover_url', '')
        video_url = data.get('video_url', '')
        video_id = data.get('video_id', 'unknown')
        platform_name = data.get('platform', platform)

        # 获取 referer 用于下载封面
        referer = None
        if 'douyin.com' in url:
            referer = 'https://www.douyin.com/'
        elif 'bilibili.com' in url:
            referer = url
        elif 'xiaohongshu.com' in url:
            referer = 'https://www.xiaohongshu.com/'
        elif 'kuaishou.com' in url:
            referer = 'https://www.kuaishou.com/'
        elif 'haokan.baidu.com' in url:
            referer = 'https://haokan.baidu.com/'

        # 下载封面到本地（避免 Gradio 直接访问外部 URL 失败）
        cover_local_path = None
        if cover_url:
            cover_local_path = client.download_cover(cover_url, video_id, referer)

        status = f"解析成功 - {platform_name}"
        return status, title, cover_local_path, video_url, platform_name
    else:
        current_video_info = {}
        return f"解析失败: {message}", "", None, "", ""


def play_video(progress=gr.Progress()) -> Tuple[str, str]:
    """
    播放视频（先下载到本地缓存再播放）

    Returns:
        (video_path, status_message)
    """
    global current_video_info

    if not current_video_info:
        return None, "请先解析视频"

    video_url = current_video_info.get('video_url', '')
    audio_url = current_video_info.get('audio_url', '')
    video_id = current_video_info.get('video_id', 'video')
    platform = current_video_info.get('platform', '')
    original_url = current_video_info.get('original_url', '')

    if not video_url:
        return None, "未找到视频链接"

    # 获取 referer
    referer = None
    if 'douyin.com' in original_url:
        referer = 'https://www.douyin.com/'
    elif 'bilibili.com' in original_url:
        referer = original_url
    elif 'xiaohongshu.com' in original_url:
        referer = 'https://www.xiaohongshu.com/'
    elif 'kuaishou.com' in original_url:
        referer = 'https://www.kuaishou.com/'
    elif 'haokan.baidu.com' in original_url:
        referer = 'https://haokan.baidu.com/'

    # 生成缓存文件名
    safe_id = "".join(c for c in video_id if c.isalnum())[:30] or "video"
    cache_path = os.path.join(client.cache_dir, f"{safe_id}_play.mp4")

    # 如果已经缓存过，直接返回
    if os.path.exists(cache_path):
        return cache_path, "加载完成（使用缓存）"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }
    if referer:
        headers['Referer'] = referer

    # B站视频需要分别下载音视频再合并
    if platform == '哔哩哔哩' and audio_url:
        video_temp = os.path.join(client.cache_dir, f"{safe_id}_video.m4s")
        audio_temp = os.path.join(client.cache_dir, f"{safe_id}_audio.m4s")

        try:
            # 下载视频轨道
            progress(0, desc="下载视频轨道...")
            response = requests.get(video_url, headers=headers, stream=True, timeout=180)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(video_temp, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress(downloaded_size / total_size * 0.4, desc=f"下载视频轨道: {downloaded_size * 100 // total_size}%")

            # 下载音频轨道
            progress(0.4, desc="下载音频轨道...")
            response = requests.get(audio_url, headers=headers, stream=True, timeout=180)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(audio_temp, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress(0.4 + downloaded_size / total_size * 0.4, desc=f"下载音频轨道: {downloaded_size * 100 // total_size}%")

            # 合并音视频
            progress(0.8, desc="合并音视频...")
            success, msg = client.merge_video_audio(video_temp, audio_temp, cache_path)

            if success:
                progress(1.0, desc="加载完成")
                return cache_path, "加载完成"
            else:
                return None, f"合并失败: {msg}"

        except Exception as e:
            # 清理临时文件
            for temp_file in [video_temp, audio_temp, cache_path]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return None, f"加载失败: {str(e)}"

    else:
        # 其他平台直接下载视频
        try:
            progress(0, desc="正在加载视频...")
            response = requests.get(video_url, headers=headers, stream=True, timeout=180)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress(downloaded_size / total_size, desc=f"加载中: {downloaded_size * 100 // total_size}%")

            progress(1.0, desc="加载完成")
            return cache_path, "加载完成"

        except Exception as e:
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None, f"加载失败: {str(e)}"


def download_video(progress=gr.Progress()) -> Tuple[str, str]:
    """
    下载视频

    Returns:
        (filepath, status_message)
    """
    global current_video_info

    if not current_video_info:
        return None, "请先解析视频"

    video_url = current_video_info.get('video_url', '')
    audio_url = current_video_info.get('audio_url', '')
    video_id = current_video_info.get('video_id', 'video')
    title = current_video_info.get('title', 'video')
    platform = current_video_info.get('platform', '')
    original_url = current_video_info.get('original_url', '')

    if not video_url:
        return None, "未找到视频链接"

    # 清理文件名
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '.')).strip()
    if not safe_title:
        safe_title = video_id
    safe_title = safe_title[:50]

    # 获取 referer
    referer = None
    if 'douyin.com' in original_url:
        referer = 'https://www.douyin.com/'
    elif 'bilibili.com' in original_url:
        referer = original_url
    elif 'xiaohongshu.com' in original_url:
        referer = 'https://www.xiaohongshu.com/'
    elif 'kuaishou.com' in original_url:
        referer = 'https://www.kuaishou.com/'

    # B站视频需要分别下载音视频再合并
    if platform == '哔哩哔哩' and audio_url:
        progress(0, desc="下载视频轨道...")

        video_temp = os.path.join(client.download_dir, f"{safe_title}_video.m4s")
        audio_temp = os.path.join(client.download_dir, f"{safe_title}_audio.m4s")
        output_path = os.path.join(client.download_dir, f"{safe_title}.mp4")

        # 下载视频轨道
        def video_progress(p):
            progress(p * 0.4, desc=f"下载视频轨道: {p*100:.0f}%")

        success, _, msg = client.download_file(video_url, f"{safe_title}_video.m4s",
                                                referer, video_progress)
        if not success:
            return None, f"视频轨道下载失败: {msg}"

        progress(0.4, desc="下载音频轨道...")

        # 下载音频轨道
        def audio_progress(p):
            progress(0.4 + p * 0.4, desc=f"下载音频轨道: {p*100:.0f}%")

        success, _, msg = client.download_file(audio_url, f"{safe_title}_audio.m4s",
                                                referer, audio_progress)
        if not success:
            return None, f"音频轨道下载失败: {msg}"

        progress(0.8, desc="合并音视频...")

        # 合并音视频
        success, msg = client.merge_video_audio(video_temp, audio_temp, output_path)
        if not success:
            return None, msg

        progress(1.0, desc="完成")
        return output_path, f"下载完成: {os.path.basename(output_path)}"

    else:
        # 其他平台直接下载
        def download_progress(p):
            progress(p, desc=f"下载中: {p*100:.0f}%")

        filename = f"{safe_title}.mp4"
        success, filepath, msg = client.download_file(video_url, filename,
                                                       referer, download_progress)

        if success:
            return filepath, msg
        else:
            return None, msg


def get_video_duration(video_path: str) -> float:
    """获取视频时长（秒）"""
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ],
            capture_output=True,
            text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0


def extract_video_frames(video_path: str, num_frames: int = MAX_FRAMES) -> list:
    """
    从视频中提取关键帧

    Args:
        video_path: 视频文件路径
        num_frames: 要提取的帧数

    Returns:
        帧图片路径列表
    """
    duration = get_video_duration(video_path)
    if duration <= 0:
        duration = 60  # 默认假设60秒

    # 计算时间间隔
    interval = duration / (num_frames + 1)

    frames = []
    temp_dir = tempfile.mkdtemp(prefix='video_frames_')

    for i in range(num_frames):
        timestamp = interval * (i + 1)
        output_path = os.path.join(temp_dir, f'frame_{i:03d}.jpg')

        try:
            subprocess.run(
                [
                    'ffmpeg', '-y',
                    '-ss', str(timestamp),
                    '-i', video_path,
                    '-vframes', '1',
                    '-q:v', '2',
                    output_path
                ],
                capture_output=True,
                check=True
            )

            if os.path.exists(output_path):
                frames.append(output_path)

        except subprocess.CalledProcessError:
            pass

    return frames


def image_to_base64(image_path: str) -> str:
    """将图片转换为 base64 编码"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


def extract_video_content(progress=gr.Progress()) -> Tuple[str, str]:
    """
    提取视频内容描述

    Returns:
        (content_text, status_message)
    """
    global current_video_info

    if not current_video_info:
        return "", "请先解析视频"

    video_id = current_video_info.get('video_id', 'video')

    # 检查是否有缓存的视频文件
    safe_id = "".join(c for c in video_id if c.isalnum())[:30] or "video"
    cache_path = os.path.join(client.cache_dir, f"{safe_id}_play.mp4")

    if not os.path.exists(cache_path):
        return "", "请先点击「在线播放」加载视频后再提取内容"

    try:
        progress(0.1, desc="正在提取视频帧...")

        # 提取视频帧
        frames = extract_video_frames(cache_path, MAX_FRAMES)

        if not frames:
            return "", "无法提取视频帧，请确保已安装 ffmpeg"

        progress(0.3, desc=f"成功提取 {len(frames)} 帧，正在分析...")

        # 构建提示词
        prompt = f"""这是从一个视频中提取的 {len(frames)} 帧关键画面。
请根据这些画面，详细描述这个视频的内容，包括：
1. 视频中出现的人物或物体
2. 发生的事件或动作
3. 场景环境
4. 视频的主题或表达的意思
5. 视频的整体叙事或故事线

请用中文回答。"""

        # 构建消息内容
        content = [{'type': 'text', 'text': prompt}]

        for frame_path in frames:
            frame_base64 = image_to_base64(frame_path)
            content.append({
                'type': 'image_url',
                'image_url': {
                    'url': f'data:image/jpeg;base64,{frame_base64}'
                }
            })

        progress(0.4, desc="正在调用 AI 分析视频内容...")

        # 创建 API 客户端
        qwen_client = OpenAI(
            base_url=QWEN_API_BASE_URL,
            api_key=QWEN_API_KEY,
        )

        # 调用 API（非流式，方便处理）
        response = qwen_client.chat.completions.create(
            model=QWEN_MODEL_ID,
            messages=[{
                'role': 'user',
                'content': content,
            }],
            stream=False
        )

        progress(0.9, desc="分析完成")

        result = response.choices[0].message.content

        # 清理临时文件
        for frame_path in frames:
            try:
                os.remove(frame_path)
            except Exception:
                pass

        try:
            os.rmdir(os.path.dirname(frames[0]))
        except Exception:
            pass

        progress(1.0, desc="提取完成")

        return result, "视频内容提取成功"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return "", f"提取失败: {str(e)}"


def clear_all():
    """清空所有内容"""
    global current_video_info
    current_video_info = {}
    return "", "自动检测", "", "", None, None, None, ""


# ==================== Gradio 界面 ====================

# 示例视频链接
EXAMPLE_URLS = {
    "抖音": "https://www.douyin.com/note/7580598241298069157",
    "哔哩哔哩": "https://www.bilibili.com/video/BV1TaqYBcEJc",
    "小红书": "https://www.xiaohongshu.com/explore/68ab2dd1000000001c0045d0?app_platform=android&ignoreEngage=true&app_version=9.13.1&share_from_user_hidden=true&xsec_source=app_share&type=video&xsec_token=CBLONm9tab3493BJUXCtvU8ScDzfYqa3cGwJstW8eSF3Y=&author_share=1&xhsshare=&shareRedId=OD04RDk1PUw2NzUyOTgwNjc7OThISj5O&apptime=1766754031&share_id=46cc1edc70704cd1ae467afb90d0e8e6&share_channel=wechat&wechatWid=94270060b457f72e6e3a2df13090e1d6&wechatOrigin=menu",
    "快手": "https://www.kuaishou.com/short-video/3x8zha3ipq6bg8q?authorId=3xcyp2v85enrv7w&streamSource=find&area=homexxbrilliant",
    "好看视频": "https://haokan.baidu.com/v?vid=13766973483433940333&tab=recommend",
}


def fill_example(platform: str):
    """填充示例链接"""
    url = EXAMPLE_URLS.get(platform, "")
    return url, platform


def create_app():
    """创建 Gradio 应用"""

    with gr.Blocks(
        title="视频解析下载器",
        theme=gr.themes.Soft(),
        css="""
        .container { max-width: 1200px; margin: auto; }
        .header { text-align: center; margin-bottom: 20px; }
        .status-box { padding: 10px; border-radius: 5px; }
        .example-btn { min-width: 80px; }
        """
    ) as app:

        gr.Markdown(
            """
            # 视频解析下载器
            支持抖音、哔哩哔哩、小红书、快手、好看视频的解析、下载和在线播放
            """,
            elem_classes=["header"]
        )

        with gr.Row():
            with gr.Column(scale=2):
                # 输入区域
                url_input = gr.Textbox(
                    label="视频链接",
                    placeholder="请输入视频链接，支持抖音、B站、小红书、快手、好看视频...",
                    lines=2
                )

                # 示例链接按钮
                gr.Markdown("**示例链接** (点击自动填充)")
                with gr.Row():
                    douyin_btn = gr.Button("抖音", size="sm", elem_classes=["example-btn"])
                    bilibili_btn = gr.Button("哔哩哔哩", size="sm", elem_classes=["example-btn"])
                    xiaohongshu_btn = gr.Button("小红书", size="sm", elem_classes=["example-btn"])
                with gr.Row():
                    kuaishou_btn = gr.Button("快手", size="sm", elem_classes=["example-btn"])
                    haokan_btn = gr.Button("好看视频", size="sm", elem_classes=["example-btn"])

                with gr.Row():
                    platform_dropdown = gr.Dropdown(
                        label="平台选择",
                        choices=["自动检测", "抖音", "哔哩哔哩", "小红书", "快手", "好看视频"],
                        value="自动检测",
                        interactive=True
                    )

                with gr.Row():
                    parse_btn = gr.Button("解析视频", variant="primary", size="lg")
                    clear_btn = gr.Button("清空", variant="secondary", size="lg")

                # 状态显示
                status_output = gr.Textbox(
                    label="状态",
                    interactive=False,
                    elem_classes=["status-box"]
                )

                # 视频信息
                title_output = gr.Textbox(
                    label="视频标题",
                    interactive=False
                )

                platform_output = gr.Textbox(
                    label="识别平台",
                    interactive=False
                )

            with gr.Column(scale=3):
                # 封面图片
                cover_output = gr.Image(
                    label="视频封面",
                    height=300
                )

                # 操作按钮
                with gr.Row():
                    play_btn = gr.Button("在线播放", variant="primary")
                    download_btn = gr.Button("下载视频", variant="secondary")

                # 视频播放器
                video_output = gr.Video(
                    label="视频播放",
                    height=400
                )

                # 下载文件
                download_output = gr.File(
                    label="下载文件",
                    visible=True
                )

                # 视频内容提取
                extract_btn = gr.Button("AI提取视频内容", variant="secondary")
                content_output = gr.Textbox(
                    label="视频内容描述",
                    lines=10,
                    max_lines=20,
                    interactive=False,
                    placeholder="点击「AI提取视频内容」按钮，AI将分析视频并生成内容描述..."
                )

        # 隐藏的视频 URL 存储
        video_url_state = gr.State("")

        # 示例链接按钮事件绑定
        douyin_btn.click(
            fn=lambda: fill_example("抖音"),
            inputs=[],
            outputs=[url_input, platform_dropdown]
        )
        bilibili_btn.click(
            fn=lambda: fill_example("哔哩哔哩"),
            inputs=[],
            outputs=[url_input, platform_dropdown]
        )
        xiaohongshu_btn.click(
            fn=lambda: fill_example("小红书"),
            inputs=[],
            outputs=[url_input, platform_dropdown]
        )
        kuaishou_btn.click(
            fn=lambda: fill_example("快手"),
            inputs=[],
            outputs=[url_input, platform_dropdown]
        )
        haokan_btn.click(
            fn=lambda: fill_example("好看视频"),
            inputs=[],
            outputs=[url_input, platform_dropdown]
        )

        # 事件绑定
        parse_btn.click(
            fn=parse_video,
            inputs=[url_input, platform_dropdown],
            outputs=[status_output, title_output, cover_output, video_url_state, platform_output]
        )

        play_btn.click(
            fn=play_video,
            inputs=[],
            outputs=[video_output, status_output]
        )

        download_btn.click(
            fn=download_video,
            inputs=[],
            outputs=[download_output, status_output]
        )

        extract_btn.click(
            fn=extract_video_content,
            inputs=[],
            outputs=[content_output, status_output]
        )

        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[url_input, platform_dropdown, status_output, title_output,
                    cover_output, video_output, download_output, content_output]
        )

        # 使用说明
        gr.Markdown(
            """
            ---
            ### 使用说明
            1. **粘贴链接**: 将视频分享链接粘贴到输入框，或点击上方示例按钮快速填充
            2. **选择平台**: 可自动检测或手动选择
            3. **解析视频**: 点击解析获取视频信息
            4. **在线播放**: 直接播放视频（B站视频需下载后播放）
            5. **下载视频**: 下载视频到本地
            6. **AI提取内容**: 点击在线播放后，可使用AI分析视频内容

            ### 支持的平台
            - **抖音**: douyin.com, iesdouyin.com
            - **哔哩哔哩**: bilibili.com, b23.tv
            - **小红书**: xiaohongshu.com, xhslink.com
            - **快手**: kuaishou.com
            - **好看视频**: haokan.baidu.com

            ### 注意事项
            - 请确保后端服务 (端口 5001) 正在运行
            - B站视频为音视频分离，需要 ffmpeg 支持
            - 下载的视频保存在 downloads 目录
            - AI提取内容需要先播放视频（加载到本地缓存）
            """
        )

    return app


# ==================== 主程序 ====================

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
