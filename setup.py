#!/usr/bin/env python3
"""
Setup script for Bitcoin Trading System with Ollama LLM
Ensures proper Python path configuration for the organized structure
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Verify the structure
def verify_structure():
    """Verify the project structure is correct"""
    required_dirs = [
        "src/sentiment",
        "src/trading", 
        "src/data",
        "src/cli",
        "src/core",
        "src/utils",
        "scripts",
        "docker",
        "docs",
        "examples",
        "tests",
        "config"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not (project_root / dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"⚠️  Missing directories: {', '.join(missing_dirs)}")
        return False
    
    print("✅ Project structure is correct")
    return True

if __name__ == "__main__":
    print("🚀 Bitcoin Trading System Setup")
    print("=" * 40)
    
    verify_structure()
    
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path includes: {src_path}")
    print("\n✅ Setup complete!")
    
    print("\n📋 Quick commands:")
    print("  python examples/main_demo.py")
    print("  python src/cli/btc_trading_cli.py --help")
    print("  python src/core/test_ollama_simple.py")