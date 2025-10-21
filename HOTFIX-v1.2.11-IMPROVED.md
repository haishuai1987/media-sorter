# 🚀 v1.2.11 - 标题清理改进版（借鉴 MoviePilot）

## 📋 改进内容

### 1. 借鉴 MoviePilot 的实现

分析了 MoviePilot 项目的核心代码：
- `app/core/metainfo.py` - 元数据识别
- `app/helper/format.py` - 格式化处理
- `app/chain/tmdb.py` - TMDB 查询

### 2. 增强标题清理功能

**新增功能：**
- ✅ 自动移除 Release Group（CHDWEB、ADWeb、HHWEB 等）
- ✅ 自动移除技术参数（1080p、H.264、WEB-DL 等）
- ✅ 自动移除流媒体标识（AMZN、NF、DSNP 等）
- ✅ 只保留纯中文标题
- ✅ 保留版本标识（如"大神版"）

**支持的 Release Group：**
```
CHDWEB, CHDWEBII, CHDWEBIII, ADWeb, HHWEB, DBTV, 
NGB, FRDS, mUHD, AilMWeb, UBWEB, CHDTV, HDCTV
```

**支持的技术参数：**
```
分辨率: 2160p, 1080p, 720p, 480p, 4K, 8K
编码: H.264, H.265, x264, x265, HEVC, AVC
来源: WEB-DL, WEBRip, BluRay, BDRip, HDRip, DVDRip
音频: DDP, AAC, AC3, DTS, Atmos, TrueHD, DDP5.1, AAC2.0
HDR: HDR, SDR, Dolby Vision, HDR10, HDR10+
平台: AMZN, NF, DSNP, HMAX, ATVP, PCOK, PMTP
```

## ✅ 测试结果

所有 12 个测试用例全部通过：

```
✓ '密室大逃脱 Great Escape' → '密室大逃脱'
✓ '密室大逃脱大神版 Great Escape Super' → '密室大逃脱大神版'
✓ '密室大逃脱大神版.第七季.Great.Escape.Super' → '密室大逃脱大神版'
✓ 'Great Escape' → 'Great Escape'
✓ '密室大逃脱.S07.1080p.WEB-DL.H265.AAC-CHDWEB' → '密室大逃脱'
✓ '花牌情缘：巡.S01.1080p.NF.WEB-DL.AAC.2.0.H.264-CHDWEB' → '花牌情缘：巡'
✓ '间谍过家家.S03.2025.1080p.CR.WEB-DL.x264.AAC-ADWeb' → '间谍过家家'
✓ '奔跑吧.Keep.Running.S09.2025.1080p.WEB-DL.H265.AAC' → '奔跑吧'
✓ '坂本日常.SAKAMOTO.DAYS.S01.2025.1080p.WEB-DL.H264.AAC' → '坂本日常'
✓ '新·吊带袜天使.New.PANTY.&.STOCKING.S01.1080p.AMZN.WEB-DL.DDP.5.1.H.264-CHDWEB' → '新·吊带袜天使'
✓ '从前有个刺客.Nero.the.Assassin.S01.2025.1080p.NF.WEB-DL.x264.DDP5.1.Atmos-ADWeb' → '从前有个刺客'
✓ 'Black Rabbit' → 'Black Rabbit'
```

## 📊 对比

### 改进前
```python
# 简单提取中文
"密室大逃脱.S07.1080p.WEB-DL.H265.AAC-CHDWEB"
→ "密室大逃脱 S07 1080p WEB DL H265 AAC CHDWEB"  ❌
```

### 改进后
```python
# 智能清理
"密室大逃脱.S07.1080p.WEB-DL.H265.AAC-CHDWEB"
→ "密室大逃脱"  ✅
```

## 🎯 实际效果

**文件重命名示例：**
```
原始: 密室大逃脱大神版.第七季.Great.Escape.Super.S07E11.2019.2160p.WEB-DL.H265.AAC-HHWEB.mp4
处理: 密室大逃脱大神版 - S07E11 - 第 11 集.mp4
路径: /vol1/1000/video/媒体库/电视剧/综艺/密室大逃脱大神版 (2019)/Season 7/
```

## 📚 参考资料

- MoviePilot 项目：https://github.com/jxxghp/MoviePilot
- 分析文档：`MOVIEPILOT-ANALYSIS.md`
- 参考代码：`reference/moviepilot/MoviePilot-2/`

## 🚀 部署

### 推送代码
```bash
双击运行: PUSH-v1.2.11.bat
```

### 更新服务器
```bash
# 飞牛OS (192.168.51.105)
ssh root@192.168.51.105
cd /root/media-sorter
git pull origin main
pkill -f "python.*app.py"
nohup python3 app.py > app.log 2>&1 &

# 云服务器 (8.134.215.137)
ssh root@8.134.215.137
cd /root/media-sorter
git pull origin main
pkill -f "python.*app.py"
nohup python3 app.py > app.log 2>&1 &
```

## 📝 版本信息

- **版本号**: v1.2.11
- **类型**: 功能增强
- **优先级**: 高
- **影响**: 所有 TMDB 查询结果
- **测试**: 12/12 通过
