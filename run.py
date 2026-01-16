#!/usr/bin/env python
"""
Скрипт для локального запуска приложения
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

from app import create_app

if __name__ == "__main__":
    app = create_app()
    
    # Параметры запуска
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🚀 Запуск приложения на http://{host}:{port}")
    print(f"📝 Веб-интерфейс: http://localhost:{port}/ui")
    print(f"❤️  Health check: http://localhost:{port}/health")
    print(f"🐛 Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)

