# EpubForge

EpubForge（电子书工坊）是一款面向 Windows 的批量 EPUB 制作与编辑工具。它以 TXT/Markdown/HTML 到 EPUB 为主，同时支持通过 Calibre 调用转换 MOBI/AZW3，提供书籍元数据、章节结构、分卷、正文编辑、批量任务和打包发布能力。

## 当前功能

- 支持导入单个文件、批量文件、文件夹，也支持拖拽导入。
- 支持 TXT、Markdown、HTML、MOBI、AZW3；TXT/Markdown/HTML 使用内置解析器，MOBI/AZW3 通过 Calibre `ebook-convert` 转换。
- TXT 自动识别 UTF-8、GBK、GB18030、Big5 等常见编码。
- 支持多种章节标题识别规则，包括 `第一章`、`第 1 章`、`卷一`、`Volume 1`、`Part II`、`Chapter 1`、序章、正文、后记等。
- 支持自定义章节正则、多行规则、固定字数分章、空行分章、不自动分章。
- 支持解析后的章节编辑：修改标题、修改正文、保存修改、还原源文件解析。
- 支持分卷与章节的树状结构展示。
- 支持手动新增、修改、删除分卷和章节，并可选择插入到当前位置前、当前位置后、当前分卷末尾或全书末尾。
- 支持章节多选、批量移动到指定分卷、拖拽排序、上移、下移、合并、拆分、清理文本。
- 支持识别调试、查找替换、章节质量报告、阅读预览。
- 支持书名、作者、语言、出版社、关键词、简介、封面等书籍元数据。
- 支持批量应用书籍设置到选中任务。
- 支持 CSS 模板和转换预设，便于快速切换网文、出版简洁、固定字数兜底等制作方案。
- 支持批量任务并发、暂停、继续、停止、失败重试、清理任务。
- 顶部工具栏会按任务状态启用或禁用按钮，避免空任务时误操作。
- 支持任务历史恢复，任务记录保存到 SQLite。
- 支持日志详情、日志筛选、日志导出。
- 转换过程会保存进度、错误信息和崩溃日志，便于排查闪退。
- 生成标准 EPUB 结构，包含 `mimetype`、`container.xml`、`content.opf`、`nav.xhtml`、CSS 和章节 XHTML。
- 支持可选 EPUBCheck 校验。
- 使用 QFluentWidgets 风格界面，右侧编辑区域和章节编辑页分隔条可拖动调整大小。
- Windows 可执行文件支持应用图标和任务栏图标。

## 开发运行

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m app.main
```

也可以使用命令行转换验证核心能力：

```powershell
py -3 -m app.main --convert .\demo.txt .\demo.md .\demo.html -o .\output
```

## 测试

```powershell
py -3 -m unittest discover tests
py -3 -m compileall app tests scripts
```

## Windows 打包

默认生成启动更快的目录版：

```powershell
.\scripts\build_exe.ps1
```

输出位置：

```text
dist\EpubForge\EpubForge.exe
```

目录版不会在每次启动时解压 PySide6 运行库，适合作为日常使用版本。

如果确实需要单文件版本：

```powershell
.\scripts\build_exe.ps1 -OneFile
```

单文件输出位置：

```text
dist\EpubForge.exe
```

单文件版启动时需要先解压运行库，打开速度会明显慢于目录版。

## 图标

应用图标位于：

```text
app\assets\app.ico
```

打包脚本会把该图标写入可执行文件，并在程序启动时设置窗口和任务栏图标。

## 配置和数据

- 用户配置保存到 `%APPDATA%\EpubForge`。
- 任务记录保存到 `%APPDATA%\EpubForge\tasks.sqlite3`。
- GUI 崩溃日志会写入用户目录下的 `EpubForge\crash.log`。

## 常见问题

### 可执行文件打开慢

优先使用默认目录版 `dist\EpubForge\EpubForge.exe`。单文件版每次启动都要解压依赖，启动速度会慢很多。

### MOBI/AZW3 无法转换

需要安装 Calibre，并在设置中配置 `ebook-convert` 路径，或确保 Calibre 已加入系统 PATH。

### 设置窗口或提示框颜色异常

程序启动时会强制使用浅色主题和浅色调色板。如果仍看到黑底黑字，优先确认是否运行的是最新打包目录里的 `dist\EpubForge\EpubForge.exe`。
