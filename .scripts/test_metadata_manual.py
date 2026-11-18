#!/usr/bin/env python3
"""手动测试元数据文件处理模块"""

import sys
import tempfile
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from books_cli.utils.metadata_file import MetadataFile


def test_create_and_load():
    """测试创建和加载元数据文件"""
    print("测试 1: 创建元数据文件...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 准备测试数据
        book_data = {
            "title": "测试书籍",
            "author": "测试作者",
            "category": "技术",
            "tags": ["Python", "测试"],
            "status": "unread",
            "rating": 5,
            "pages": 100,
            "filesize": 1024
        }
        pdf_path = Path(tmpdir) / "test.pdf"

        # 创建元数据文件
        metadata_path = MetadataFile.create(book_data, pdf_path)

        print(f"✓ 元数据文件已创建: {metadata_path.name}")

        # 读取并显示文件内容
        with open(metadata_path, "r", encoding="utf-8") as f:
            content = f.read()
        print("\n--- 元数据文件内容 ---")
        print(content)
        print("--- 文件内容结束 ---\n")

        # 加载元数据
        loaded_data = MetadataFile.load(metadata_path)
        print("✓ 元数据已加载")

        # 验证关键字段
        assert loaded_data["title"] == "测试书籍", "标题不匹配"
        assert loaded_data["author"] == "测试作者", "作者不匹配"
        assert loaded_data["tags"] == ["Python", "测试"], "标签不匹配"
        assert loaded_data["status"] == "unread", "状态不匹配"
        assert loaded_data["rating"] == 5, "评分不匹配"
        print("✓ 所有字段验证通过")


def test_update():
    """测试更新元数据文件"""
    print("\n测试 2: 更新元数据文件...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建初始文件
        book_data = {
            "title": "原始标题",
            "author": "原始作者",
            "rating": 3
        }
        pdf_path = Path(tmpdir) / "update_test.pdf"
        metadata_path = MetadataFile.create(book_data, pdf_path)

        print(f"✓ 初始文件已创建")

        # 更新元数据
        update_data = {
            "title": "更新标题",
            "rating": 5
        }
        MetadataFile.update(metadata_path, update_data)
        print("✓ 元数据已更新")

        # 验证更新结果
        loaded_data = MetadataFile.load(metadata_path)
        assert loaded_data["title"] == "更新标题", "标题更新失败"
        assert loaded_data["author"] == "原始作者", "作者应该保持不变"
        assert loaded_data["rating"] == 5, "评分更新失败"
        print("✓ 更新验证通过")


def test_tags_parsing():
    """测试 JSON 字符串格式的标签解析"""
    print("\n测试 3: 标签字符串解析...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 使用 JSON 字符串格式的 tags
        book_data = {
            "title": "标签测试",
            "tags": '["标签A", "标签B", "标签C"]'
        }
        pdf_path = Path(tmpdir) / "tags_test.pdf"
        metadata_path = MetadataFile.create(book_data, pdf_path)

        # 加载并验证
        loaded_data = MetadataFile.load(metadata_path)
        assert loaded_data["tags"] == ["标签A", "标签B", "标签C"], "标签解析失败"
        print("✓ JSON 标签字符串解析正确")


def test_chinese_support():
    """测试中文支持"""
    print("\n测试 4: 中文支持...")

    with tempfile.TemporaryDirectory() as tmpdir:
        book_data = {
            "title": "深入理解计算机系统",
            "author": "Randal E. Bryant",
            "category": "计算机科学",
            "tags": ["操作系统", "体系结构"]
        }
        pdf_path = Path(tmpdir) / "中文测试.pdf"
        metadata_path = MetadataFile.create(book_data, pdf_path)

        # 读取文件验证编码
        with open(metadata_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "深入理解计算机系统" in content, "中文标题未正确写入"
        assert "计算机科学" in content, "中文分类未正确写入"
        assert "操作系统" in content, "中文标签未正确写入"

        # 加载验证
        loaded_data = MetadataFile.load(metadata_path)
        assert loaded_data["title"] == "深入理解计算机系统"
        assert loaded_data["category"] == "计算机科学"
        assert loaded_data["tags"] == ["操作系统", "体系结构"]
        print("✓ 中文支持正常")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("元数据文件模块测试")
    print("=" * 50)

    try:
        test_create_and_load()
        test_update()
        test_tags_parsing()
        test_chinese_support()

        print("\n" + "=" * 50)
        print("所有测试通过!")
        print("=" * 50)
        return 0
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
