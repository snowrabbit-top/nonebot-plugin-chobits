"""
pyproject.toml 生成与增强工具

功能：
- 读取当前目录下的 pyproject.toml
- 保留所有已有配置（包括 [tool.nonebot] 等自定义 section）
- 补全标准打包所需的 [build-system] 和 [project] 字段（如作者、许可证、classifiers 等）
- 写回文件（安全覆盖）

使用方式：
    python generate_pyproject.py

作者：SnowRabbit
兼容 Python 版本：>=3.9
"""

import os
import sys
from pathlib import Path

# 尝试导入 TOML 读写库（兼容 Python 3.9+）
try:
    # Python 3.11+ 有内置 tomllib（只读）
    import tomllib as toml_reader
except ImportError:
    # Python < 3.11 需要 tomli
    try:
        import tomli as toml_reader
    except ImportError:
        print("错误：请安装 'tomli'（Python < 3.11）: pip install tomli", file=sys.stderr)
        sys.exit(1)

try:
    import tomli_w as toml_writer  # 用于写入 TOML
except ImportError:
    print("错误：请安装 'tomli-w' 以支持写入 TOML: pip install tomli-w", file=sys.stderr)
    sys.exit(1)


def load_pyproject_toml(filepath: Path):
    """从文件加载 pyproject.toml 为字典"""
    if not filepath.exists():
        print(f"警告：{filepath} 不存在，将创建一个新的配置。")
        return {}
    try:
        with open(filepath, "rb") as f:
            return toml_reader.load(f)
    except Exception as e:
        print(f"错误：无法读取 {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def save_pyproject_toml(filepath: Path, data: dict):
    """将字典写入 pyproject.toml 文件"""
    try:
        with open(filepath, "wb") as f:
            toml_writer.dump(data, f)
        print(f"✅ 已成功写入 {filepath}")
    except Exception as e:
        print(f"错误：无法写入 {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def merge_project_metadata(existing_project: dict) -> dict:
    """
    合并 [project] 配置：保留已有字段，补充缺失的标准字段
    """
    # 默认的打包元数据（你可以根据项目修改）
    default_project = {
        "name": "wjyzcm",  # 通常来自已有配置
        "version": "0.0.1",
        "description": "wjyzcm",
        "readme": "README.md",
        "requires-python": ">=3.9, <4.0",
        "license": {"text": "MIT"},  # 建议明确许可证
        "authors": [
            {"name": "Your Name", "email": "you@example.com"}
        ],
        "classifiers": [
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Operating System :: OS Independent",
        ],
        "dependencies": [
            "nonebot2>=2.0.0",
            "nonebot-adapter-onebot>=2.0.0",
        ],
    }

    # 优先使用已有配置中的值
    merged = default_project.copy()
    merged.update(existing_project)

    # 特别处理：如果已有 dependencies，不要覆盖
    if "dependencies" in existing_project:
        merged["dependencies"] = existing_project["dependencies"]

    return merged


def ensure_build_system(data: dict):
    """
    确保 [build-system] 存在且正确
    """
    build_system = data.get("build-system", {})
    # 如果已有 build-backend，不强制覆盖（但通常应为 setuptools）
    if "build-backend" not in build_system:
        build_system["requires"] = ["setuptools>=61.0", "wheel"]
        build_system["build-backend"] = "setuptools.build_meta"
    data["build-system"] = build_system


def enhance_pyproject():
    """主逻辑：读取、增强、写回 pyproject.toml"""
    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"

    print("🔍 正在读取当前 pyproject.toml 配置...")
    config = load_pyproject_toml(pyproject_path)

    # 1. 处理 [project]
    existing_project = config.get("project", {})
    enhanced_project = merge_project_metadata(existing_project)
    config["project"] = enhanced_project

    # 2. 确保 [build-system]
    ensure_build_system(config)

    # 3. 保留所有其他配置（如 [tool.nonebot]）
    # → 因为 config 是从原文件加载的，其他字段已存在，无需额外操作

    # 4. 写回文件
    save_pyproject_toml(pyproject_path, config)

    print("\n🎉 pyproject.toml 已成功增强！")
    print("   - 已补全 [project] 打包元数据")
    print("   - 已设置 [build-system] 使用 setuptools")
    print("   - 原有的 [tool.nonebot] 等自定义配置已保留")
    print("\n💡 建议：")
    print("   - 检查 authors 和 license 是否符合你的项目")
    print("   - 如需添加更多依赖，请编辑 dependencies 列表")


if __name__ == "__main__":
    enhance_pyproject()
