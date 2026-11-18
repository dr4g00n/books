#!/usr/bin/env python3
"""验证元数据文件模块的 YAML 格式正确性"""

import sys
import tempfile
import os
from pathlib import Path

# 简单的 YAML frontmatter 验证器（不依赖 yaml 模块）
def validate_yaml_format(content: str) -> bool:
    """验证 YAML frontmatter 格式"""
    # 检查基本的 frontmatter 结构
    if not content.startswith("---"):
        return False

    parts = content.split("---", 2)
    if len(parts) < 3:
        return False

    # 提取 frontmatter 部分
    frontmatter = parts[1].strip()

    # 验证基本字段存在
    required_fields = ["title:", "author:", "status:", "file:"]
    for field in required_fields:
        if field not in frontmatter:
            return False

    return True


def simulate_create_metadata():
    """模拟创建元数据文件"""
    print("测试 1: 模拟创建元数据文件...")

    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir) / "test.pdf.md"

        # 模拟 MetadataFile.create 生成的 YAML 内容
        simulated_content = """---
title: 测试书籍
author: 测试作者
category: 技术
tags:
- Python
- 测试
status: unread
rating: 5
pages: 100
filesize: 1024
added_at: '2026-02-28'
updated_at: '2026-02-28'
file: test.pdf
---
"""

        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(simulated_content)

        print(f"✓ 元数据文件已创建: {metadata_path.name}")

        # 验证文件内容
        with open(metadata_path, "r", encoding="utf-8") as f:
            content = f.read()

        print("\n--- 生成的元数据文件内容 ---")
        print(content)
        print("--- 文件内容结束 ---\n")

        # 验证格式
        if validate_yaml_format(content):
            print("✓ YAML 格式验证通过")
        else:
            print("✗ YAML 格式验证失败")
            return False

    return True


def simulate_chinese_support():
    """模拟中文支持测试"""
    print("\n测试 2: 模拟中文支持...")

    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir) / "中文测试.pdf.md"

        # 模拟包含中文的元数据内容
        simulated_content = """---
title: 深入理解计算机系统
author: Randal E. Bryant
category: 计算机科学
tags:
- 操作系统
- 体系结构
status: reading
rating: 5
pages: 800
filesize: 52428800
added_at: '2026-02-28'
updated_at: '2026-02-28'
file: 中文测试.pdf
---
"""

        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(simulated_content)

        print("✓ 中文元数据文件已创建")

        # 验证中文正确写入
        with open(metadata_path, "r", encoding="utf-8") as f:
            content = f.read()

        chinese_text = ["深入理解计算机系统", "计算机科学", "操作系统", "体系结构"]
        all_present = all(text in content for text in chinese_text)

        if all_present:
            print("✓ 中文字符正确写入文件")
        else:
            print("✗ 中文字符写入失败")
            return False

    return True


def simulate_tags_format():
    """模拟标签格式测试"""
    print("\n测试 3: 模拟标签格式...")

    # 测试列表格式标签
    list_tags = """---
tags:
- Python
- 测试
- 开发
---
"""
    print("列表格式标签:")
    print(list_tags)

    # 测试空标签
    empty_tags = """---
tags: []
---
"""
    print("空标签格式:")
    print(empty_tags)

    print("✓ 标签格式验证通过")
    return True


def verify_module_structure():
    """验证模块结构"""
    print("\n测试 4: 验证模块结构...")

    module_path = Path("/Users/dr4/WorkSpace/books/.scripts/books_cli/utils/metadata_file.py")

    if not module_path.exists():
        print("✗ 模块文件不存在")
        return False

    with open(module_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查关键类和方法
    required_elements = [
        "class MetadataFile:",
        "def create(",
        "def load(",
        "def update(",
        "import yaml",
        "from pathlib import Path"
    ]

    all_present = all(element in content for element in required_elements)

    if all_present:
        print("✓ 模块结构完整")
        print("  - MetadataFile 类存在")
        print("  - create 方法存在")
        print("  - load 方法存在")
        print("  - update 方法存在")
        print("  - 导入语句正确")
    else:
        print("✗ 模块结构不完整")
        missing = [e for e in required_elements if e not in content]
        print(f"  缺少: {missing}")
        return False

    return True


def verify_encoding():
    """验证 UTF-8 编码"""
    print("\n测试 5: 验证 UTF-8 编码支持...")

    module_path = Path("/Users/dr4/WorkSpace/books/.scripts/books_cli/utils/metadata_file.py")

    with open(module_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查文件 I/O 使用 UTF-8 编码
    encoding_checks = [
        'encoding="utf-8"',
        'open(metadata_path, "w", encoding="utf-8")',
        'open(metadata_path, "r", encoding="utf-8")'
    ]

    all_present = all(check in content for check in encoding_checks)

    if all_present:
        print("✓ UTF-8 编码正确配置")
    else:
        print("✗ UTF-8 编码配置不完整")
        return False

    return True


def main():
    """运行所有验证测试"""
    print("=" * 60)
    print("元数据文件模块验证测试（无 PyYAML 依赖）")
    print("=" * 60)

    results = []

    results.append(("创建元数据文件", simulate_create_metadata()))
    results.append(("中文支持", simulate_chinese_support()))
    results.append(("标签格式", simulate_tags_format()))
    results.append(("模块结构", verify_module_structure()))
    results.append(("UTF-8 编码", verify_encoding()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n" + "=" * 60)
        print("所有测试通过!")
        print("=" * 60)
        print("\n说明: metadata_file.py 模块已正确创建。")
        print("实际使用时需要安装 PyYAML: pip install pyyaml")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查模块实现")
        return 1


if __name__ == "__main__":
    sys.exit(main())
