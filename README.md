# EpubForge

EpubForge（电子书工坊）是一款面向 Windows 的批量 EPUB 制作与转换工具。当前实现以 MVP 为主：支持 TXT 转 EPUB、批量任务、TXT 编码识别、章节识别、基础元数据、转换日志和 PyInstaller 打包；MOBI/AZW3 通过 Calibre `ebook-convert` 入口转换。

## 功能

- 导入单个文件、多个文件、文件夹，支持拖拽导入。
- 支持 TXT、Markdown、HTML、MOBI、AZW3；TXT/Markdown/HTML 使用内置解析器，MOBI/AZW3 调用 Calibre。
- 自动识别 UTF-8、GBK、GB18030、Big5 等常见 TXT 编码。
- 自动识别中文章节、序章、楔子、前言、后记、番外、Chapter 标题；Markdown/HTML 按标题自动分章。
- 内置多种章节标题识别规则，覆盖 `第一章`、`卷一`、`1. 标题`、`Chapter 1`、`序章/正文/后记` 等形式，并支持多行自定义正则。
- 章节编辑面板可在转换前调整章节标题和正文内容，转换时优先使用已编辑内容。
- 支持分卷识别和分卷目录输出，`第一卷`、`卷一`、`Volume 1`、`Part II` 等标题会作为分卷显示。
- GUI 异常会写入用户目录下的 `EpubForge/crash.log`，转换线程异常会弹窗提示，便于排查闪退。
- HTML/Markdown 解析会保留游离文本、连续空章节和基础文本结构，避免静默丢内容。
- 生成标准 EPUB 结构，包含 `mimetype`、`container.xml`、`content.opf`、`nav.xhtml`、CSS 和章节 XHTML。
- 支持书名、作者、语言、出版社、关键词、简介、封面元数据。
- 批量任务支持并发、暂停、继续、停止、失败隔离和日志导出。
- 配置保存到用户目录，任务记录保存到 SQLite。

<img width="1589" height="940" alt="image" src="https://github.com/user-attachments/assets/2977822a-c25f-452c-86c2-4e545ace42a9" />


## 开发运行

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m app.main
```

未安装 PySide6 时，也可以先用命令行转换验证核心能力：

```powershell
py -3 -m app.main --convert .\demo.txt .\demo.md .\demo.html -o .\output
```

## 测试

```powershell
py -3 -m unittest discover tests
```

## 打包

```powershell
.\scripts\build_exe.ps1
```

默认输出为启动更快的目录版：`dist/EpubForge/EpubForge.exe`。目录版不会在每次启动时解压 PySide6 运行库，适合作为日常使用版本。

如确实需要单文件版本，可执行：

```powershell
.\scripts\build_exe.ps1 -OneFile
```

单文件输出位于 `dist/EpubForge.exe`，但启动时需要先解压运行库，打开速度会明显慢于目录版。如需安装包，可用 Inno Setup 打开 `scripts/build_installer.iss` 生成 `EpubForge_Setup_1.0.0.exe`。
