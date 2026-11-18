# Books CLI 扁平化改造设计

**日期**: 2025-02-07
**状态**: 设计阶段

## 概述

将 Books CLI 从多级目录结构改造为扁平化存储，使用 Obsidian 兼容的 tags 方式进行分类。

## 当前架构

```
books/
├── 01-网络安全/books/*.pdf
├── 02-Web安全/books/*.pdf
├── 88-开发技术/books/*.pdf
└── ...
```

## 目标架构

```
library/
├── 书籍1.pdf
├── 书籍1.pdf.md          # Obsidian 兼容元数据
├── 书籍2.pdf
├── 书籍2.pdf.md
└── ...
```

## 核心改动

### 1. 路径扁平化
- 所有书籍统一存放在 `library/` 目录
- 移除多级目录结构

### 2. 元数据文件
- 每本书配对同名 `.pdf.md` 文件
- YAML frontmatter 存储标签和属性
- 支持 Markdown 笔记内容

### 3. 标签分类
- 使用 tags 替代目录分类
- 支持多标签：`["#安全", "#Rust", "#书籍"]`

### 4. 数据库扩展
- 新增 `tags` 字段（JSON 数组）
- 新增 `metadata_file` 字段

## 实施步骤

### 阶段 1：数据结构
- [ ] 修改数据库模型
- [ ] 创建 library/ 目录
- [ ] 更新配置文件

### 阶段 2：迁移功能
- [ ] 实现 migrate 命令
- [ ] 元数据文件生成逻辑
- [ ] 测试数据迁移

### 阶段 3：CLI 改造
- [ ] 修改 organize 命令
- [ ] 扩展 query 命令
- [ ] 修改 edit 命令

### 阶段 4：交互式菜单
- [ ] 更新 start.sh

## 元数据文件格式

```yaml
---
title: 书名
author: 作者
tags:
  - #安全
  - #Rust
  - #书籍
status: unread
rating: 0
file: 书名.pdf
---
```
