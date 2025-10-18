const express = require('express');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.static('public'));

// 媒体文件扩展名
const MEDIA_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'];
// 字幕文件扩展名
const SUBTITLE_EXTENSIONS = ['.srt', '.ass', '.ssa', '.sub', '.vtt'];

// 获取指定目录下的媒体和字幕文件
app.post('/api/scan', async (req, res) => {
  try {
    const { folderPath } = req.body;
    
    if (!folderPath) {
      return res.status(400).json({ error: '请提供文件夹路径' });
    }

    const stats = await fs.stat(folderPath);
    if (!stats.isDirectory()) {
      return res.status(400).json({ error: '路径不是有效的文件夹' });
    }

    const files = await fs.readdir(folderPath);
    const fileList = [];

    for (const file of files) {
      const filePath = path.join(folderPath, file);
      const fileStat = await fs.stat(filePath);
      
      if (fileStat.isFile()) {
        const ext = path.extname(file).toLowerCase();
        let type = null;
        
        if (MEDIA_EXTENSIONS.includes(ext)) {
          type = 'media';
        } else if (SUBTITLE_EXTENSIONS.includes(ext)) {
          type = 'subtitle';
        }
        
        if (type) {
          fileList.push({
            name: file,
            path: filePath,
            type: type,
            size: fileStat.size,
            modified: fileStat.mtime
          });
        }
      }
    }

    res.json({ files: fileList, folderPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 重命名文件
app.post('/api/rename', async (req, res) => {
  try {
    const { oldPath, newName } = req.body;
    
    if (!oldPath || !newName) {
      return res.status(400).json({ error: '请提供原路径和新文件名' });
    }

    const dir = path.dirname(oldPath);
    const newPath = path.join(dir, newName);

    // 检查新文件名是否已存在
    try {
      await fs.access(newPath);
      return res.status(400).json({ error: '文件名已存在' });
    } catch {
      // 文件不存在，可以继续
    }

    await fs.rename(oldPath, newPath);
    res.json({ success: true, newPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`服务器运行在 http://localhost:${PORT}`);
});
