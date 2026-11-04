# 构建读者版

在仓库根目录运行：

```sh
python3 -m pip install -r tools/requirements.txt
python3 tools/build.py
```

另需安装Pandoc，或安装pypandoc_binary以使用其同捆Pandoc。WeasyPrint需要Pango及其系统依赖；Linux可按WeasyPrint官方安装文档配置。现有字体子集随仓库提供，无需网络字体或私有源仓库。支持Python 3.10或更高版本。

输出位于`dist/<formal_version>/`（当前`dist/zh-v1.0.1/`）；旧版根目录文件与原发布资产保留。章节顺序按`book.json`的`display_order`，不按稳定ID排列。逐章Markdown及前言、版权、参考文献是排版的权威输入；`manuscript/zh-CN/book.md`是完整便携阅读稿。PDF采用A5，嵌入Reader Serif SC字体，含页码、目录页码与可点击内部链接；EPUB 3含导航与嵌入字体。

字体来自Noto Serif CJK SC，遵循SIL Open Font License 1.1；经子集化和重命名，修改后字体名为Reader Serif SC。保留Glyph ID以兼容多个PDF渲染器。许可及版权在`assets/fonts/Noto-CJK-LICENSE.txt`。本仓库书稿许可不改变字体许可。

字体子集覆盖本版所用字符。增加新字符时，构建器会明确报缺字，应使用合法的Noto CJK原始字体更新子集，保留许可和Glyph ID，不可忽略报错。正文改动后应重新渲染检查，而不是仅检查文件存在。

验证命令见`tools/validate.py`。本构建不要求账号、密钥、私有文件或AI服务。PDF底层对象编号可能因依赖版本而变；内容、结构与字体可重建，不承诺跨系统二进制哈希一致。
