"""
图片处理类（Python 3.11+ 版）
效果: 对图片的下载、识别、去重、分类、文件管理等

配置相关方法
    __init__: 初始化图片处理器配置

图片识别方法
    get_image_info: 从字节数据中提取图片元信息
    _identify_file_type_by_magic: 根据文件头魔数识别文件类型

图片下载方法
    download_image: 下载文件并保存到本地目录
    batch_download_from_api: 从多个API批量下载图片
    sizeof_url_image: 获取远程图片尺寸与元信息（不保存）
    is_image_accessible: 检查URL是否可访问

文件管理方法
    correct_file_extension: 根据魔数修正文件扩展名
    batch_correct_extensions: 批量修正目录中所有文件的扩展名
    list_files_in_directory: 列出目录下所有文件
    deduplicate_by_phash_optimized: 优化的基于感知哈希去重方法
    filter_images_by_size: 按尺寸过滤图像文件
    classify_image_by_orientation: 按方向分类图像（横向/竖向）
    move_file: 移动文件
    unblock_file: 解除Windows安全标记锁定

功能说明:
- 支持全类型文件魔数识别
- 支持手动处理Location重定向的安全下载
- 支持自动重命名、去重、分类等功能
- 支持多线程并行处理提高效率
- 支持图片尺寸过滤和方向分类
- 具备损坏图片修复功能

使用类库:
    Pillow(PIL):
        安装: pip install Pillow
    imagehash:
        安装: pip install imagehash
    httpx:
        安装: pip install httpx
"""
import os
import json
import httpx
import shutil
import logging
import threading
import imagehash
import multiprocessing

