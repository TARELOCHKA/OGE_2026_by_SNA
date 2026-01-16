"""
Скрипт для запуска Flask приложения.
Использование: python run.py
"""
from app import create_app

if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("🚀 Запуск сервера Flask")
    print("=" * 60)
    print("📍 UI доступен по адресу: http://localhost:8080/ui")
    print("📍 Health check: http://localhost:8080/health")
    print("=" * 60)
    print("Для остановки нажмите Ctrl+C")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8080, debug=True)
