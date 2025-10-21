#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级媒体识别器
融合 NAS-Tools 和 MoviePilot 的最佳识别算法
"""

import re
from typing import Dict, Any, Optional, List, Tuple


class AdvancedRecognizer:
    """高级识别器 - 融合多种识别算法"""
    
    def __init__(self):
        # NAS-Tools 风格的正则模式（更全面）
        self.patterns = {
            'season': [
                r'[Ss](\d{1,2})',                    # S01, s1
                r'第(\d{1,2})[季期]',                 # 第1季, 第1期
                r'[Ss]eason[\s._-]?(\d{1,2})',       # Season 1, Season.1
                r'[\[【](\d{1,2})[季期][\]】]',       # [1季], 【1期】
            ],
            'episode': [
                r'[Ee](\d{1,3})',                    # E01, e1
                r'第(\d{1,3})[集话話]',               # 第1集, 第1话
                r'[Ee]pisode[\s._-]?(\d{1,3})',      # Episode 1
                r'[\[【](\d{1,3})[集话話][\]】]',     # [01集], 【1话】
                r'EP?(\d{1,3})',                     # EP01, E01
                r'[\s._-](\d{2,3})[\s._-]',          # .01., _01_
            ],
            'year': [
                r'(?:^|[^\d])(19\d{2}|20[0-2]\d)(?:[^\d]|$)',  # 1900-2029
                r'[\[【(](\d{4})[\]】)]',             # [2023], (2023)
            ],
            'resolution': [
                r'(\d{3,4}[Pp])',                    # 1080p, 720p, 2160p
                r'(4[Kk])',                          # 4K
                r'(8[Kk])',                          # 8K
                r'(UHD)',                            # UHD
                r'(FHD)',                            # FHD
                r'(HD)',                             # HD
            ],
            'video_codec': [
                r'(H\.?264|[Xx]264|AVC)',            # H264, H.264, x264, AVC
                r'(H\.?265|HEVC|[Xx]265)',           # H265, H.265, HEVC, x265
                r'(AV1)',                            # AV1
                r'(VP9)',                            # VP9
                r'(MPEG-?2)',                        # MPEG2, MPEG-2
            ],
            'audio_codec': [
                r'(AAC)',                            # AAC
                r'(AC-?3)',                          # AC3, AC-3
                r'(DTS(?:-HD)?)',                    # DTS, DTS-HD
                r'(TrueHD)',                         # TrueHD
                r'(FLAC)',                           # FLAC
                r'(DDP|DD\+)',                       # DDP, DD+
                r'(Atmos)',                          # Atmos
            ],
            'source': [
                r'(BluRay|Blu-Ray|BDMV|BD)',         # BluRay
                r'(WEB-?DL|WEBDL)',                  # WEB-DL
                r'(WEBRip)',                         # WEBRip
                r'(HDTV)',                           # HDTV
                r'(DVDRip)',                         # DVDRip
                r'(REMUX)',                          # REMUX
                r'(HDRip)',                          # HDRip
                r'(BRRip)',                          # BRRip
            ],
            'hdr': [
                r'(HDR10\+?)',                       # HDR10, HDR10+
                r'(Dolby[\s._-]?Vision|DV)',         # Dolby Vision
                r'(HLG)',                            # HLG
                r'(SDR)',                            # SDR
            ],
            'language': [
                r'(chs|chi|zh|chinese)',             # 简体中文
                r'(cht|zh-tw|taiwanese)',            # 繁体中文
                r'(eng?|english)',                   # 英语
                r'(jpn?|japanese)',                  # 日语
                r'(kor?|korean)',                    # 韩语
            ],
            'subtitle': [
                r'(简体|简中|CHS)',                   # 简体字幕
                r'(繁体|繁中|CHT)',                   # 繁体字幕
                r'(中英|双语)',                       # 双语字幕
                r'(内封|内嵌)',                       # 内封字幕
                r'(外挂)',                           # 外挂字幕
            ],
            'release_group': [
                r'[\[【]([A-Za-z0-9]+)[\]】]$',      # [RARBG], 【YYeTs】
                r'-([A-Za-z0-9]+)$',                 # -RARBG
            ],
        }
        
        # 季集信息的组合模式
        self.season_episode_patterns = [
            r'[Ss](\d{1,2})[Ee](\d{1,3})',          # S01E01
            r'第(\d{1,2})季[\s._-]?第(\d{1,3})集',   # 第1季第1集
            r'(\d{1,2})x(\d{1,3})',                  # 1x01
        ]
    
    def recognize(self, filename: str) -> Dict[str, Any]:
        """
        识别文件名中的媒体信息
        
        Args:
            filename: 文件名
            
        Returns:
            识别结果字典
        """
        result = {
            'original_name': filename,
            'title': None,
            'year': None,
            'season': None,
            'episode': None,
            'resolution': None,
            'video_codec': None,
            'audio_codec': None,
            'source': None,
            'hdr': None,
            'language': [],
            'subtitle': [],
            'release_group': None,
            'is_tv': False,
        }
        
        # 清理文件名
        clean_name = self._clean_filename(filename)
        
        # 识别季集信息（组合模式）
        season, episode = self._extract_season_episode(clean_name)
        if season or episode:
            result['season'] = season
            result['episode'] = episode
            result['is_tv'] = True
        
        # 识别各种属性
        result['year'] = self._extract_first(clean_name, self.patterns['year'])
        result['resolution'] = self._extract_first(clean_name, self.patterns['resolution'])
        result['video_codec'] = self._extract_first(clean_name, self.patterns['video_codec'])
        result['audio_codec'] = self._extract_first(clean_name, self.patterns['audio_codec'])
        result['source'] = self._extract_first(clean_name, self.patterns['source'])
        result['hdr'] = self._extract_first(clean_name, self.patterns['hdr'])
        result['release_group'] = self._extract_first(clean_name, self.patterns['release_group'])
        
        # 识别语言和字幕（可能有多个）
        result['language'] = self._extract_all(clean_name, self.patterns['language'])
        result['subtitle'] = self._extract_all(clean_name, self.patterns['subtitle'])
        
        # 提取标题（移除所有识别到的信息）
        result['title'] = self._extract_title(clean_name, result)
        
        return result
    
    def _clean_filename(self, filename: str) -> str:
        """清理文件名"""
        # 移除文件扩展名
        name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # 替换常见分隔符为空格
        name = re.sub(r'[._]', ' ', name)
        
        return name
    
    def _extract_season_episode(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """提取季集信息（组合模式）"""
        # 尝试组合模式
        for pattern in self.season_episode_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    season = int(match.group(1))
                    episode = int(match.group(2))
                    return season, episode
                except (ValueError, IndexError):
                    pass
        
        # 单独提取
        season = self._extract_first(text, self.patterns['season'])
        episode = self._extract_first(text, self.patterns['episode'])
        
        try:
            season = int(season) if season else None
            episode = int(episode) if episode else None
        except ValueError:
            season = None
            episode = None
        
        return season, episode
    
    def _extract_first(self, text: str, patterns: List[str]) -> Optional[str]:
        """提取第一个匹配的值"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None
    
    def _extract_all(self, text: str, patterns: List[str]) -> List[str]:
        """提取所有匹配的值"""
        results = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1) if match.groups() else match.group(0)
                if value not in results:
                    results.append(value)
        return results
    
    def _extract_title(self, text: str, info: Dict[str, Any]) -> str:
        """提取标题（移除所有识别到的信息）"""
        title = text
        
        # 移除年份
        if info['year']:
            title = re.sub(rf'\b{info["year"]}\b', '', title, flags=re.IGNORECASE)
        
        # 移除季集信息
        if info['season'] or info['episode']:
            for pattern in self.season_episode_patterns:
                title = re.sub(pattern, '', title, flags=re.IGNORECASE)
            for pattern in self.patterns['season'] + self.patterns['episode']:
                title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # 移除其他信息
        for key in ['resolution', 'video_codec', 'audio_codec', 'source', 'hdr', 'release_group']:
            if info[key]:
                title = re.sub(rf'\b{re.escape(str(info[key]))}\b', '', title, flags=re.IGNORECASE)
        
        # 移除语言和字幕信息
        for lang in info['language'] + info['subtitle']:
            title = re.sub(rf'\b{re.escape(lang)}\b', '', title, flags=re.IGNORECASE)
        
        # 清理多余空格和特殊字符
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'[\[\]【】()（）]', '', title)
        title = title.strip(' -_.')
        
        return title if title else text
    
    def get_quality_score(self, info: Dict[str, Any]) -> int:
        """
        计算文件质量分数（用于去重）
        
        Args:
            info: 识别结果
            
        Returns:
            质量分数
        """
        score = 0
        
        # 分辨率分数
        resolution_scores = {
            '8K': 8000, '8k': 8000,
            '4K': 4000, '4k': 4000, 'UHD': 4000,
            '2160p': 2160, '2160P': 2160,
            '1080p': 1080, '1080P': 1080, 'FHD': 1080,
            '720p': 720, '720P': 720, 'HD': 720,
            '480p': 480, '480P': 480,
            '360p': 360, '360P': 360,
        }
        if info['resolution']:
            score += resolution_scores.get(info['resolution'], 0)
        
        # 来源分数
        source_scores = {
            'REMUX': 100,
            'BluRay': 80, 'Blu-Ray': 80, 'BDMV': 80, 'BD': 80,
            'WEB-DL': 60, 'WEBDL': 60,
            'WEBRip': 40,
            'HDRip': 30,
            'BRRip': 25,
            'HDTV': 20,
            'DVDRip': 10,
        }
        if info['source']:
            score += source_scores.get(info['source'], 0)
        
        # 编码分数
        codec_scores = {
            'H.265': 10, 'H265': 10, 'HEVC': 10, 'x265': 10,
            'AV1': 15,
            'H.264': 5, 'H264': 5, 'x264': 5, 'AVC': 5,
        }
        if info['video_codec']:
            score += codec_scores.get(info['video_codec'], 0)
        
        # HDR 加分
        hdr_scores = {
            'HDR10+': 20,
            'HDR10': 15,
            'Dolby Vision': 25, 'DV': 25,
            'HLG': 10,
        }
        if info['hdr']:
            score += hdr_scores.get(info['hdr'], 0)
        
        # 音频编码加分
        audio_scores = {
            'TrueHD': 10,
            'DTS-HD': 8,
            'Atmos': 12,
            'DTS': 5,
            'AC3': 3, 'AC-3': 3,
            'AAC': 2,
        }
        if info['audio_codec']:
            score += audio_scores.get(info['audio_codec'], 0)
        
        return score


# 全局实例
_advanced_recognizer = None


def get_advanced_recognizer() -> AdvancedRecognizer:
    """获取高级识别器实例（单例）"""
    global _advanced_recognizer
    if _advanced_recognizer is None:
        _advanced_recognizer = AdvancedRecognizer()
    return _advanced_recognizer
