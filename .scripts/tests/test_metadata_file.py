"""测试元数据文件处理模块"""

import pytest
from pathlib import Path
import tempfile
import yaml
from books_cli.utils.metadata_file import MetadataFile


class TestMetadataFile:
    """测试 MetadataFile 类"""

    def test_create_metadata_file(self):
        """测试创建元数据文件"""
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

            # 验证文件存在
            assert metadata_path.exists()
            assert metadata_path.name == "test.pdf.md"

            # 验证文件内容格式
            with open(metadata_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 验证 frontmatter 格式
            assert content.startswith("---")
            assert content.endswith("---\n\n")

            # 解析并验证 YAML 内容
            parts = content.split("---", 2)
            frontmatter_data = yaml.safe_load(parts[1])

            assert frontmatter_data["title"] == "测试书籍"
            assert frontmatter_data["author"] == "测试作者"
            assert frontmatter_data["category"] == "技术"
            assert frontmatter_data["tags"] == ["Python", "测试"]
            assert frontmatter_data["status"] == "unread"
            assert frontmatter_data["rating"] == 5
            assert frontmatter_data["pages"] == 100
            assert frontmatter_data["filesize"] == 1024
            assert frontmatter_data["file"] == "test.pdf"

    def test_load_metadata_file(self):
        """测试加载元数据文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            book_data = {
                "title": "加载测试",
                "author": "作者",
                "tags": ["标签1"]
            }
            pdf_path = Path(tmpdir) / "load_test.pdf"
            metadata_path = MetadataFile.create(book_data, pdf_path)

            # 加载元数据
            loaded_data = MetadataFile.load(metadata_path)

            # 验证加载的数据
            assert loaded_data["title"] == "加载测试"
            assert loaded_data["author"] == "作者"
            assert loaded_data["tags"] == ["标签1"]

    def test_update_metadata_file(self):
        """测试更新元数据文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建初始文件
            book_data = {
                "title": "原始标题",
                "author": "原始作者",
                "rating": 3
            }
            pdf_path = Path(tmpdir) / "update_test.pdf"
            metadata_path = MetadataFile.create(book_data, pdf_path)

            # 更新元数据
            update_data = {
                "title": "更新标题",
                "rating": 5
            }
            MetadataFile.update(metadata_path, update_data)

            # 验证更新结果
            loaded_data = MetadataFile.load(metadata_path)
            assert loaded_data["title"] == "更新标题"
            assert loaded_data["author"] == "原始作者"  # 保持不变
            assert loaded_data["rating"] == 5

    def test_tags_string_parsing(self):
        """测试 tags 字符串解析"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 使用 JSON 字符串格式的 tags
            book_data = {
                "title": "标签测试",
                "tags": '["标签A", "标签B", "标签C"]'
            }
            pdf_path = Path(tmpdir) / "tags_test.pdf"
            metadata_path = MetadataFile.create(book_data, pdf_path)

            # 加载并验证 tags 已正确解析
            loaded_data = MetadataFile.load(metadata_path)
            assert loaded_data["tags"] == ["标签A", "标签B", "标签C"]

    def test_empty_metadata_file(self):
        """测试空元数据处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 使用空数据创建
            book_data = {}
            pdf_path = Path(tmpdir) / "empty.pdf"
            metadata_path = MetadataFile.create(book_data, pdf_path)

            # 验证默认值
            loaded_data = MetadataFile.load(metadata_path)
            assert loaded_data["title"] == ""
            assert loaded_data["status"] == "unread"
            assert loaded_data["rating"] == 0
            assert loaded_data["pages"] == 0
