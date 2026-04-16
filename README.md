# 🎵 maimai随机选歌工具

一个多平台的maimai随机选歌工具，支持QQ机器人、Web网页、Windows桌面应用和Android移动应用。

**当前版本：Alpha-0.0.1**

## 📁 项目结构

```
maimai_rand_song/
├── core/                   # 核心模块 - 选歌逻辑和数据模型
├── bot/                    # QQ机器人模块 (nonebot2)
├── web/                    # Web模块
│   ├── backend/           # FastAPI后端
│   └── frontend/          # Web前端界面
├── app/                    # App模块
│   ├── windows/           # Windows桌面应用 (Electron)
│   └── android/           # Android应用 (Flutter)
├── config/                 # 配置文件
├── data/                   # 数据文件
│   └── songs.json         # 歌曲数据库
├── tests/                  # 测试文件
├── requirements.txt        # Python依赖
├── VERSION                 # 版本信息
└── README.md              # 项目说明
```

## 🚀 快速开始

### 1. 核心模块和Web服务

```bash
# 安装Python依赖
pip install -r requirements.txt

# 启动Web服务
cd web/backend
python main.py
```

访问 http://localhost:8000 即可使用Web界面

### 2. QQ机器人

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件配置机器人参数

# 启动机器人
cd bot
python main.py
```

### 3. Windows桌面应用

```bash
cd app/windows
npm install
npm start
```

### 4. Android应用

```bash
cd app/android
flutter pub get
flutter run
```

## 🎮 功能特性

### 核心功能
- ✅ 随机选歌
- ✅ 多条件筛选（难度、等级、类型、流派）
- ✅ 批量选歌
- ✅ 歌曲数据库管理

### QQ机器人
- ✅ 群聊at响应
- ✅ 指令式交互
- ✅ 随机选歌命令
- ✅ 帮助信息

### Web界面
- ✅ 可视化选歌条件设置
- ✅ 实时选歌结果展示
- ✅ 歌曲列表浏览
- ✅ 响应式设计

### Windows应用
- ✅ 原生桌面体验
- ✅ 离线使用
- ✅ 快速响应

### Android应用
- ✅ 移动端优化
- ✅ Material Design
- ✅ 触控友好

## 📊 数据格式

歌曲数据存储在 `data/songs.json`，格式如下：

```json
{
  "id": "001",
  "title": "歌曲名称",
  "artist": "艺术家",
  "type": "标准",
  "difficulties": {
    "Easy": 1.0,
    "Basic": 3.0,
    "Advanced": 6.0,
    "Expert": 9.0,
    "Master": 12.0,
    "Re:Master": 14.5
  },
  "genre": "流行",
  "version": "maimai DX",
  "bpm": 120
}
```

## 🔧 配置说明

### 环境变量 (.env)

```env
# QQ机器人配置
BOT_SUPERUSERS=["你的QQ号"]
BOT_HOST=127.0.0.1
BOT_PORT=8080

# Web服务配置
WEB_HOST=127.0.0.1
WEB_PORT=8000

# 数据文件路径
SONGS_DATA_PATH=data/songs.json
```

## 📝 版本历史

### Alpha-0.0.1 (当前版本)
- 🎉 项目初始化
- ✨ 完成基础框架搭建
- ✨ 实现核心选歌逻辑
- ✨ QQ机器人基础功能
- ✨ Web界面基础功能
- ✨ Windows应用基础功能
- ✨ Android应用基础功能

## 🤝 贡献指南

欢迎贡献代码！请查看各个模块的README了解详情。

## 📄 许可证

MIT License

## 🙏 致谢

- maimai 是 SEGA 的注册商标
- 感谢所有贡献者的支持
