# 构建说明

本项目提供了两种GitHub Actions自动构建流程，可以将Python项目自动打包成EXE可执行文件。

## 🚀 构建流程

### 1. 完整构建流程 (build-exe.yml)

**触发条件：**
- 推送到 `main` 或 `master` 分支
- 创建标签 (如 `v1.0.0`)
- 提交Pull Request
- 手动触发

**功能特性：**
- ✅ 自动构建Windows EXE文件
- ✅ 创建完整的发布包（包含配置文件、样式等）
- ✅ 自动压缩为ZIP文件
- ✅ 标签推送时自动创建GitHub Release
- ✅ 可选的跨平台构建（Windows/Linux/macOS）

### 2. 快速构建流程 (quick-build.yml)

**触发条件：**
- 仅手动触发

**功能特性：**
- ⚡ 快速构建，仅生成EXE文件
- 📦 文件大小检查
- 🎯 适合开发测试使用

## 📋 使用方法

### 方法一：自动构建（推荐）

1. **创建标签发布：**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **等待构建完成：**
   - 访问项目的 Actions 页面
   - 查看构建进度
   - 构建完成后会自动创建Release

### 方法二：手动触发

1. **访问Actions页面：**
   - 进入GitHub项目页面
   - 点击 "Actions" 标签

2. **选择工作流：**
   - 选择 "Build EXE" 或 "Quick Build EXE"
   - 点击 "Run workflow"

3. **下载构建结果：**
   - 构建完成后在Artifacts中下载

## 🔧 构建配置

### 依赖要求

确保项目根目录有以下文件：
- `requirements.txt` - Python依赖列表
- `soul_launcher.spec` - PyInstaller配置文件

### PyInstaller配置

项目使用现有的 `soul_launcher.spec` 文件进行构建，该文件包含：
- 入口点配置
- 资源文件包含
- 输出文件名设置
- 图标和版本信息

## 📦 构建产物

### 完整构建输出：
```
Soul-Launcher-v1.0.0.zip
├── SoulMask Server Launcher.exe          # 主程序
├── configs/                   # 配置文件目录
├── src/common/styles.css      # 样式文件
└── README.txt                 # 使用说明
```

### 快速构建输出：
```
soul-launcher-latest/
└── SoulMask Server Launcher.exe          # 仅主程序
```

## 🛠️ 本地构建

如果需要在本地构建，可以使用以下命令：

```bash
# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 构建EXE
pyinstaller soul_launcher.spec --clean --noconfirm

# 输出文件位于 dist/ 目录
```

## 🔍 故障排除

### 常见问题：

1. **构建失败：**
   - 检查 `requirements.txt` 是否包含所有依赖
   - 确认 `soul_launcher.spec` 文件配置正确

2. **EXE无法运行：**
   - 确保目标系统有必要的运行时库
   - 检查是否缺少资源文件

3. **文件过大：**
   - 优化 `soul_launcher.spec` 中的包含规则
   - 排除不必要的依赖

### 调试方法：

1. **查看构建日志：**
   - 在Actions页面点击具体的构建任务
   - 查看详细的构建输出

2. **本地测试：**
   - 先在本地环境测试构建
   - 确认无误后再推送到GitHub

## 📝 自定义配置

### 修改构建触发条件：

编辑 `.github/workflows/build-exe.yml` 文件中的 `on` 部分：

```yaml
on:
  push:
    branches: [ main ]  # 仅在推送到main分支时触发
  release:
    types: [published]  # 仅在发布Release时触发
```

### 添加构建通知：

可以在工作流中添加通知步骤，如发送邮件或Slack消息。

### 多版本构建：

可以修改工作流以支持多个Python版本的构建测试。

---

💡 **提示：** 首次使用时建议先用"Quick Build"测试构建流程，确认无误后再使用完整构建流程。