# Руководство по использованию Appium Inspector

## Что такое Appium Inspector?

Appium Inspector - это визуальный инструмент для анализа элементов мобильного приложения. Он позволяет:
- Просматривать структуру экрана
- Получать селекторы элементов (ID, XPath, Accessibility ID)
- Тестировать взаимодействие с элементами
- Делать скриншоты

## Установка Appium Inspector

### Вариант 1: Через Appium Desktop (рекомендуется)

1. Скачайте Appium Desktop: https://github.com/appium/appium-desktop/releases
2. Установите приложение
3. Запустите Appium Desktop

### Вариант 2: Через npm (если уже установлен Node.js)

```bash
npm install -g appium-inspector
```

## Подключение к устройству

### Шаг 1: Запустите Appium сервер

```bash
appium
```

Или через Appium Desktop:
- Откройте Appium Desktop
- Нажмите "Start Server"

### Шаг 2: Настройте Desired Capabilities

В Appium Inspector нажмите "Start Session" и укажите:

```json

```

**Или используйте Quick Start:**
- Remote Host: `localhost`
- Remote Port: `4723`
- Remote Path: `/wd/hub` (или оставьте пустым для Appium 2.x)

### Шаг 3: Подключитесь

Нажмите "Start Session" - откроется окно с вашим приложением.

## Поиск кнопки в Appium Inspector

### Шаг 1: Найдите кнопку визуально

1. В левой части экрана вы увидите структуру элементов (XML дерево)
2. В правой части - визуальное представление приложения
3. Наведите курсор на элемент в XML дереве - он подсветится на экране

### Шаг 2: Получите селекторы

Кликните на элемент в XML дереве. Внизу появятся доступные селекторы:

#### 1. Resource ID (самый надежный)
```
resource-id: com.example.app:id/login_button
```
**В коде:**
```python
AppiumBy.ID, "com.example.app:id/login_button"
```

#### 2. XPath
```
xpath: //android.widget.Button[@resource-id='com.example.app:id/login_button']
```
**В коде:**
```python
AppiumBy.XPATH, "//android.widget.Button[@resource-id='com.example.app:id/login_button']"
```

#### 3. Accessibility ID (content-desc)
```
content-desc: Login Button
```
**В коде:**
```python
AppiumBy.ACCESSIBILITY_ID, "Login Button"
```

#### 4. Текст кнопки
```
text: Войти
```
**В коде:**
```python
AppiumBy.XPATH, "//android.widget.Button[@text='Войти']"
```

#### 5. Класс элемента
```
class: android.widget.Button
```
**В коде:**
```python
AppiumBy.CLASS_NAME, "android.widget.Button"
```

## Примеры использования селекторов

### Пример 1: Поиск по Resource ID (рекомендуется)

```python
from appium.webdriver.common.appiumby import AppiumBy

# Если ID полный
button = driver.find_element(
    AppiumBy.ID, 
    "com.example.app:id/login_button"
)

# Если ID короткий (только после двоеточия)
button = driver.find_element(
    AppiumBy.ID, 
    "login_button"
)
```

### Пример 2: Поиск по тексту

```python
button = driver.find_element(
    AppiumBy.XPATH, 
    "//android.widget.Button[@text='Войти']"
)

# Или по части текста
button = driver.find_element(
    AppiumBy.XPATH, 
    "//android.widget.Button[contains(@text, 'Вход')]"
)
```

### Пример 3: Поиск по Accessibility ID

```python
button = driver.find_element(
    AppiumBy.ACCESSIBILITY_ID, 
    "Login Button"
)
```

## Полезные функции Appium Inspector

### 1. Поиск элементов
- Используйте поле "Search" для поиска по тексту или ID
- Фильтруйте по типу элемента (Button, TextView, etc.)

### 2. Тестирование действий
- Кликните "Tap" для проверки клика
- Используйте "Send Keys" для ввода текста
- Проверьте "Selected" для переключателей

### 3. Скриншоты
- Нажмите "Screenshot" для сохранения текущего экрана

### 4. Обновление структуры
- Нажмите "Refresh" для обновления структуры после действий

## Советы по выбору селектора

1. **Resource ID** - самый надежный, используйте его в первую очередь
2. **Accessibility ID** - хорош, если доступен
3. **XPath по тексту** - используйте, если ID недоступен
4. **XPath по классу** - последний вариант, менее надежен

## Типичные проблемы

### Проблема: Элемент не находится
- Проверьте, что приложение на нужном экране
- Обновите структуру (Refresh)
- Попробуйте другой селектор

### Проблема: ID меняется
- Используйте частичный XPath
- Ищите по тексту или Accessibility ID

### Проблема: Элемент появляется не сразу
- Используйте WebDriverWait для ожидания
- Увеличьте таймаут

