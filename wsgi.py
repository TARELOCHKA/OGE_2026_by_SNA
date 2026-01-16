import os
import sys
from pathlib import Path

# Убеждаемся, что корень проекта в PYTHONPATH
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app import create_app

app = create_app()

# Проверка при импорте (только для отладки)
if __name__ == "__main__":
    print(f"[DEBUG] Python path: {sys.path}")
    print(f"[DEBUG] Working directory: {os.getcwd()}")
    print(f"[DEBUG] Project root: {project_root}")
