# 📘 Pet project with Django + DRF + PostgreSQL + Redis

## Содержание
- [Стек](#стек)
- [Быстрый старт (dev)](#быстрый-старт-dev)
- [Переменные окружения](#переменные-окружения)
- [Запуск Redis (Docker)](#запуск-redis-docker)
- [Миграции и суперпользователь](#миграции-и-суперпользователь)
- [API](#api)
- [Кэширование](#кэширование)
- [Троттлинг (rate limit)](#троттлинг-rate-limit)
- [Тесты кэша глазами](#тесты-кэша-глазами)
- [Подсмотр в Redis](#подсмотр-в-redis)
- [Инвалидация кэша](#инвалидация-кэша)
- [Траблшутинг](#траблшутинг)
- [Дорожная карта](#дорожная-карта)

---

## Стек
- **Python** 3.11+
- **Django** (DRF)
- **Redis** (кэш + троттлинг)
- **PostgreSQL**
- **Docker** (для Redis)
- (Optional) **Celery** — в планах

---

## Быстрый старт (dev)

```powershell
# 1) Клонировать
git clone <repo-url>
cd <repo-folder>

# 2) Виртуальное окружение
python -m venv venv
venv\Scripts\activate

# 3) Зависимости
pip install -r requirements.txt

# 4) .env
copy .env.example .env   # создаём .env из примера и правим под себя

# 5) Миграции
python manage.py migrate

# 6) Суперпользователь (опционально)
python manage.py createsuperuser

# 7) Запуск
python manage.py runserver
```

**URL по умолчанию:**  
- API: `http://127.0.0.1:8000/api/v1/...`  
- Админка: `http://127.0.0.1:8000/admin/`

---

## Переменные окружения

`.env` (минимум):
```
# Django
DEBUG=1
DJANGO_SECRET_KEY=change-me

# БД (если нужна Postgres — добавь свои переменные)
# DATABASE_URL=postgres://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/1
CACHE_TTL=300
```

> Проект подхватывает `.env` через `python-dotenv`.

---

## Запуск Redis (Docker)

```yaml
# docker-compose.yml (минимальный сервис Redis)
services:
  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes", "--save", "60", "1000"]
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
volumes:
  redis-data:
```

```powershell
docker compose up -d redis
```

> Если порт 6379 занят — поменяй на `6380:6379` и укажи `REDIS_URL=redis://localhost:6380/1`.

---

## Миграции и суперпользователь

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## API

Основные эндпоинты (минимум, используемые в README):

- **Список/создание курсов**  
  `GET /api/v1/courses/` — список (кэшируется `cache_page`)  
  `POST /api/v1/courses/` — создать курс (не кэшируется)

- **Деталь курса**  
  `GET /api/v1/courses/<id>/` — детальная карточка (ручной кэш на Redis)

- **Топ курсов**  
  `GET /api/v1/courses/top/?limit=5&order=title` — топ по выбранному полю  
    по умолчанию `order=-id` (замени на свои поля, когда появятся рейтинги)

Есть и другие пути (например, `/api/v1/me/`, `/api/v1/user/<id>/`, служебные ключи Redis), см. `backend/urls.py`.

---

## Кэширование

Включено через `django-redis`:

```python
CACHES = {
  "default": {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
    "TIMEOUT": int(os.environ.get("CACHE_TTL", 300)),
    "OPTIONS": {
      "CLIENT_CLASS": "django_redis.client.DefaultClient",
      "CONNECTION_POOL_KWARGS": {"max_connections": 100},
      "IGNORE_EXCEPTIONS": True
    }
  }
}
```

Паттерны:
- **Списки** — `cache_page(TTL)`, ключи хэшируются (в Redis выглядят «нечитаемо», это нормально).
- **Деталь/Топ** — **ручной кэш** с читаемыми ключами:
  - `v1:courses:detail:{id}` (TTL 300 c)
  - `v1:courses:top:{limit}:{order}` (TTL 60 c)  
  Django добавляет версию `:1:` → реальный ключ будет `:1:v1:courses:detail:1`.

Для отладки добавлен заголовок `X-Cache: MISS/HIT`.

---

## Троттлинг (rate limit)

Хранение счётчиков — в Redis через Django cache.

```python
REST_FRAMEWORK = {
  "DEFAULT_THROTTLE_CLASSES": [
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
    "rest_framework.throttling.ScopedRateThrottle",
  ],
  "DEFAULT_THROTTLE_RATES": {
    "anon": "60/min",
    "user": "120/min",
    "courses-top": "10/min",
  },
}
```

Во вью добавлен скоуп:
```python
class TopCoursesView(APIView):
    throttle_scope = "courses-top"
    ...
```
---

## Тесты кэша глазами

### Windows (PowerShell)
```powershell
# деталь (первый MISS, дальше HIT)
curl.exe -s -D - -o NUL "http://127.0.0.1:8000/api/v1/courses/1/" | findstr X-Cache
curl.exe -s -D - -o NUL "http://127.0.0.1:8000/api/v1/courses/1/" | findstr X-Cache

# топ (ключ зависит от limit и order)
curl.exe -s -D - -o NUL "http://127.0.0.1:8000/api/v1/courses/top/?limit=5&order=title" | findstr X-Cache
curl.exe -s -D - -o NUL "http://127.0.0.1:8000/api/v1/courses/top/?limit=5&order=title" | findstr X-Cache
```

### Linux/macOS
```bash
curl -s -D - -o /dev/null "http://127.0.0.1:8000/api/v1/courses/1/" | grep X-Cache
curl -s -D - -o /dev/null "http://127.0.0.1:8000/api/v1/courses/1/" | grep X-Cache
```

---

## Подсмотр в Redis

> На Windows удобнее заходить через контейнер.

```powershell
# проверка соединения
docker exec -it backend-redis-1 redis-cli -n 1 ping

# посмотреть ключи по курсам (учти префикс :1:)
docker exec -it backend-redis-1 sh -lc "redis-cli -n 1 scan 0 match '*v1:courses*' count 100"

# TTL конкретного ключа
docker exec -it backend-redis-1 sh -lc "redis-cli -n 1 ttl ':1:v1:courses:detail:1'"
docker exec -it backend-redis-1 sh -lc "redis-cli -n 1 ttl ':1:v1:courses:top:5:title'"

# прямой тест кэша
python manage.py shell -c "from django.core.cache import cache; cache.set('test:foo', 123, 300); print(cache.get('test:foo'))"
docker exec -it backend-redis-1 sh -lc "redis-cli -n 1 get ':1:test:foo'"
```

> Для аккуратных ключей — `CACHES["default"]` `KEY_PREFIX="app"`, тогда вид будет `app:1:...`.

---

## Инвалидация кэша

Инвалидация «деталей» и «топов» на сигналах:

```python
# courses/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Course

def purge_course_detail(course_id: int):
    cache.delete(f"v1:courses:detail:{course_id}")

def purge_top_lists():
    cache.delete_pattern("v1:courses:top:*")  # работает через django-redis

@receiver(post_save, sender=Course)
def on_course_save(sender, instance: Course, **kwargs):
    purge_course_detail(instance.pk)
    purge_top_lists()

@receiver(post_delete, sender=Course)
def on_course_delete(sender, instance: Course, **kwargs):
    purge_course_detail(instance.pk)
    purge_top_lists()
```

Подключение:
```python
# courses/apps.py
class CoursesConfig(AppConfig):
    name = "courses"
    def ready(self):
        from . import signals  # noqa
```

И в `INSTALLED_APPS`:
```python
"courses.apps.CoursesConfig",
```

---

## Траблшутинг

- **`redis-cli: command not found` (Windows)** — заходи через контейнер:
  ```powershell
  docker exec -it backend-redis-1 redis-cli -n 1 ping
  ```
- **Ключей «не видно», но кэш работает** — `cache_page` создаёт хэш-ключи. Для явной проверки используй ручные ключи деталки/топа или `cache.set/get`.
- **Ключей всё равно не видно** — проверь версию `:1:` в начале ключа:
  ```powershell
  python manage.py shell -c "from django.core.cache import caches; print(caches['default'].make_key('v1:courses:detail:1'))"
  ```
- **Порт 6379 занят** — поменяй публикацию порта в compose на `6380:6379` и `REDIS_URL=redis://localhost:6380/1`.
- **500 на `/courses/top/`** — проверь сортировку: используй существующее поле `order=title` или `order=-id`.

---

## Дорожная карта

- [ ] **Celery + Redis** (брокер/result), `Flower` для мониторинга, вынесение писем/сертификатов/агрегатов в фон.  
- [ ] Поля `created_at`, `views`, `students_count`, `rating` → «настоящий топ» через `annotate()` + индексы.  
- [ ] KEY_PREFIX в кэше (например, `app`) для наглядности ключей.  
- [ ] Автотесты производительности (pytest-benchmark) до/после кэша.