from io import BytesIO
from PIL import Image, UnidentifiedImageError
from hashlib import md5
from typing import Callable, List, Dict, Any
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    图片与文件处理工具类，专为高可靠下载与文件识别设计。
    """

    # --- 常量定义 ---
    Image.MAX_IMAGE_PIXELS = None
    Image.LOAD_TRUNCATED_IMAGES = True

    # 文件类型标识（统一小写英文）
    FILE_TYPE_PNG = 'png'
    FILE_TYPE_JPEG = 'jpeg'
    FILE_TYPE_GIF = 'gif'
    FILE_TYPE_BMP = 'bmp'
    FILE_TYPE_TIFF = 'tiff'
    FILE_TYPE_WEBP = 'webp'
    FILE_TYPE_AVIF = 'avif'
    FILE_TYPE_ICO = 'ico'
    FILE_TYPE_PSD = 'psd'
    FILE_TYPE_PDF = 'pdf'
    FILE_TYPE_DOC = 'doc'
    FILE_TYPE_DOCX = 'docx'
    FILE_TYPE_HTML = 'html'
    FILE_TYPE_MP3 = 'mp3'
    FILE_TYPE_WAV = 'wav'
    FILE_TYPE_FLAC = 'flac'
    FILE_TYPE_MP4 = 'mp4'
    FILE_TYPE_AVI = 'avi'
    FILE_TYPE_MOV = 'mov'
    FILE_TYPE_MKV = 'mkv'
    FILE_TYPE_ZIP = 'zip'
    FILE_TYPE_RAR = 'rar'
    FILE_TYPE_7Z = '7z'
    FILE_TYPE_EXE = 'exe'
    FILE_TYPE_ELF = 'elf'
    FILE_TYPE_PY = 'py'
    FILE_TYPE_PL = 'pl'
    FILE_TYPE_PHP = 'php'
    FILE_TYPE_CPP = 'cpp'
    FILE_TYPE_SH = 'sh'

    # 扩展名映射
    EXTENSION_MAPPING: dict[str, str] = {
        FILE_TYPE_PNG: '.png',
        FILE_TYPE_JPEG: '.jpg',
        FILE_TYPE_GIF: '.gif',
        FILE_TYPE_BMP: '.bmp',
        FILE_TYPE_TIFF: '.tiff',
        FILE_TYPE_WEBP: '.webp',
        FILE_TYPE_AVIF: '.avif',
        FILE_TYPE_ICO: '.ico',
        FILE_TYPE_PSD: '.psd',
        FILE_TYPE_PDF: '.pdf',
        FILE_TYPE_DOC: '.doc',
        FILE_TYPE_DOCX: '.docx',
        FILE_TYPE_HTML: '.html',
        FILE_TYPE_MP3: '.mp3',
        FILE_TYPE_WAV: '.wav',
        FILE_TYPE_FLAC: '.flac',
        FILE_TYPE_MP4: '.mp4',
        FILE_TYPE_AVI: '.avi',
        FILE_TYPE_MOV: '.mov',
        FILE_TYPE_MKV: '.mkv',
        FILE_TYPE_ZIP: '.zip',
        FILE_TYPE_RAR: '.rar',
        FILE_TYPE_7Z: '.7z',
        FILE_TYPE_EXE: '.exe',
        FILE_TYPE_ELF: '.elf',
        FILE_TYPE_PY: '.py',
        FILE_TYPE_PL: '.pl',
        FILE_TYPE_PHP: '.php',
        FILE_TYPE_CPP: '.cpp',
        FILE_TYPE_SH: '.sh',
    }

    # 魔数定义（按匹配优先级排序，长前缀优先）
    MAGIC_NUMBERS: list[tuple[bytes, str]] = [
        (b'PK\x03\x04', FILE_TYPE_ZIP),
        (b'PK\x05\x06', FILE_TYPE_ZIP),
        (b'PK\x07\x08', FILE_TYPE_ZIP),
        (b'Rar!\x1A\x07\x00', FILE_TYPE_RAR),
        (b'Rar!\x1A\x07\x01\x00', FILE_TYPE_RAR),
        (b'7z\xBC\xAF\x27\x1C', FILE_TYPE_7Z),
        (b'\x25\x50\x44\x46', FILE_TYPE_PDF),
        (b'\x4D\x5A', FILE_TYPE_EXE),
        (b'\x7F\x45\x4C\x46', FILE_TYPE_ELF),
        (b'\x00\x00\x00\x1cftypavif', FILE_TYPE_AVIF),
        (b'\x00\x00\x00\x18ftyp', FILE_TYPE_MP4),
        (b'\x00\x00\x00\x20ftyp', FILE_TYPE_MP4),
        (b'RIFF', FILE_TYPE_AVI),
        (b'ftypqt', FILE_TYPE_MOV),
        (b'moov', FILE_TYPE_MOV),
        (b'free', FILE_TYPE_MOV),
        (b'\x1A\x45\xDF\xA3', FILE_TYPE_MKV),
        (b'fLaC', FILE_TYPE_FLAC),
        (b'ID3', FILE_TYPE_MP3),
        (b'RIFF', FILE_TYPE_WAV),
        (b'RIFF', FILE_TYPE_WEBP),
        (b'\x89PNG', FILE_TYPE_PNG),
        (b'\xFF\xD8\xFF', FILE_TYPE_JPEG),
        (b'GIF89a', FILE_TYPE_GIF),
        (b'GIF87a', FILE_TYPE_GIF),
        (b'BM', FILE_TYPE_BMP),
        (b'\x49\x49\x2A\x00', FILE_TYPE_TIFF),
        (b'\x4D\x4D\x00\x2A', FILE_TYPE_TIFF),
        (b'8BPS', FILE_TYPE_PSD),
        (b'\x00\x00\x01\x00', FILE_TYPE_ICO),
        (b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', FILE_TYPE_DOC),
        (b'<!DOCTYP', FILE_TYPE_HTML),
        (b'<!doctype', FILE_TYPE_HTML),
        (b'#!/usr/bin/env python', FILE_TYPE_PY),
        (b'#!/usr/bin/python', FILE_TYPE_PY),
        (b'#!/bin/bash', FILE_TYPE_SH),
        (b'#!/bin/sh', FILE_TYPE_SH),
        (b'#!/usr/bin/perl', FILE_TYPE_PL),
        (b'<?php', FILE_TYPE_PHP),
        (b'#include <', FILE_TYPE_CPP),
        (b'\x23\x21', FILE_TYPE_PL),
        (b'\x23\x20', FILE_TYPE_SH),
        (b'\x23\x69', FILE_TYPE_PHP),
        (b'\x2A\x2A\x2A', FILE_TYPE_CPP),
        (b'\x0A', FILE_TYPE_PY),
    ]

    def __init__(self) -> None:
        pass

    # ────────────────────────────────────────────────────────
    # 工具方法（被其他方法调用）
    # ────────────────────────────────────────────────────────

    def _add_https_if_missing(self, url: str) -> str:
        """
        若 URL 无协议前缀，自动添加 'https://'。

        :param url: 原始 URL
        :return: 补全协议后的 URL
        """
        if not url.startswith(('http://', 'https://')):
            return 'https://' + url.lstrip('/')
        return url

    def _generate_fake_headers(self, url: str) -> dict[str, str]:
        if '://' in url:
            parts = url.split('/', 3)
            host = parts[2]
            path = '/' + (parts[3] if len(parts) > 3 else '')
        else:
            host = url
            path = '/'
        referer = f"https://{host}{path}"
        referer = 'https://www.google.com/'
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            # 'Referer': referer,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def _identify_file_type_by_magic(self, data: bytes) -> str | None:
        """
        根据文件头魔数识别文件类型。

        :param data: 文件前的若干个字节（建议 ≥32 字节）
        :return: 文件类型（如 'jpeg'），无法识别返回 None
        """
        print('magic:', data[:32])
        if not data or len(data) < 2:
            return None

        # 特殊处理 RIFF 容器格式
        if data.startswith(b'RIFF') and len(data) >= 12:
            riff_type = data[8:12]
            if riff_type == b'AVI ':
                return self.FILE_TYPE_AVI
            elif riff_type == b'WAVE':
                return self.FILE_TYPE_WAV
            elif riff_type == b'WEBP':
                return self.FILE_TYPE_WEBP

        # 通用魔数匹配
        for magic, file_type in self.MAGIC_NUMBERS:
            if len(magic) <= len(data) and data.startswith(magic):
                return file_type
        return None

    def _fetch_content_with_location(
        self,
        client: httpx.Client,
        url: str,
        headers: dict[str, str],
        timeout: int,
        max_redirects: int = 5
    ) -> bytes | None:
        """
        手动处理 HTTP 重定向（兼容 301/302/200 + Location 头），递归获取最终内容。

        :param client: httpx 客户端
        :param url: 当前请求 URL
        :param headers: 请求头
        :param timeout: 超时时间
        :param max_redirects: 最大重定向次数
        :return: 文件内容字节，失败返回 None
        """
        if max_redirects <= 0:
            logger.warning(f"重定向次数超限: {url}")
            return None

        try:
            response = client.get(url, headers=headers, follow_redirects=False, timeout=timeout)
            location = response.headers.get("Location")

            # 只要有 Location 头，无论状态码，都跳转（兼容您的原始逻辑）
            if location:
                new_url = self._add_https_if_missing(location)
                logger.info(f"跳转: {url} -> {new_url} (状态码: {response.status_code})")
                return self._fetch_content_with_location(
                    client, new_url, headers, timeout, max_redirects - 1
                )
            elif response.status_code == 200:
                return response.content
            else:
                logger.error(f"非成功响应且无 Location: {response.status_code} from {url}")
                return None

        except Exception as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            return None

    def _build_file_info(self, content: bytes, file_type: str, md5_hex: str) -> dict[str, Any]:
        """
        构建文件信息字典（含图片元数据）。

        :param content: 文件字节内容
        :param file_type: 文件类型
        :param md5_hex: MD5 值
        :return: 文件信息字典
        """
        info = self.get_image_info(content)
        if not info['file_type']:
            info['file_type'] = file_type
        if not info['md5']:
            info['md5'] = md5_hex
        return info

    # ────────────────────────────────────────────────────────
    # 核心功能：获取图片信息
    # ────────────────────────────────────────────────────────

    def get_image_info(self, bytes_object: bytes) -> dict[str, Any]:
        """
        从字节数据中提取图片元信息（仅适用于图像文件）。

        :param bytes_object: 图片字节数据
        :return: 包含 size, md5, phash, file_type, width, height, orientation 的字典
        """
        size = len(bytes_object)
        md5_value = md5(bytes_object).hexdigest().upper()
        phash = ""
        file_type = ""
        width = 0
        height = 0
        orientation = ""

        try:
            with BytesIO(bytes_object) as bytes_io:
                # 首先尝试正常打开图像
                image = Image.open(bytes_io)

                # 检测是否是调色板透明度图像，需要转换
                if image.mode == 'P':
                    try:
                        # 尝试转换为RGBA以处理透明度
                        image = image.convert('RGBA')
                    except Exception:
                        # 如果转换失败，尝试其他方式
                        try:
                            image = image.convert('RGB')
                        except Exception:
                            # 重新打开原始图像
                            bytes_io.seek(0)
                            image = Image.open(bytes_io)

                file_type = image.format.lower() if image.format else ""

                # 在尝试获取phash之前，先确保图像数据完整
                try:
                    # 为了安全起见，使用verify后再重新打开
                    bytes_io.seek(0)
                    temp_image = Image.open(bytes_io)
                    temp_image.verify()  # 验证图像
                    bytes_io.seek(0)  # 重新定位到开头
                    image = Image.open(bytes_io)  # 重新打开
                except Exception:
                    # 如果验证失败，直接使用原图像
                    bytes_io.seek(0)
                    image = Image.open(bytes_io)

                # 确保图像已加载
                if hasattr(image, 'load'):
                    image.load()

                phash = str(imagehash.phash(image)).upper()
                width, height = image.size
                orientation = "横向" if width > height else "竖向"
        except (UnidentifiedImageError, IOError):
            pass
        except Exception as e:
            # 检查错误信息并尝试修复
            error_msg = str(e)
            if "Corrupt EXIF data" in error_msg or "Palette images with Transparency" in error_msg:
                try:
                    # 尝试修复图像
                    fixed_bytes = self._fix_corrupted_image(bytes_object)
                    if fixed_bytes:
                        # 递归调用自身处理修复后的数据
                        return self.get_image_info(fixed_bytes)
                except Exception as fix_error:
                    logger.debug(f"修复图像失败: {fix_error}")
            logger.debug(f"解析图片失败: {e}")

        return {
            'size': size,
            'md5': md5_value,
            'phash': phash,
            'file_type': file_type,
            'width': width,
            'height': height,
            'orientation': orientation
        }

    # ────────────────────────────────────────────────────────
    # 核心功能：下载
    # ────────────────────────────────────────────────────────

    def download_image(
        self,
        url: str,
        save_dir: str,
        filename: str | None = None,
        timeout: int = 36
    ) -> dict[str, Any] | None:
        """
        下载文件并保存到本地目录，不涉及数据库操作。

        :param url: 文件 URL
        :param save_dir: 保存目录
        :param filename: 自定义文件名（可选）
        :param timeout: 超时时间（秒）
        :return: 成功返回文件信息字典，失败返回 None
        """
        url = self._add_https_if_missing(url)
        headers = self._generate_fake_headers(url)

        try:
            with httpx.Client(timeout=timeout) as client:
                content = self._fetch_content_with_location(client, url, headers, timeout)
                if content is None:
                    logger.error(f"无法获取内容: {url}")
                    return None

            file_type = self._identify_file_type_by_magic(content[:32])
            if not file_type:
                logger.warning(f"无法识别文件类型: {url}")
                return None

            image_info = self.get_image_info(content)
            md5_hex = image_info['md5'] or md5(content).hexdigest().upper()
            ext = self.EXTENSION_MAPPING.get(file_type, f".{file_type}")
            final_name = filename or f"{md5_hex}{ext}"
            file_path = os.path.join(save_dir, final_name)

            if os.path.exists(file_path):
                logger.info(f"文件已存在: {file_path}")
                return {
                    'file_path': file_path,
                    'width': image_info['width'],
                    'height': image_info['height'],
                    'size': image_info['size'],
                    'md5': md5_hex,
                    'file_type': file_type,
                    'phash': image_info.get('phash', ''),
                    'orientation': image_info.get('orientation', '')
                }

            os.makedirs(save_dir, exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.info(f"文件保存成功: {file_path}")

            return {
                'file_path': file_path,
                'width': image_info['width'],
                'height': image_info['height'],
                'size': image_info['size'],
                'md5': md5_hex,
                'file_type': file_type,
                'phash': image_info.get('phash', ''),
                'orientation': image_info.get('orientation', '')
            }

        except Exception as e:
            logger.error(f"下载保存失败: {url}, 错误: {e}")
            return None

    def sizeof_url_image(self, url: str, timeout: int = 30) -> dict[str, Any]:
        """
        获取远程图片尺寸与元信息（不保存）。

        :param url: 图片 URL
        :param timeout: 超时时间
        :return: 图片信息或错误字典
        """
        url = self._add_https_if_missing(url)
        headers = self._generate_fake_headers(url)
        try:
            with httpx.Client(timeout=timeout) as client:
                content = self._fetch_content_with_location(client, url, headers, timeout)
                if content is None:
                    return {'error': '无法获取内容'}

            # 使用get_image_info来处理可能的图像错误
            image_info = self.get_image_info(content)
            if image_info.get('width') and image_info.get('height'):
                return {
                    'width': image_info['width'],
                    'height': image_info['height'],
                    'file_size': len(content),
                    'md5': image_info['md5']
                }
            else:
                return {'error': '无法解析图片信息'}
        except Exception as e:
            return {'error': str(e)}

    def is_image_accessible(self, url: str, timeout: int = 30) -> bool:
        """
        检查 URL 是否可访问（通过 Location 重定向链）。

        :param url: URL
        :param timeout: 超时时间
        :return: 是否可访问
        """
        url = self._add_https_if_missing(url)
        headers = self._generate_fake_headers(url)
        try:
            with httpx.Client(timeout=timeout) as client:
                content = self._fetch_content_with_location(client, url, headers, timeout)
                return content is not None
        except Exception:
            return False

    # ────────────────────────────────────────────────────────
    # 数据库存储（完全解耦）
    # ────────────────────────────────────────────────────────

    def save_image_record_to_db(self, mysql_db: Any, image_info: dict[str, Any], url: str) -> None:
        """
        将图片信息存入数据库（需调用者主动调用）。

        :param mysql_db: 数据库实例
        :param image_info: 图片信息字典（需包含 'md5'）
        :param url: 原始 URL
        """
        if not isinstance(image_info, dict) or 'md5' not in image_info:
            logger.error("无效的 image_info，跳过数据库存储")
            return

        # 仅支持图像类型
        if image_info.get('file_type') not in {
            self.FILE_TYPE_PNG, self.FILE_TYPE_JPEG, self.FILE_TYPE_GIF,
            self.FILE_TYPE_BMP, self.FILE_TYPE_WEBP, self.FILE_TYPE_AVIF
        }:
            logger.debug("非图像文件，跳过数据库存储")
            return

        md5_val = image_info['md5']
        existing = mysql_db.find_info("image", where={"md5": md5_val})
        if existing is None:
            record = image_info.copy()
            record.update({"type": "动漫", "local": "是"})
            mysql_db.insert("image", record)
            image_id = mysql_db.find_info("image", where={"md5": md5_val})['id']
        else:
            mysql_db.update("image", image_info, where={"md5": md5_val})
            image_id = existing['id']

        url_record = mysql_db.find_info("image_url", where={"url": url})
        if url_record is None:
            mysql_db.insert("image_url", {"url": url, "image_id": image_id, "access": "能"})
        logger.info(f"数据库记录已更新: {url}")

    # ────────────────────────────────────────────────────────
    # 批量下载
    # ────────────────────────────────────────────────────────

    def batch_download_from_api(
        self,
        api_urls: list[str],
        save_path: str,
        count_per_api: int = 5,
        parser_func: Callable[[dict], str | None] | None = None,
    ) -> dict[str, Any]:
        """
        从多个 API 批量下载图片，支持两类 API：
        1. 返回 JSON（含图片 URL）
        2. 直接返回图片（200 二进制）或重定向到图片（301/302）

        采用轮询策略，自动清理 URL 空格，增强反爬兼容性。
        """
        # 清理 URL 空格并去重
        cleaned_urls = []
        for url in api_urls:
            stripped = url.strip()
            if stripped:
                cleaned_urls.append(stripped)
        if not cleaned_urls:
            logger.warning("无有效 API URL")
            return {'success': 0, 'failed': 0, 'details': []}

        results = {'success': 0, 'failed': 0, 'details': []}

        def default_parser(json_data: dict) -> str | None:
            for key in ['url', 'img', 'text']:
                if key in json_data:
                    return str(json_data[key])
            if 'data' in json_data and isinstance(json_data['data'], list) and json_data['data']:
                item = json_data['data'][0]
                if 'url' in item:
                    return item['url']
                if 'urls' in item and 'original' in item['urls']:
                    return item['urls']['original']
            return None

        parser = parser_func or default_parser

        for round_idx in range(count_per_api):
            for api_url in cleaned_urls:
                try:
                    headers = self._generate_fake_headers(api_url)
                    with httpx.Client(timeout=60) as client:
                        # 先尝试获取最终内容（处理重定向）
                        content = self._fetch_content_with_location(client, api_url, headers, 60)

                        if content is None:
                            raise Exception(f"无法获取内容: {api_url}")

                        # 检查内容是否为JSON格式
                        try:
                            # 尝试解析为JSON
                            decoded_content = content.decode('utf-8', errors='ignore')
                            json_data = json.loads(decoded_content)

                            # 如果是JSON格式，解析并获取图片URL
                            img_url = parser(json_data)

                            if img_url:
                                if not img_url.startswith(('http://', 'https://')):
                                    img_url = ('https://' if api_url.startswith('https') else 'http://') + img_url.lstrip('/')
                                result = self.download_image(img_url, save_path)
                                api_type = 'json'
                            else:
                                # 如果JSON解析成功但没有找到图片URL，可能是API返回了错误信息
                                raise Exception(f"JSON响应中未找到图片URL: {api_url}, 响应: {decoded_content[:200]}")
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # 如果不是JSON格式，可能是直接返回图片或HTML错误页面
                            # 尝试解析为HTML，看是否是错误页面
                            try:
                                decoded_content = content.decode('utf-8', errors='ignore')
                                if '<html>' in decoded_content.lower() and ('error' in decoded_content.lower() or 'moved permanently' in decoded_content.lower()):
                                    raise Exception(f"收到HTML错误页面: {api_url}, 内容: {decoded_content[:200]}")
                            except:
                                pass  # 如果解码失败，继续尝试作为图片处理

                            # 尝试作为图片处理 - 这意味着API直接返回了图片，不需要额外下载
                            # 首先通过魔数检测文件类型
                            file_type = self._identify_file_type_by_magic(content[:32])

                            # 如果魔数检测确认是图片类型，尝试处理
                            if file_type and file_type in [self.FILE_TYPE_JPEG, self.FILE_TYPE_PNG, self.FILE_TYPE_GIF,
                                                           self.FILE_TYPE_BMP, self.FILE_TYPE_WEBP, self.FILE_TYPE_TIFF, self.FILE_TYPE_AVIF]:
                                # 确认是图片类型，尝试保存
                                md5_hash = md5(content).hexdigest().upper()
                                ext = self.EXTENSION_MAPPING.get(file_type, f".{file_type}")
                                file_path = os.path.join(save_path, f"{md5_hash}{ext}")

                                os.makedirs(save_path, exist_ok=True)
                                with open(file_path, 'wb') as f:
                                    f.write(content)

                                # 获取图片信息，这会尝试修复可能损坏的图片
                                image_info = self.get_image_info(content)

                                # 检查是否成功获取了图片信息
                                if image_info.get('width') > 0 and image_info.get('height') > 0:
                                    result = {
                                        'file_path': file_path,
                                        'width': image_info['width'],
                                        'height': image_info['height'],
                                        'size': image_info['size'],
                                        'md5': image_info['md5'],
                                        'file_type': image_info['file_type'],
                                        'phash': image_info.get('phash', ''),
                                        'orientation': image_info.get('orientation', '')
                                    }
                                    # 在这种情况下，我们实际上是从API URL获得的图片，所以使用api_url作为image_url
                                    img_url = api_url
                                    api_type = 'direct'
                                else:
                                    # 如果get_image_info无法提取有效信息，删除保存的文件
                                    try:
                                        os.remove(file_path)
                                    except:
                                        pass
                                    raise Exception(f"响应不是有效的图片: {api_url}")
                            else:
                                # 尝试使用PIL直接打开（作为最后手段）
                                import io
                                from PIL import Image

                                try:
                                    with Image.open(io.BytesIO(content)) as img:
                                        # 是有效图片，保存它
                                        md5_hash = md5(content).hexdigest().upper()
                                        ext = self.EXTENSION_MAPPING.get(img.format.lower(), f".{img.format.lower()}")
                                        file_path = os.path.join(save_path, f"{md5_hash}{ext}")

                                        os.makedirs(save_path, exist_ok=True)
                                        with open(file_path, 'wb') as f:
                                            f.write(content)

                                        # 获取图片信息
                                        image_info = self.get_image_info(content)
                                        result = {
                                            'file_path': file_path,
                                            'width': image_info['width'],
                                            'height': image_info['height'],
                                            'size': image_info['size'],
                                            'md5': image_info['md5'],
                                            'file_type': image_info['file_type'],
                                            'phash': image_info.get('phash', ''),
                                            'orientation': image_info.get('orientation', '')
                                        }
                                        # 在这种情况下，我们实际上是从API URL获得的图片，所以使用api_url作为image_url
                                        img_url = api_url
                                        api_type = 'direct'
                                except Exception:
                                    # 不是有效图片，抛出错误
                                    raise Exception(f"响应不是有效的JSON也不是图片: {api_url}")
                        if 'error' not in result:
                            results['success'] += 1
                            results['details'].append({
                                'api': api_url,
                                'image_url': img_url,
                                'result': result,
                                'type': api_type
                            })
                            logger.info(f"轮次 {round_idx + 1}: 下载成功 {api_url}")
                        else:
                            raise Exception(result['error'])

                except Exception as e:
                    results['failed'] += 1
                    results['details'].append({
                        'api': api_url,
                        'error': str(e),
                        'round': round_idx + 1
                    })
                    logger.error(f"轮次 {round_idx + 1}, API {api_url} 失败: {e}")

        return results

    # ────────────────────────────────────────────────────────
    # 文件管理工具
    # ────────────────────────────────────────────────────────

    def correct_file_extension(self, file_path: str, target_dir: str | None = None) -> None:
        """
        根据魔数修正文件扩展名（使用 MD5 重命名）
        仅支持文件，目录请使用 `batch_correct_extensions`
        :param file_path: 文件路径
        :param target_dir: 目标目录，默认为原始目录
        """
        try:
            with open(file_path, 'rb') as f:
                all_content = f.read()

            # 首先尝试获取图像信息，可能会修复损坏的图像
            image_info = self.get_image_info(all_content)
            md5_name = image_info['md5']

            file_type = self._identify_file_type_by_magic(all_content[:32])
            if not file_type:
                # 如果魔数无法识别，尝试使用图像信息
                file_type = image_info.get('file_type', '')

            if not file_type:
                logger.warning(f"无法识别文件类型: {file_path}")
                return

            ext = self.EXTENSION_MAPPING.get(file_type, f".{file_type}")
            target_dir = target_dir or os.path.dirname(file_path)
            new_path = os.path.join(target_dir, md5_name + ext)
            if new_path != file_path:
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(file_path, new_path)
                logger.info(f"重命名: {file_path} -> {new_path}")
        except Exception as e:
            logger.error(f"修正扩展名失败: {file_path}, 错误: {e}")

    def batch_correct_extensions(self, directory: str, target_dir: str = None) -> None:
        """批量修正目录中所有文件的扩展名"""
        files = self.list_files_in_directory(directory)
        for filename in files:
            file_path = os.path.join(directory, filename)
            self.correct_file_extension(file_path, target_dir)

    def list_files_in_directory(self, directory: str) -> list[str]:
        """列出目录下所有文件（非递归）"""
        try:
            with os.scandir(directory) as entries:
                return [entry.name for entry in entries if entry.is_file()]
        except Exception as e:
            logger.error(f"读取目录失败: {directory}, 错误: {e}")
            return []

    def move_file(self, src: str, dst: str) -> None:
        """移动文件"""
        try:
            shutil.move(src, dst)
            logger.info(f"移动: {src} -> {dst}")
        except Exception as e:
            logger.error(f"移动失败: {src} -> {dst}, 错误: {e}")

    def check_and_update_md5(self, file_path: str) -> str:
        """计算文件 MD5 值"""
        with open(file_path, 'rb') as f:
            return md5(f.read()).hexdigest().upper()

    def deduplicate_by_phash_optimized(self, directory: str, max_workers: int = 0, cache_file: str = "phash_cache.json") -> None:
        """
        优化的基于感知哈希去重方法 - 结合预过滤、并行处理和缓存机制

        :param directory: 要处理的目录
        :param max_workers: 并行处理的最大线程数，0表示自动计算
        :param cache_file: 缓存文件路径
        """
        # 自动计算工作线程数
        if max_workers <= 0:
            max_workers = min(16, max(1, multiprocessing.cpu_count()))

        # 预过滤图像文件
        files = [f for f in self.list_files_in_directory(directory)
                 if self._is_likely_image(os.path.join(directory, f))]

        logger.info(f"开始去重，共 {len(files)} 个图像文件，使用 {max_workers} 个线程")

        # 加载缓存
        cache = self._load_cache(cache_file)

        # 并行处理文件
        phash_results = self._process_files_parallel(directory, files, cache, max_workers)

        # 保存新缓存
        self._save_cache(phash_results, cache_file)

        # 按phash分组
        phash_groups = defaultdict(list)
        for item in phash_results.values():
            if 'phash' in item:
                phash_groups[item['phash']].append(item)

        # 批量删除重复项
        self._remove_duplicates(phash_groups)

    def _is_likely_image(self, file_path: str) -> bool:
        """快速判断是否为图像文件"""
        ext = os.path.splitext(file_path)[1].lower()
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        return ext in image_extensions

    def _load_cache(self, cache_file: str) -> Dict[str, Any]:
        """加载缓存"""
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            except:
                cache = {}
        return cache

    def _save_cache(self, cache: Dict[str, Any], cache_file: str) -> None:
        """保存缓存"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    def _process_files_parallel(self, directory: str, files: List[str], cache: Dict[str, Any], max_workers: int) -> Dict[str, Any]:
        """并行处理文件"""
        phash_results = {}
        lock = threading.Lock()

        def process_file(filename: str):
            file_path = os.path.join(directory, filename)
            file_mtime = os.path.getmtime(file_path)

            # 检查缓存
            if filename in cache and cache[filename].get('mtime') == file_mtime:
                return filename, cache[filename]  # 使用缓存

            # 重新计算
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()

                # 获取图像信息，内部会处理错误和修复
                info = self.get_image_info(content)

                if info['phash']:
                    return filename, {
                        'phash': info['phash'],
                        'size': info['size'],
                        'mtime': file_mtime,
                        'path': file_path
                    }
            except Exception as e:
                logger.error(f"处理文件失败: {file_path}, 错误: {e}")
            return filename, None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(process_file, f): f for f in files}

            for future in as_completed(future_to_file):
                filename, result = future.result()
                if result:
                    with lock:
                        phash_results[filename] = result

        return phash_results

    def _remove_duplicates(self, phash_groups: Dict[str, List[Dict[str, Any]]]) -> None:
        """删除重复项"""
        total_removed = 0
        for group in phash_groups.values():
            if len(group) > 1:
                group.sort(key=lambda x: x['size'], reverse=True)
                for to_remove in group[1:]:
                    try:
                        os.remove(to_remove['path'])
                        logger.info(f"删除重复: {to_remove['path']}")
                        total_removed += 1
                    except Exception as e:
                        logger.error(f"删除失败: {to_remove['path']}, 错误: {e}")

        logger.info(f"去重完成，共删除 {total_removed} 个重复文件")

    def filter_images_by_size(
        self,
        directory: str,
        min_width: int = 0,
        min_height: int = 0,
        max_width: float = float('inf'),
        max_height: float = float('inf')
    ) -> list[dict[str, Any]]:
        """
        按尺寸过滤图像文件 - 根据指定的宽高范围筛选目录中的图像文件
        """
        valid_images = []
        for filename in self.list_files_in_directory(directory):
            path = os.path.join(directory, filename)
            try:
                with open(path, 'rb') as f:
                    content = f.read()

                # 使用get_image_info来处理可能的图像错误
                info = self.get_image_info(content)

                if (min_width <= info['width'] <= max_width and
                        min_height <= info['height'] <= max_height):
                    info['file_path'] = path
                    valid_images.append(info)
            except Exception as e:
                logger.error(f"过滤失败: {path}, 错误: {e}")
        return valid_images

    def classify_image_by_orientation(
        self,
        source_dir: str,
        horizontal_dir: str | None = None,
        vertical_dir: str | None = None
    ) -> None:
        """按方向分类图像（横向/竖向）"""
        horizontal_dir = horizontal_dir or os.path.join(source_dir, "horizontal")
        vertical_dir = vertical_dir or os.path.join(source_dir, "vertical")
        os.makedirs(horizontal_dir, exist_ok=True)
        os.makedirs(vertical_dir, exist_ok=True)

        for filename in self.list_files_in_directory(source_dir):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.avif')):
                continue
            src_path = os.path.join(source_dir, filename)
            try:
                with open(src_path, 'rb') as f:
                    content = f.read()

                # 使用get_image_info来处理可能的图像错误
                info = self.get_image_info(content)

                dst_dir = horizontal_dir if info['orientation'] == '横向' else vertical_dir
                shutil.copy2(src_path, os.path.join(dst_dir, filename))
                logger.info(f"分类: {filename} -> {info['orientation']}")
            except Exception as e:
                logger.error(f"分类失败: {src_path}, 错误: {e}")

    def unblock_file(self, file_path):
        """
        解除由Windows标记的“文件锁定”（即删除Zone.Identifier备用数据流）。
        适用于从网络下载的文件被阻塞的情况。

        参数:
            file_path (str): 需要解除锁定的文件路径。
        """
        # 构建Zone.Identifier备用数据流的完整路径
        zone_identifier_stream = file_path + ':Zone.Identifier'

        try:
            # 检查备用数据流是否存在
            if os.path.exists(zone_identifier_stream):
                # 删除该数据流以解除锁定
                os.remove(zone_identifier_stream)
                print(f"成功解除文件锁定: {file_path}")
            else:
                # 如果不存在，说明文件没有此安全标记
                print(f"文件未被锁定或无Zone.Identifier数据流: {file_path}")
        except Exception as e:
            print(f"处理文件时发生错误: {file_path} - 错误: {e}")

    def _fix_corrupted_image(self, image_bytes: bytes) -> bytes | None:
        """
        尝试修复损坏的图像文件

        :param image_bytes: 原始图像字节数据
        :return: 修复后的图像字节数据，如果修复失败则返回None
        """
        try:
            with BytesIO(image_bytes) as input_buffer:
                # 首先尝试打开图像
                image = Image.open(input_buffer)

                # 如果是调色板模式且包含透明度，转换为RGBA
                if image.mode == 'P':
                    try:
                        # 尝试获取透明度信息
                        transparency = image.info.get('transparency')
                        if transparency is not None:
                            image = image.convert('RGBA')
                        else:
                            image = image.convert('RGB')
                    except Exception:
                        # 如果转换失败，尝试直接转为RGB
                        try:
                            image = image.convert('RGB')
                        except Exception:
                            # 重新打开图像
                            input_buffer.seek(0)
                            image = Image.open(input_buffer)

                # 创建输出缓冲区
                output_buffer = BytesIO()

                # 保存修复后的图像，不包含可能损坏的EXIF数据
                save_kwargs = {}

                # 根据图像模式和格式设置保存参数
                if image.format == 'JPEG':
                    # JPEG不支持透明度，需要转换
                    if image.mode in ('RGBA', 'LA', 'P'):
                        image = image.convert('RGB')
                    save_kwargs['quality'] = 95
                    save_kwargs['optimize'] = True
                elif image.format in ('PNG', 'WEBP'):
                    # PNG和WEBP支持透明度
                    if 'transparency' in image.info and image.mode in ('RGBA', 'LA'):
                        save_kwargs['transparency'] = image.info['transparency']

                # 保存图像
                image.save(output_buffer, format=image.format, **save_kwargs)

                return output_buffer.getvalue()
        except Exception as e:
            logger.error(f"修复图像失败: {e}")
            return None

    def split_image_by_grid(
        self,
        image_path: str,
        rows: int,
        cols: int,
        output_dir: str = "./output",
        output_prefix: str = "split"
    ) -> List[str]:
        """
        将图片按网格分割成多个子图

        :param image_path: 输入图片路径
        :param rows: 网格行数
        :param cols: 网格列数
        :param output_dir: 输出目录
        :param output_prefix: 输出文件名前缀
        :return: 生成的图片路径列表
        """
        # 打开图片
        img = Image.open(image_path)
        width, height = img.size

        # 计算每个小图的尺寸
        cell_width = width // cols
        cell_height = height // rows

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        output_paths = []

        # 遍历每个单元格并裁剪保存
        for row in range(rows):
            for col in range(cols):
                left = col * cell_width
                top = row * cell_height
                right = left + cell_width
                bottom = top + cell_height

                # 裁剪子图
                cropped = img.crop((left, top, right, bottom))

                # 保存为单独文件
                index = row * cols + col + 1
                output_path = os.path.join(output_dir, f"{output_prefix}_{index:02d}.png")
                cropped.save(output_path)
                output_paths.append(output_path)
                print(f"已保存: {output_path}")

        print(f"\n所有图片已成功拆分！共生成 {len(output_paths)} 个子图")
        return output_paths
