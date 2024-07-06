# ForestEye

ForestEye - это приложение на PyQt6 для обработки и анализа фотографий с животными. Оно позволяет загружать фотографии, обнаруживать животных на них, группировать фотографии по сценам и визуализировать результаты на карте.

Сделано командой компании [MooMind](moomind.tech).


## Основные функции

- Загрузка и обработка фотографий
- Обнаружение животных на фотографиях с использованием YOLO
- Группировка фотографий по сценам
- Визуализация результатов на карте
- Экспорт данных в CSV и XLSX форматы
- Jupyter notebooks с обучением модели находятся в папке notebooks

## Требования

- Python 3.7+
- PyQt6
- ONNX Runtime
- OpenCV
- Folium
- Другие зависимости (см. requirements.txt)

## Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## Обучение модели

Jupyter notebooks с процессом обучения модели находятся в папке `notebooks`. Для просмотра и запуска notebooks, убедитесь, что у вас установлен Jupyter, и выполните:

## Установка

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/your-username/photo-analyzer.git
   cd photo-analyzer
   ```

2. Создайте и активируйте виртуальное окружение:
   ```
   python -m venv venv
   source venv/bin/activate  # Для Linux/Mac
   venv\Scripts\activate  # Для Windows
   ```

3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

## Запуск приложения

Для запуска приложения выполните следующую команду:

```
python main.py
```

## Сборка в исполняемый файл

Для создания исполняемого файла используйте PyInstaller:

```
pyinstaller --name=PhotoAnalyzer --windowed --onefile main.py
```

Исполняемый файл будет создан в папке `dist`.

## Инструкция для запуска из-под venv через Python:

1. Создайте виртуальное окружение:
   ```
   python -m venv venv
   ```

2. Активируйте виртуальное окружение:
   - Для Windows:
     ```
     venv\Scripts\activate
     ```
   - Для Linux/Mac:
     ```
     source venv/bin/activate
     ```

3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

4. Запустите приложение:
   ```
   python main.py
   ```

## Инструкция для сборки в exe:
Не проверялось, так как нет подходящего железа.

1. Установите PyInstaller:
   ```
   pip install pyinstaller
   ```

2. Соберите приложение в exe:
   ```
   pyinstaller --name=PhotoAnalyzer --windowed --onefile main.py
   ```

3. Исполняемый файл будет создан в папке `dist`.
