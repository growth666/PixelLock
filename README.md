# PixelLock

PixelLock 是一个使用 **PySide6** 编写的本地图片加密桌面工具，采用 8-bit 像素风界面。它会把任意输入图片转换为 `256 × 256` 灰度图，然后在本地完成加密、密文预览、PNG 导出、解密和误差检查。

图片不会上传到网络。项目适合课程实验、算法演示和可逆图像处理练习。

## 功能

- 打开 PNG、JPG、JPEG、BMP、WEBP、TIF 或 TIFF 图片。
- 自动转换为 `256 × 256` 的 8-bit 灰度图。
- 支持四种算法：
  - **一次一密（OTP）**：像素矩阵与由种子生成的密钥矩阵按模 256 相加。
  - **Arnold 置乱**：按 Arnold 坐标变换搬移像素，支持设置轮数。
  - **Hill 扩散**：使用现有的 2×2 分块矩阵，在模 256 下进行双边矩阵运算。
  - **组合加密**：先 Arnold 置乱，再 Hill 扩散。
- 可调整 OTP 种子和 Arnold 轮数。
- 加密后显示密文，并保存为 PNG。
- 解密后显示还原图，并显示：
  - `MAX ERROR`：最大像素绝对误差。
  - `MAE`：平均绝对误差。
- 底部状态栏显示当前操作状态。

## 界面使用方法

1. 点击 **打开图片 / OPEN IMAGE**，选择一张图片。
2. 确认左侧输出为 `256 × 256 / 灰度`。
3. 在算法下拉框中选择一次一密、Arnold、Hill 或组合加密。
4. 根据算法设置参数：
   - 一次一密：设置 **密钥种子 / OTP SEED**。
   - Arnold：设置 **Arnold 轮数 / ARNOLD ROUNDS**，范围为 `1–192`。
   - Hill：使用固定的 2×2 矩阵，不需要额外参数。
   - 组合加密：设置 Arnold 轮数，执行顺序为 Arnold → Hill。
5. 点击 **加密图片 / ENCRYPT IMAGE** 查看密文。
6. 点击 **保存密文 PNG / SAVE CIPHER PNG** 保存密文图片。
7. 点击 **解密并校验 / DECRYPT + CHECK** 查看还原图和误差。

正确使用同一组参数解密时，应显示最大误差 `0`、平均误差 `0.0000`（英文为 `MAX ERROR` 和 `MAE`）。

## 中英文切换与像素界面

程序默认使用中文。点击右上角 **EN / English** 切换为英文，点击 **中 / 中文** 切回中文。按钮、算法名称、参数说明、预览提示、文件对话框标题、操作状态及误差值会同步切换；图片、参数、密文和还原结果保持不变。重新启动时默认回到中文。

界面采用像素字标、像素锁图标、方块背景、硬边面板及游戏按键样式。正文保留易读字体，图像预览使用最近邻显示；界面装饰不会修改图片像素或加密结果。

## 从源码运行

需要 Python 3.12 或兼容版本。PowerShell 示例：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

如果只运行桌面程序，核心依赖是 `PySide6`；`numpy`、`Pillow` 和 `matplotlib` 还用于保留的旧版实验脚本 `encrypt_lena.py`。

运行旧实验脚本前，请在 `image/` 中准备 `input.png` 和 `photo.png`，再从项目根目录执行 `python encrypt_lena.py`。这些本地输入图片和生成结果均不会提交到 Git。

## 使用 exe

已生成两个 Windows 版本：

- `dist/portable/PixelLockPortable.exe`：单文件版，复制这一个 exe 即可运行。
- `dist/PixelLock/PixelLock.exe`：目录版，必须和旁边的 `_internal` 文件夹一起复制。

单文件版首次启动时可能需要几秒解压运行库。exe 模式下，默认的密文输出目录是 exe 所在目录下的 `image` 文件夹；源码运行时则是项目根目录下的 `image` 文件夹。

## 重新打包

先确保 `.venv` 中安装了 PyInstaller，然后运行：

```powershell
.\build_exe.ps1
```

该脚本使用同一个 `PixelLock.spec` 依次生成目录版和单文件版。请使用该脚本，避免用裸 PyInstaller 命令绕过 DLL 修复配置。

### QtCore DLL 启动错误

如果出现 `DLL load failed while importing QtCore: 找不到指定的程序`，本项目曾确认的原因是：打包工具从 PATH 中误收集了 Poppler 的 `icuuc.dll`，它与 Qt 6.12 所需的 Windows ICU 接口不兼容。配置已排除该 DLL 和它带入的 ICU 78 数据库，让 Windows 加载系统 ICU。这不需要激活虚拟环境，也不应从网上随意下载 DLL 替换系统文件。

当前构建使用 Python 3.12、PySide6 6.12.0、PyInstaller 6.22.3，建议在 Windows 10/11 64 位环境使用；其他系统版本需要另行验证。重新打包后请替换整个旧目录版或旧单文件 exe。

可用 `--self-test --report <报告绝对路径>` 检查打包产物：程序会创建并渲染主窗口，检查四种算法、PNG 保存及重新读取，然后退出并写出 JSON。只有退出码为 0 且报告中 `ok` 为 `true` 才算通过；进程仍存在不代表启动成功。

## 项目结构

```text
PixelLock/
├─ app.py                # PySide6 界面和工作流
├─ crypto_algorithms.py  # 不依赖 NumPy 的加解密实现
├─ i18n.py               # 中英文文案
├─ pixel_theme.py        # 像素图标、字标及主题
├─ smoke_test.py         # 打包产物启动与功能自检
├─ tests/                # 语言切换与状态保留回归检查
├─ encrypt_lena.py       # 原有的 NumPy/Matplotlib 实验脚本
├─ requirements.txt      # Python 依赖
├─ PixelLock.spec        # PyInstaller 目录版配置
├─ build_exe.ps1         # Windows 打包脚本
├─ image/                # 本地生成的密文和导出图片
└─ README.md
```

## 算法和安全说明

这是一个用于学习和演示的图像处理项目，不应直接用于保护真实敏感资料。OTP 的种子在本程序内用于复现同一密钥矩阵，能够保证本程序的加解密匹配；它与旧版 `encrypt_lena.py` 中使用 NumPy 随机数生成器得到的密钥流不同。实际应用还需要安全的密钥生成、保存、分发和认证机制。

当前缩放会强制把输入图片变为正方形 `256 × 256`，因此非正方形图片可能产生几何拉伸；这是本项目规定的统一输入格式。

## Git 提交建议

`.gitignore` 已排除虚拟环境、缓存、PyInstaller 构建目录、exe 输出目录、临时编辑器文件和 `image` 下的生成图片。应提交的主要内容包括源码、`requirements.txt`、`README.md`、`PixelLock.spec` 和 `build_exe.ps1`。
