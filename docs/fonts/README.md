# 字体说明

本目录用于保证课程提交包在不同机器上打开 README 与 TeX 文档时，中文字体风格尽量一致。

## 包含字体

- `NotoSansSC-VF.ttf`
- `NotoSerifSC-VF.ttf`

## 使用位置

- `README.md`（表格排版的中文 fallback 字体）
- `docs/AI使用说明.tex`（XeLaTeX 编译时优先读取本地字体）

## 说明

- 字体文件来源于本机系统字体目录中的 Noto SC 字体。
- 若目标机器缺少系统中文字体，文档会优先使用本目录字体。
