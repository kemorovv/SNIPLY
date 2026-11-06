"""
Generates comprehensive English and Russian translation JSON dictionaries for SNIPLY.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRANSLATIONS_DIR = PROJECT_ROOT / "resources" / "translations"

TRANSLATIONS = {
    # App Identity
    "app.name": {"en": "SNIPLY", "ru": "SNIPLY"},
    "app.tagline": {"en": "Your clipboard. Reimagined.", "ru": "Ваш буфер обмена. Переосмыслен."},
    "app.version_label": {"en": "v{version}", "ru": "v{version}"},

    # Main Navigation
    "navigation.all_clips": {"en": "All Clips", "ru": "Вся история"},
    "navigation.pinned": {"en": "Pinned", "ru": "Закреплённое"},
    "navigation.favorites": {"en": "Favorites", "ru": "Избранное"},
    "navigation.collections": {"en": "Collections", "ru": "Коллекции"},
    "navigation.colors": {"en": "Colors", "ru": "Цвета"},
    "navigation.images": {"en": "Images", "ru": "Изображения"},
    "navigation.snippets": {"en": "Snippets", "ru": "Шаблоны"},
    "navigation.insights": {"en": "Insights", "ru": "Статистика"},
    "navigation.settings": {"en": "Settings", "ru": "Настройки"},
    "navigation.collapse_sidebar": {"en": "Collapse sidebar", "ru": "Свернуть боковую панель"},
    "navigation.expand_sidebar": {"en": "Expand sidebar", "ru": "Развернуть боковую панель"},

    # Sidebar Footer & Status
    "sidebar.storage_usage": {"en": "Storage: {size}", "ru": "Хранилище: {size}"},
    "sidebar.privacy_active": {"en": "Local & Private", "ru": "Локально и приватно"},
    "sidebar.monitoring_active": {"en": "Monitoring Active", "ru": "Мониторинг активен"},
    "sidebar.monitoring_paused": {"en": "Monitoring Paused", "ru": "Мониторинг на паузе"},
    "sidebar.demo_mode": {"en": "Demo Gallery", "ru": "Демо-режим"},

    # Top Bar & Search
    "search.placeholder": {"en": "Search clips, types, tags, or collections...", "ru": "Поиск по тексту, типам, тегам или коллекциям..."},
    "search.quick_paste_placeholder": {"en": "Type to search clipboard history...", "ru": "Введите запрос для поиска в буфере обмена..."},
    "search.snippets_placeholder": {"en": "Search templates by name, category, or tag...", "ru": "Поиск шаблонов по названию, категории или тегу..."},
    "search.colors_placeholder": {"en": "Search colors by HEX, RGB, or HSL...", "ru": "Поиск цветов по HEX, RGB или HSL..."},

    # Filters
    "filter.label": {"en": "Filter", "ru": "Фильтр"},
    "filter.all": {"en": "All Types", "ru": "Все типы"},
    "filter.text": {"en": "Text", "ru": "Текст"},
    "filter.image": {"en": "Images", "ru": "Изображения"},
    "filter.color": {"en": "Colors", "ru": "Цвета"},
    "filter.url": {"en": "URLs", "ru": "Ссылки"},
    "filter.code": {"en": "Code", "ru": "Код"},
    "filter.json": {"en": "JSON", "ru": "JSON"},
    "filter.email": {"en": "Email", "ru": "Email"},
    "filter.favorites": {"en": "Favorites Only", "ru": "Только избранное"},
    "filter.pinned": {"en": "Pinned Only", "ru": "Только закреплённое"},

    # Sorting
    "sort.label": {"en": "Sort", "ru": "Сортировка"},
    "sort.recent_copied": {"en": "Recently Copied", "ru": "Недавно скопированные"},
    "sort.recent_used": {"en": "Recently Used", "ru": "Недавно использованные"},
    "sort.oldest": {"en": "Oldest First", "ru": "Сначала старые"},
    "sort.most_used": {"en": "Most Frequently Copied", "ru": "Часто используемые"},

    # View Modes
    "view.list": {"en": "List View", "ru": "Список"},
    "view.grid": {"en": "Grid View", "ru": "Сетка"},
    "view.toggle_inspector": {"en": "Toggle Inspector", "ru": "Панель деталей"},

    # Content Type Labels
    "type.text": {"en": "Plain Text", "ru": "Текст"},
    "type.color": {"en": "Color", "ru": "Цвет"},
    "type.url": {"en": "Link", "ru": "Ссылка"},
    "type.json": {"en": "JSON", "ru": "JSON"},
    "type.code": {"en": "Code", "ru": "Код"},
    "type.email": {"en": "Email", "ru": "Email"},
    "type.image": {"en": "Image", "ru": "Изображение"},

    # Pluralized Item Counts
    "items.count.one": {"en": "{count} item", "ru": "{count} элемент"},
    "items.count.few": {"en": "{count} items", "ru": "{count} элемента"},
    "items.count.many": {"en": "{count} items", "ru": "{count} элементов"},

    "clips.count.one": {"en": "{count} clip", "ru": "{count} запись"},
    "clips.count.few": {"en": "{count} clips", "ru": "{count} записи"},
    "clips.count.many": {"en": "{count} clips", "ru": "{count} записей"},

    "words.count.one": {"en": "{count} word", "ru": "{count} слово"},
    "words.count.few": {"en": "{count} words", "ru": "{count} слова"},
    "words.count.many": {"en": "{count} words", "ru": "{count} слов"},

    "chars.count.one": {"en": "{count} character", "ru": "{count} символ"},
    "chars.count.few": {"en": "{count} characters", "ru": "{count} символа"},
    "chars.count.many": {"en": "{count} characters", "ru": "{count} символов"},

    "lines.count.one": {"en": "{count} line", "ru": "{count} строка"},
    "lines.count.few": {"en": "{count} lines", "ru": "{count} строки"},
    "lines.count.many": {"en": "{count} lines", "ru": "{count} строк"},

    "uses.count.one": {"en": "Used {count} time", "ru": "Использовано {count} раз"},
    "uses.count.few": {"en": "Used {count} times", "ru": "Использовано {count} раза"},
    "uses.count.many": {"en": "Used {count} times", "ru": "Использовано {count} раз"},

    # Relative Timestamps
    "time.just_now": {"en": "Copied just now", "ru": "Скопировано только что"},
    "time.seconds_ago.one": {"en": "Copied {count} second ago", "ru": "Скопировано {count} секунду назад"},
    "time.seconds_ago.few": {"en": "Copied {count} seconds ago", "ru": "Скопировано {count} секунды назад"},
    "time.seconds_ago.many": {"en": "Copied {count} seconds ago", "ru": "Скопировано {count} секунд назад"},
    "time.minutes_ago.one": {"en": "Copied {count} minute ago", "ru": "Скопировано {count} минуту назад"},
    "time.minutes_ago.few": {"en": "Copied {count} minutes ago", "ru": "Скопировано {count} минуты назад"},
    "time.minutes_ago.many": {"en": "Copied {count} minutes ago", "ru": "Скопировано {count} минут назад"},
    "time.hours_ago.one": {"en": "Copied {count} hour ago", "ru": "Скопировано {count} час назад"},
    "time.hours_ago.few": {"en": "Copied {count} hours ago", "ru": "Скопировано {count} часа назад"},
    "time.hours_ago.many": {"en": "Copied {count} hours ago", "ru": "Скопировано {count} часов назад"},
    "time.days_ago.one": {"en": "Copied {count} day ago", "ru": "Скопировано {count} день назад"},
    "time.days_ago.few": {"en": "Copied {count} days ago", "ru": "Скопировано {count} дня назад"},
    "time.days_ago.many": {"en": "Copied {count} days ago", "ru": "Скопировано {count} дней назад"},

    # Common Actions & Context Menu
    "action.copy": {"en": "Copy", "ru": "Копировать"},
    "action.restore": {"en": "Restore to Clipboard", "ru": "Восстановить в буфер"},
    "action.pin": {"en": "Pin", "ru": "Закрепить"},
    "action.unpin": {"en": "Unpin", "ru": "Открепить"},
    "action.favorite": {"en": "Add to Favorites", "ru": "В избранное"},
    "action.unfavorite": {"en": "Remove from Favorites", "ru": "Убрать из избранного"},
    "action.add_to_collection": {"en": "Move to Collection", "ru": "Переместить в коллекцию"},
    "action.remove_from_collection": {"en": "Remove from Collection", "ru": "Убрать из коллекции"},
    "action.view_details": {"en": "View Details", "ru": "Показать детали"},
    "action.delete": {"en": "Delete", "ru": "Удалить"},
    "action.delete_selected": {"en": "Delete Selected ({count})", "ru": "Удалить выбранные ({count})"},
    "action.save": {"en": "Save", "ru": "Сохранить"},
    "action.cancel": {"en": "Cancel", "ru": "Отмена"},
    "action.create": {"en": "Create", "ru": "Создать"},
    "action.edit": {"en": "Edit", "ru": "Редактировать"},
    "action.duplicate": {"en": "Duplicate", "ru": "Дублировать"},
    "action.export": {"en": "Export", "ru": "Экспортировать"},
    "action.import": {"en": "Import", "ru": "Импортировать"},
    "action.clear_history": {"en": "Clear History", "ru": "Очистить историю"},
    "action.open_url": {"en": "Open in Browser", "ru": "Открыть в браузере"},
    "action.copy_hex": {"en": "Copy HEX", "ru": "Копировать HEX"},
    "action.copy_rgb": {"en": "Copy RGB", "ru": "Копировать RGB"},
    "action.copy_hsl": {"en": "Copy HSL", "ru": "Копировать HSL"},
    "action.copy_formatted_json": {"en": "Copy Formatted JSON", "ru": "Копировать форматированный JSON"},
    "action.copy_minified_json": {"en": "Copy Minified JSON", "ru": "Копировать компактный JSON"},
    "action.copy_original": {"en": "Copy Original", "ru": "Копировать оригинал"},
    "action.save_image_as": {"en": "Save Image to Disk...", "ru": "Сохранить изображение на диск..."},

    # Toast Notifications
    "toast.copied": {"en": "Copied to clipboard", "ru": "Скопировано в буфер обмена"},
    "toast.restored": {"en": "Restored to clipboard", "ru": "Восстановлено в буфер обмена"},
    "toast.pinned": {"en": "Entry pinned", "ru": "Запись закреплена"},
    "toast.unpinned": {"en": "Entry unpinned", "ru": "Запись откреплена"},
    "toast.favorited": {"en": "Added to favorites", "ru": "Добавлено в избранное"},
    "toast.unfavorited": {"en": "Removed from favorites", "ru": "Удалено из избранного"},
    "toast.deleted": {"en": "Entry deleted", "ru": "Запись удалена"},
    "toast.saved": {"en": "Changes saved", "ru": "Изменения сохранены"},
    "toast.monitoring_paused": {"en": "Clipboard monitoring paused", "ru": "Мониторинг буфера обмена приостановлен"},
    "toast.monitoring_resumed": {"en": "Clipboard monitoring resumed", "ru": "Мониторинг буфера обмена возобновлён"},
    "toast.sensitive_skipped": {"en": "Sensitive content filtered for privacy", "ru": "Конфиденциальные данные пропущены"},
    "toast.image_too_large": {"en": "Image exceeds maximum configured size ({size} MB)", "ru": "Изображение превышает лимит размера ({size} МБ)"},
    "toast.backup_created": {"en": "Database backup saved successfully", "ru": "Резервная копия базы данных сохранена"},
    "toast.export_success": {"en": "Data exported successfully", "ru": "Данные успешно экспортированы"},
    "toast.import_success": {"en": "Data imported successfully", "ru": "Данные успешно импортированы"},

    # Empty States
    "empty.history.title": {"en": "Your clipboard history is empty", "ru": "История буфера обмена пуста"},
    "empty.history.subtitle": {"en": "Copy any text, color, URL, JSON, code snippet, or image — SNIPLY will organize it automatically.", "ru": "Скопируйте текст, цвет, ссылку, JSON, фрагмент кода или изображение — SNIPLY автоматически распознает и сохранит их."},
    "empty.search.title": {"en": "No matching entries found", "ru": "Ничего не найдено"},
    "empty.search.subtitle": {"en": "Try adjusting your search query or clearing active filters.", "ru": "Попробуйте изменить поисковый запрос или сбросить активные фильтры."},
    "empty.pinned.title": {"en": "No pinned items yet", "ru": "Нет закреплённых элементов"},
    "empty.pinned.subtitle": {"en": "Pin essential clips so they stay at the top and are never removed during cleanup.", "ru": "Закрепляйте важные записи, чтобы они всегда оставались наверху и были защищены от автоочистки."},
    "empty.favorites.title": {"en": "No favorite items yet", "ru": "В избранном пока пусто"},
    "empty.favorites.subtitle": {"en": "Star your most useful clipboard items for instant access.", "ru": "Отмечайте звёздочкой важные записи для быстрого доступа."},
    "empty.images.title": {"en": "No copied images yet", "ru": "Нет скопированных изображений"},
    "empty.images.subtitle": {"en": "Screenshots and copied images will appear here in a responsive visual grid.", "ru": "Скриншоты и скопированные изображения будут отображаться здесь в виде удобной галереи."},
    "empty.colors.title": {"en": "No recognized colors yet", "ru": "Распознанных цветов пока нет"},
    "empty.colors.subtitle": {"en": "Copy any HEX (#A78BFA) or RGB color code to build your palette.", "ru": "Скопируйте любой цветовой код HEX (#A78BFA) или RGB, чтобы собрать палитру."},
    "empty.snippets.title": {"en": "No snippets created yet", "ru": "Шаблоны ещё не созданы"},
    "empty.snippets.subtitle": {"en": "Save reusable prompts, code templates, commands, and email replies.", "ru": "Сохраняйте часто используемые ответы, промпты, команды и шаблоны кода."},

    # Demo Mode Banner
    "demo.banner_text": {"en": "Demonstration Gallery Active — Showing sample items to preview SNIPLY recognition. Your real clipboard history is untouched.", "ru": "Активен демо-режим — показаны примеры для демонстрации распознавания SNIPLY. Ваша реальная история не затронута."},
    "demo.exit_button": {"en": "Exit Demo Mode", "ru": "Выйти из демо-режима"},
    "demo.enter_button": {"en": "Preview Demo Gallery", "ru": "Посмотреть демо-примеры"},
    "demo.badge": {"en": "EXAMPLE", "ru": "ПРИМЕР"},

    # Inspector Panel
    "inspector.title": {"en": "Inspector", "ru": "Инспектор"},
    "inspector.no_selection": {"en": "Select an item to inspect its details, metadata, and format actions.", "ru": "Выберите элемент для просмотра подробной информации, метаданных и быстрых действий."},
    "inspector.copied_at": {"en": "Copied", "ru": "Скопировано"},
    "inspector.last_used": {"en": "Last Used", "ru": "Использовано"},
    "inspector.usage_count": {"en": "Usage Count", "ru": "Количество использований"},
    "inspector.collection": {"en": "Collection", "ru": "Коллекция"},
    "inspector.no_collection": {"en": "Unassigned", "ru": "Без коллекции"},
    "inspector.tags": {"en": "Tags", "ru": "Теги"},
    "inspector.add_tag_placeholder": {"en": "Add tag + Enter...", "ru": "Добавить тег + Enter..."},
    "inspector.reading_time": {"en": "Est. reading time: {seconds} sec", "ru": "Время чтения: ~{seconds} сек"},
    "inspector.dimensions": {"en": "Dimensions", "ru": "Разрешение"},
    "inspector.file_size": {"en": "File Size", "ru": "Размер файла"},
    "inspector.format": {"en": "Format", "ru": "Формат"},
    "inspector.domain": {"en": "Domain", "ru": "Домен"},
    "inspector.language": {"en": "Language", "ru": "Язык"},
    "inspector.json_valid": {"en": "Valid JSON", "ru": "Корректный JSON"},
    "inspector.json_invalid": {"en": "Malformed JSON", "ru": "Ошибка синтаксиса JSON"},
    "inspector.json_tree": {"en": "Structure Tree", "ru": "Дерево структуры"},
    "inspector.color_conversions": {"en": "Color Conversions", "ru": "Цветовые форматы"},
    "inspector.alpha": {"en": "Alpha", "ru": "Прозрачность (Alpha)"},

    # Quick Paste Window
    "quick_paste.title": {"en": "Quick Paste", "ru": "Быстрая вставка"},
    "quick_paste.hint": {"en": "↑↓ Navigate  •  Enter Copy/Paste  •  Ctrl+F Search  •  Esc Close", "ru": "↑↓ Навигация  •  Enter Вставить  •  Ctrl+F Поиск  •  Esc Закрыть"},
    "quick_paste.pinned_badge": {"en": "PINNED", "ru": "ЗАКРЕПЛЕНО"},

    # Collections View
    "collections.new_button": {"en": "New Collection", "ru": "Новая коллекция"},
    "collections.edit_title": {"en": "Edit Collection", "ru": "Редактировать коллекцию"},
    "collections.create_title": {"en": "Create Collection", "ru": "Создать коллекцию"},
    "collections.name_label": {"en": "Collection Name", "ru": "Название коллекции"},
    "collections.description_label": {"en": "Description", "ru": "Описание"},
    "collections.color_label": {"en": "Accent Color", "ru": "Цвет метки"},
    "collections.icon_label": {"en": "Icon", "ru": "Иконка"},
    "collections.delete_title": {"en": "Delete Collection", "ru": "Удаление коллекции"},
    "collections.delete_prompt": {"en": "How would you like to handle entries inside '{name}'?", "ru": "Как поступить с записями внутри коллекции «{name}»?"},
    "collections.keep_entries": {"en": "Keep entries (remove collection assignment only)", "ru": "Сохранить записи (только убрать привязку к коллекции)"},
    "collections.delete_entries": {"en": "Delete collection and all its unpinned entries", "ru": "Удалить коллекцию вместе со всеми незакреплёнными записями"},

    # Snippets View
    "snippets.new_button": {"en": "New Snippet", "ru": "Новый шаблон"},
    "snippets.create_title": {"en": "Create Snippet", "ru": "Создать шаблон"},
    "snippets.edit_title": {"en": "Edit Snippet", "ru": "Редактировать шаблон"},
    "snippets.name_label": {"en": "Snippet Title", "ru": "Название шаблона"},
    "snippets.description_label": {"en": "Description", "ru": "Описание"},
    "snippets.category_label": {"en": "Category", "ru": "Категория"},
    "snippets.tags_label": {"en": "Tags (comma-separated)", "ru": "Теги (через запятую)"},
    "snippets.content_label": {"en": "Template Content", "ru": "Содержимое шаблона"},

    # Colors View
    "colors.export_palette": {"en": "Export Palette (JSON/CSS)", "ru": "Экспорт палитры (JSON/CSS)"},
    "colors.copied_format": {"en": "Copied {format}: {value}", "ru": "Скопирован {format}: {value}"},

    # Insights / Statistics View
    "insights.subtitle": {"en": "Real-time analytics computed strictly from your local database", "ru": "Аналитика в реальном времени на основе вашей локальной базы данных"},
    "insights.total_clips": {"en": "Total Captured Items", "ru": "Всего записей"},
    "insights.text_clips": {"en": "Text & Code Entries", "ru": "Текст и код"},
    "insights.image_clips": {"en": "Image Entries", "ru": "Изображения"},
    "insights.color_clips": {"en": "Color Swatches", "ru": "Цветовые образцы"},
    "insights.top_copied": {"en": "Most Frequently Used Clips", "ru": "Самые используемые записи"},
    "insights.top_collections": {"en": "Collections Breakdown", "ru": "Распределение по коллекциям"},
    "insights.daily_activity": {"en": "Activity Over the Last 7 Days", "ru": "Активность за последние 7 дней"},
    "insights.type_distribution": {"en": "Content Type Distribution", "ru": "Распределение по типам данных"},

    # Settings View
    "settings.tab.general": {"en": "General", "ru": "Общие"},
    "settings.tab.appearance": {"en": "Appearance", "ru": "Внешний вид"},
    "settings.tab.clipboard": {"en": "Clipboard & Privacy", "ru": "Буфер и приватность"},
    "settings.tab.shortcuts": {"en": "Shortcuts", "ru": "Горячие клавиши"},
    "settings.tab.storage": {"en": "Storage & Backup", "ru": "Хранилище и резерв"},
    "settings.tab.about": {"en": "About", "ru": "О программе"},

    # Settings - General
    "settings.general.language": {"en": "Interface Language", "ru": "Язык интерфейса"},
    "settings.general.language_desc": {"en": "Switch the entire application language immediately.", "ru": "Мгновенное переключение языка всего интерфейса приложения."},
    "settings.general.launch_startup": {"en": "Launch SNIPLY at Windows startup", "ru": "Запускать SNIPLY при входе в Windows"},
    "settings.general.start_minimized": {"en": "Start minimized in system tray", "ru": "Запускать свёрнутым в системный трей"},
    "settings.general.minimize_to_tray": {"en": "Minimize to system tray", "ru": "Сворачивать в системный трей"},
    "settings.general.close_to_tray": {"en": "Keep running in system tray when main window is closed", "ru": "Оставлять в системном трее при закрытии главного окна"},
    "settings.general.auto_start_monitoring": {"en": "Start clipboard monitoring automatically on launch", "ru": "Автоматически начинать мониторинг буфера при запуске"},
    "settings.general.auto_paste": {"en": "Automatically paste into previous window on Quick Paste selection", "ru": "Автоматически вставлять в предыдущее окно при выборе в Быстрой вставке"},

    # Settings - Appearance
    "settings.appearance.theme": {"en": "Theme Mode", "ru": "Тема оформления"},
    "settings.appearance.theme_dark": {"en": "Premium Dark (#17181C)", "ru": "Премиальная тёмная (#17181C)"},
    "settings.appearance.theme_light": {"en": "Clean Light", "ru": "Светлая"},
    "settings.appearance.accent": {"en": "Primary Accent Color", "ru": "Основной акцентный цвет"},
    "settings.appearance.density": {"en": "Interface Density", "ru": "Плотность интерфейса"},
    "settings.appearance.density_comfortable": {"en": "Comfortable", "ru": "Комфортная"},
    "settings.appearance.density_compact": {"en": "Compact", "ru": "Компактная"},
    "settings.appearance.reduced_motion": {"en": "Reduced motion (disable UI micro-animations)", "ru": "Уменьшение движения (отключить микроанимации)"},
    "settings.appearance.sidebar_collapsed": {"en": "Collapse sidebar by default", "ru": "Сворачивать боковую панель по умолчанию"},

    # Settings - Clipboard & Privacy
    "settings.clipboard.monitoring_enabled": {"en": "Enable real-time clipboard monitoring", "ru": "Включить мониторинг буфера обмена в реальном времени"},
    "settings.clipboard.max_history": {"en": "Maximum history entries", "ru": "Максимальное количество записей в истории"},
    "settings.clipboard.retention_period": {"en": "Automatic cleanup period", "ru": "Период автоматической очистки"},
    "settings.clipboard.retention_1d": {"en": "1 Day", "ru": "1 день"},
    "settings.clipboard.retention_7d": {"en": "7 Days", "ru": "7 дней"},
    "settings.clipboard.retention_30d": {"en": "30 Days", "ru": "30 дней"},
    "settings.clipboard.retention_90d": {"en": "90 Days", "ru": "90 дней"},
    "settings.clipboard.retention_never": {"en": "Never (Keep indefinitely)", "ru": "Никогда (хранить бессрочно)"},
    "settings.clipboard.deduplicate": {"en": "Merge duplicate copies and move existing item to top", "ru": "Объединять дубликаты и поднимать существующую запись наверх"},
    "settings.clipboard.save_images": {"en": "Capture and store copied images", "ru": "Сохранять скопированные изображения"},
    "settings.clipboard.max_image_mb": {"en": "Maximum image size (MB)", "ru": "Максимальный размер изображения (МБ)"},
    "settings.clipboard.filter_sensitive": {"en": "Filter obvious passwords, private keys, and API tokens", "ru": "Фильтровать очевидные пароли, приватные ключи и API-токены"},
    "settings.clipboard.excluded_apps": {"en": "Excluded Applications (Process Names)", "ru": "Исключённые приложения (имена процессов)"},
    "settings.clipboard.excluded_apps_desc": {"en": "Clipboard changes made while these executables are in the foreground will be ignored.", "ru": "Изменения буфера обмена в этих программах будут игнорироваться."},
    "settings.clipboard.add_exclusion_placeholder": {"en": "e.g., KeePassXC.exe", "ru": "например, KeePassXC.exe"},
    "settings.clipboard.add_exclusion_btn": {"en": "Add Process", "ru": "Добавить процесс"},
    "settings.clipboard.remove_exclusion_btn": {"en": "Remove Selected", "ru": "Удалить выбранный"},

    # Settings - Shortcuts
    "settings.shortcuts.quick_paste": {"en": "Open Quick Paste Popup", "ru": "Открыть окно Быстрой вставки"},
    "settings.shortcuts.main_window": {"en": "Toggle Main SNIPLY Window", "ru": "Показать / скрыть главное окно SNIPLY"},
    "settings.shortcuts.pause_monitoring": {"en": "Pause / Resume Clipboard Monitoring", "ru": "Пауза / возобновление мониторинга"},
    "settings.shortcuts.conflict_warning": {"en": "Shortcut conflict detected: '{shortcut}' is already assigned.", "ru": "Обнаружен конфликт клавиш: «{shortcut}» уже используется."},
    "settings.shortcuts.reset_defaults": {"en": "Reset Default Shortcuts", "ru": "Сбросить по умолчанию"},

    # Settings - Storage
    "settings.storage.db_path": {"en": "SQLite Database Location", "ru": "Расположение базы данных SQLite"},
    "settings.storage.images_path": {"en": "Image Storage Directory", "ru": "Папка хранения изображений"},
    "settings.storage.db_size": {"en": "Database Size", "ru": "Размер базы данных"},
    "settings.storage.images_size": {"en": "Images & Thumbnails Size", "ru": "Размер изображений и миниатюр"},
    "settings.storage.backup_btn": {"en": "Backup Database Now", "ru": "Создать резервную копию БД"},
    "settings.storage.export_btn": {"en": "Export Data to JSON...", "ru": "Экспортировать данные в JSON..."},
    "settings.storage.import_btn": {"en": "Import Data from JSON...", "ru": "Импортировать данные из JSON..."},
    "settings.storage.run_cleanup_btn": {"en": "Run Retention Cleanup Now", "ru": "Выполнить автоочистку сейчас"},
    "settings.storage.clear_all_btn": {"en": "Clear Unpinned Clipboard History", "ru": "Очистить незакреплённую историю"},

    # Settings - About
    "settings.about.description": {"en": "SNIPLY is a privacy-first, intelligent Windows clipboard manager that understands colors, links, JSON payloads, code fragments, and images — working 100% offline.", "ru": "SNIPLY — умный локальный менеджер буфера обмена для Windows, который распознаёт цвета, ссылки, JSON, фрагменты кода и изображения, работая полностью офлайн."},
    "settings.about.license": {"en": "License: MIT Open Source", "ru": "Лицензия: MIT Open Source"},
    "settings.about.github": {"en": "GitHub Repository", "ru": "Репозиторий GitHub"},
    "settings.about.credits": {"en": "Built with Python, PySide6, SQLite, Pillow, and Pygments.", "ru": "Разработано с использованием Python, PySide6, SQLite, Pillow и Pygments."},

    # System Tray Menu
    "tray.open_sniply": {"en": "Open SNIPLY", "ru": "Открыть SNIPLY"},
    "tray.quick_paste": {"en": "Quick Paste (Ctrl+Shift+V)", "ru": "Быстрая вставка (Ctrl+Shift+V)"},
    "tray.pause_monitoring": {"en": "Pause Monitoring", "ru": "Приостановить мониторинг"},
    "tray.resume_monitoring": {"en": "Resume Monitoring", "ru": "Возобновить мониторинг"},
    "tray.settings": {"en": "Settings", "ru": "Настройки"},
    "tray.exit": {"en": "Exit SNIPLY", "ru": "Выход"},

    # Onboarding Flow (6 Screens)
    "onboarding.window_title": {"en": "Welcome to SNIPLY", "ru": "Добро пожаловать в SNIPLY"},
    "onboarding.skip": {"en": "Skip Intro", "ru": "Пропустить"},
    "onboarding.back": {"en": "Back", "ru": "Назад"},
    "onboarding.next": {"en": "Continue", "ru": "Далее"},
    "onboarding.finish": {"en": "Start Using SNIPLY", "ru": "Начать работу со SNIPLY"},
    "onboarding.detected_ru": {"en": "Russian system locale detected. You can switch language anytime.", "ru": "Обнаружен русский язык системы. Вы можете переключить язык в любой момент."},

    "onboarding.step1.title": {"en": "Welcome to SNIPLY", "ru": "Добро пожаловать в SNIPLY"},
    "onboarding.step1.body": {"en": "Your clipboard, reimagined. SNIPLY remembers what you copy and automatically recognizes HEX/RGB colors, JSON payloads, URLs, code snippets, and high-resolution images.", "ru": "Ваш буфер обмена, переосмысленный заново. SNIPLY запоминает скопированные данные и автоматически распознаёт цвета HEX/RGB, структуры JSON, ссылки, фрагменты кода и изображения."},

    "onboarding.step2.title": {"en": "100% Local & Private History", "ru": "100% локальная и приватная история"},
    "onboarding.step2.body": {"en": "Everything you copy is stored strictly on your device inside a local SQLite database. There are no accounts, no cloud servers, no telemetry, and zero external network requests.", "ru": "Всё, что вы копируете, хранится исключительно на вашем компьютере в локальной базе SQLite. Никаких аккаунтов, облачных серверов, телеметрии и скрытых сетевых запросов."},

    "onboarding.step3.title": {"en": "Instant Quick Paste Anywhere", "ru": "Мгновенная быстрая вставка"},
    "onboarding.step3.body": {"en": "Press Ctrl + Shift + V from any application to summon the compact Quick Paste bar. Search thousands of clips in milliseconds and press Enter to restore.", "ru": "Нажмите Ctrl + Shift + V в любом приложении, чтобы открыть компактное окно Быстрой вставки. Находите нужные записи за миллисекунды и нажимайте Enter для вставки."},

    "onboarding.step4.title": {"en": "Smart Privacy & App Exclusions", "ru": "Защита данных и исключения программ"},
    "onboarding.step4.body": {"en": "Password managers (1Password, KeePassXC, Bitwarden) are excluded by default, and conservative secret filtering skips obvious API keys and private keys.", "ru": "Менеджеры паролей (1Password, KeePassXC, Bitwarden) исключены по умолчанию, а умный фильтр безопасности пропускает очевидные API-ключи и приватные токены."},

    "onboarding.step5.title": {"en": "Consent & Monitoring Preferences", "ru": "Согласие и параметры мониторинга"},
    "onboarding.step5.body": {"en": "SNIPLY never collects clipboard history without your explicit permission. Choose how you want monitoring and retention configured:", "ru": "SNIPLY не начинает сохранять историю буфера обмена без вашего явного согласия. Выберите удобные параметры работы:"},
    "onboarding.step5.consent_checkbox": {"en": "I understand and enable local clipboard monitoring", "ru": "Я ознакомлен и включаю локальный мониторинг буфера обмена"},

    "onboarding.step6.title": {"en": "You're All Set", "ru": "Всё готово к работе"},
    "onboarding.step6.body": {"en": "SNIPLY is ready. You can pause monitoring anytime from the system tray or explore the optional Demo Gallery to see smart recognition in action.", "ru": "SNIPLY готов к использованию. Вы можете в любой момент поставить мониторинг на паузу через системный трей или открыть Демо-режим для знакомства с функциями."},

    # Confirmations & Dialogs
    "dialog.confirm_delete_pinned.title": {"en": "Delete Pinned Item?", "ru": "Удалить закреплённую запись?"},
    "dialog.confirm_delete_pinned.body": {"en": "This item is pinned to protect it from accidental removal. Are you sure you want to permanently delete it?", "ru": "Эта запись закреплена для защиты от случайного удаления. Вы действительно хотите удалить её навсегда?"},
    "dialog.confirm_clear_history.title": {"en": "Clear Clipboard History?", "ru": "Очистить историю буфера обмена?"},
    "dialog.confirm_clear_history.body": {"en": "This will remove all unpinned and non-favorite clipboard entries. Pinned and favorite items will be preserved.", "ru": "Все незакреплённые и не добавленные в избранное записи будут удалены. Закреплённые и избранные записи сохранятся."},
}


def generate_translations() -> None:
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    en_dict = {}
    ru_dict = {}
    for key, langs in sorted(TRANSLATIONS.items()):
        en_dict[key] = langs["en"]
        ru_dict[key] = langs["ru"]

    (TRANSLATIONS_DIR / "en.json").write_text(
        json.dumps(en_dict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (TRANSLATIONS_DIR / "ru.json").write_text(
        json.dumps(ru_dict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated {len(en_dict)} translation keys for en.json and ru.json")


if __name__ == "__main__":
    generate_translations()
