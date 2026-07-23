# EpubForge

EpubForge（电子书工坊）是一款面向 Windows 的批量 EPUB 制作与转换工具。当前实现以 MVP 为主：支持 TXT 转 EPUB、批量任务、TXT 编码识别、章节识别、基础元数据、转换日志和 PyInstaller 打包；MOBI/AZW3 通过 Calibre `ebook-convert` 入口转换。

## 功能

- 导入单个文件、多个文件、文件夹，支持拖拽导入。
- 支持 TXT、Markdown、HTML、MOBI、AZW3；TXT/Markdown/HTML 使用内置解析器，MOBI/AZW3 调用 Calibre。
- 自动识别 UTF-8、GBK、GB18030、Big5 等常见 TXT 编码。
- 自动识别中文章节、序章、楔子、前言、后记、番外、Chapter 标题；Markdown/HTML 按标题自动分章。
- 生成标准 EPUB 结构，包含 `mimetype`、`container.xml`、`content.opf`、`nav.xhtml`、CSS 和章节 XHTML。
- 支持书名、作者、语言、出版社、关键词、简介、封面元数据。
- 批量任务支持并发、暂停、继续、停止、失败隔离和日志导出。
- 配置保存到用户目录，任务记录保存到 SQLite。

![Uploading image.png…]()


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

打包输出位于 `dist/EpubForge.exe`。如需安装包，可用 Inno Setup 打开 `scripts/build_installer.iss` 生成 `EpubForge_Setup_1.0.0.exe`。
