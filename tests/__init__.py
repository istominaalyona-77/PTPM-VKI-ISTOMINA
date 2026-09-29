import os
import sys

# Добавляем папку src в путь импорта, чтобы тесты видели модули проекта
# при запуске командой «python -m unittest discover -v» из корня репозитория.
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
