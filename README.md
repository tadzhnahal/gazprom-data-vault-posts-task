# Data Vault Posts Loader

## О проекте

Этот репозиторий содержит решение тестового задания для стажировки «ДИП:КОД» в ИТ-кластере «Газпром нефти» на направление «Инженер данных».

Проект забирает данные из REST API `https://jsonplaceholder.typicode.com/posts/`, загружает их в PostgreSQL и перекладывает из слоя `STG` в слой `DDS`. Для слоя `DDS` используется Data Vault 2.0.

В проекте есть два потока:

1. Скрипт `elt_1_load_stg.py` загружает данные из REST API в таблицу `stg.posts`.
2. Скрипт `elt_2_load_dds.py` перекладывает данные из таблицы `stg.posts` в таблицы слоя `dds`.

DataMart в проекте не реализован. На схеме задания он показан как следующий слой, но в тексте задачи нужно спроектировать только `STG` и `DDS`, а также реализовать `ELT 1` и `ELT 2`.

## Стек

Python, PostgreSQL, Docker Compose.

## Структура репозитория

Папка `sql` хранит DDL-скрипты для схем и таблиц. Папка `src` хранит Python-код для подключения к базе и два ELT-скрипта. Файл `docker-compose.yml` поднимает локальную PostgreSQL. Файл `.env.example` показывает переменные, которые нужны для локального запуска.

```text
.
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── sql
│   ├── 001_create_schemas.sql
│   ├── 002_create_stg_tables.sql
│   └── 003_create_dds_tables.sql
└── src
    ├── config.py
    ├── db.py
    ├── elt_1_load_stg.py
    └── elt_2_load_dds.py
```

## Как работают слои

### STG

Слой `STG` хранит данные из источника почти в исходном виде. В проекте для этого есть таблица `stg.posts`. Скрипт `elt_1_load_stg.py` загружает в неё данные из REST API.

В таблицу `stg.posts` попадают поля из источника:

1. `id` — идентификатор поста из API. В `DDS` это поле станет бизнес-ключом поста.
2. `user_id` — идентификатор пользователя из поля `userId`. В `DDS` это поле станет бизнес-ключом пользователя.
3. `title` — заголовок поста.
4. `body` — текст поста.

Также таблица `stg.posts` хранит технические поля:

1. `source_system` — имя источника данных. В этом проекте используется значение `jsonplaceholder_posts`.
2. `loaded_at` — время загрузки строки в `STG`.

В этой версии `STG` работает как свежий снимок источника. Перед загрузкой скрипт `elt_1_load_stg.py` очищает таблицу `stg.posts` и затем записывает новый набор строк из API.

### DDS

Слой `DDS` построен по Data Vault 2.0. В нём бизнес-ключи, связи и атрибуты лежат отдельно.

В проекте есть четыре DDS-таблицы:

1. `dds.h_user` — hub пользователей, который хранит бизнес-ключ пользователя из поля `userId`.
2. `dds.h_post` — hub постов, который хранит бизнес-ключ поста из поля `id`.
3. `dds.l_user_post` — link между пользователем и постом, который хранит связь пользователя с его постом.
4. `dds.s_post_details` — satellite с деталями поста, который хранит поля `title`, `body` и `hash_diff`.

Для hash key используется SHA-256. Python считает hash key в hex-виде, поэтому hash-поля в PostgreSQL имеют тип `varchar(64)`.

## Основные решения

### Поля `id` и `userId` разделены по разным hub-таблицам

В задании поля `id` и `userId` указаны как бизнес-ключи. Эти поля описывают разные сущности, поэтому в слое `DDS` они попадают в разные hub-таблицы.

Поле `id` описывает пост. Поэтому скрипт `elt_2_load_dds.py` кладёт значение этого поля в таблицу `dds.h_post` как поле `post_id` и считает для него hash key `post_hash_key`.

Поле `userId` описывает пользователя. Поэтому скрипт `elt_2_load_dds.py` кладёт значение этого поля в таблицу `dds.h_user` как поле `user_id` и считает для него hash key `user_hash_key`.

Связь между пользователем и постом не хранится внутри hub-таблиц. Для этой связи есть link-таблица `dds.l_user_post`. Так модель явно показывает, какой пользователь связан с каким постом.

### Поля `title` и `body` хранятся отдельно от hub-таблицы `dds.h_post`

Hub-таблица `dds.h_post` хранит только бизнес-ключ поста. Это помогает не смешивать идентификатор сущности с описательными полями.

Поля `title` и `body` описывают пост, но не задают его идентичность. Поэтому значения этих полей лежат в satellite-таблице `dds.s_post_details`. Если текст поста изменится, поле `post_id` останется тем же, а новые детали можно будет сохранить отдельной строкой.

Поле `hash_diff` считается по полям `title` и `body`. Скрипт `elt_2_load_dds.py` не добавляет новую строку в таблицу `dds.s_post_details`, если для поста уже есть такая же версия деталей.

### Таблица `stg.posts` очищается перед загрузкой

В этой версии проекта слой `STG` хранит свежий снимок источника. Поэтому скрипт `elt_1_load_stg.py` сначала очищает таблицу `stg.posts` командой `truncate table`, а потом заново загружает в неё данные из API `jsonplaceholder`.

Так проще проверить тестовое задание. После запуска этапа `ELT 1` в таблице `stg.posts` всегда лежит актуальный набор строк из источника `jsonplaceholder`.

### Локальная PostgreSQL через Docker Compose

Docker Compose нужен только для локальной PostgreSQL. Python-скрипты запускаются с хоста. Так проект остаётся простым. В нём нет Dockerfile для Python, Airflow, cron или других инструментов, которые не требуются по заданию.

## Как запустить проект

### 1. Подготовьте окружение

Установите Python 3, Docker и Docker Compose.

Проверьте Python. Выполните команду:

```bash
python3 --version
```

Проверьте Docker. Выполните команду:

```bash
docker --version
```

Проверьте Docker Compose. Выполните команду:

```bash
docker compose version
```

### 2. Склонируйте репозиторий

Склонируйте проект и перейдите в его корень. Выполните команды:

```bash
git clone https://github.com/tadzhnahal/gazprom-data-vault-posts-task
cd gazprom-data-vault-posts-task
```

### 3. Создайте файл `.env`

Скопируйте пример переменных в локальный файл `.env`. Выполните команду:

```bash
cp .env.example .env
```

Файл `.env` нужен Docker Compose и Python-скриптам. Git не хранит этот файл, потому что он указан в `.gitignore`.

В файле `.env.example` уже лежат значения для локального запуска:

```text
POSTGRES_DB=gazprom_posts_warehouse
POSTGRES_USER=posts_loader
POSTGRES_PASSWORD=posts_loader_pass
POSTGRES_PORT=5432
DATABASE_URL=postgresql://posts_loader:posts_loader_pass@localhost:5432/gazprom_posts_warehouse
```

### 4. Поднимите PostgreSQL

Запустите PostgreSQL через Docker Compose. Выполните команду:

```bash
docker compose up -d
```

Проверьте контейнер. Выполните команду:

```bash
docker compose ps
```

В списке должен быть контейнер `gazprom_dv_posts_postgres`. Его статус должен быть `running` или `healthy`.

### 5. Создайте Python-окружение

Создайте виртуальное окружение. Выполните команду:

```bash
python3 -m venv .venv
```

Активируйте его. Выполните команду:

```bash
source .venv/bin/activate
```

Установите зависимости. Выполните команду:

```bash
python -m pip install -r requirements.txt
```

### 6. Проверьте вход в PostgreSQL

Откройте консоль PostgreSQL внутри контейнера. Выполните команду:

```bash
docker compose exec postgres psql -U posts_loader -d gazprom_posts_warehouse
```

Проверьте базу и пользователя. Выполните запрос:

```sql
select current_database(), current_user;
```

Ожидаемый результат должен показать базу `gazprom_posts_warehouse` и пользователя `posts_loader`.

Выйдите из PostgreSQL. Выполните команду:

```sql
\q
```

### 7. Создайте схемы и таблицы

Выполните SQL-файл со схемами. Выполните команду:

```bash
docker compose exec -T postgres psql -U posts_loader -d gazprom_posts_warehouse < sql/001_create_schemas.sql
```

Выполните SQL-файл для слоя `STG`. Выполните команду:

```bash
docker compose exec -T postgres psql -U posts_loader -d gazprom_posts_warehouse < sql/002_create_stg_tables.sql
```

Выполните SQL-файл для слоя `DDS`. Выполните команду:

```bash
docker compose exec -T postgres psql -U posts_loader -d gazprom_posts_warehouse < sql/003_create_dds_tables.sql
```

Эти файлы можно запускать повторно. В них используется `if not exists`, поэтому PostgreSQL не выдаст ошибку, если схема или таблица уже есть.

### 8. Запустите ELT 1

Запустите загрузку из REST API в слой `STG`. Выполните команду:

```bash
python src/elt_1_load_stg.py
```

Ожидаемый вывод:

```text
loaded 100 posts to stg.posts
```

Скрипт `elt_1_load_stg.py` забирает данные из `https://jsonplaceholder.typicode.com/posts/`, очищает таблицу `stg.posts` и записывает свежий набор строк.

### 9. Запустите ELT 2

Запустите загрузку из слоя `STG` в слой `DDS`. Выполните команду:

```bash
python src/elt_2_load_dds.py
```

Ожидаемый вывод:

```text
processed 100 stg rows into dds
```

Скрипт `elt_2_load_dds.py` читает таблицу `stg.posts`, считает hash key, загружает hub-таблицы, link-таблицу и таблицу с деталями постов.

## Как проверить результат

### 1. Проверьте строки в STG

Откройте PostgreSQL. Выполните команду:

```bash
docker compose exec postgres psql -U posts_loader -d gazprom_posts_warehouse
```

Проверьте число строк в таблице `stg.posts`. Выполните запрос:

```sql
select count(*)
from stg.posts;
```

Ожидаемый результат:

```text
100
```

Посмотрите первые строки. Выполните запрос:

```sql
select id, user_id, left(title, 40) as title_start
from stg.posts
order by id
limit 5;
```

В ответе должны появиться посты с полем `id` от `1` до `5`.

### 2. Проверьте строки в DDS

Проверьте hub пользователей. Выполните запрос:

```sql
select count(*)
from dds.h_user;
```

Ожидаемый результат:

```text
10
```

Проверьте hub постов. Выполните запрос:

```sql
select count(*)
from dds.h_post;
```

Ожидаемый результат:

```text
100
```

Проверьте link пользователя и поста. Выполните запрос:

```sql
select count(*)
from dds.l_user_post;
```

Ожидаемый результат:

```text
100
```

Проверьте таблицу с деталями постов. Выполните запрос:

```sql
select count(*)
from dds.s_post_details;
```

Ожидаемый результат:

```text
100
```

### 3. Проверьте связь пользователя и поста

Выполните запрос:

```sql
select
    hu.user_id,
    hp.post_id
from dds.l_user_post lup
join dds.h_user hu on hu.user_hash_key = lup.user_hash_key
join dds.h_post hp on hp.post_hash_key = lup.post_hash_key
order by hp.post_id
limit 5;
```

В ответе должны появиться посты с полем `post_id` от `1` до `5` и полем `user_id` со значением `1`.

### 4. Проверьте детали постов

Выполните запрос:

```sql
select
    hp.post_id,
    left(spd.title, 40) as title_start,
    left(spd.hash_diff, 12) as hash_diff_start
from dds.s_post_details spd
join dds.h_post hp on hp.post_hash_key = spd.post_hash_key
order by hp.post_id
limit 5;
```

В ответе должны появиться поле `post_id`, начало поля `title` и начало поля `hash_diff`.

### 5. Проверьте повторный запуск ELT 2

Выйдите из PostgreSQL. Выполните команду:

```sql
\q
```

Запустите `ELT 2` ещё раз. Выполните команду:

```bash
python src/elt_2_load_dds.py
```

Снова откройте PostgreSQL. Выполните команду:

```bash
docker compose exec postgres psql -U posts_loader -d gazprom_posts_warehouse
```

Проверьте, что число строк в таблице `dds.s_post_details` не выросло. Выполните запрос:

```sql
select count(*)
from dds.s_post_details;
```

Ожидаемый результат:

```text
100
```

Так можно проверить, что скрипт `elt_2_load_dds.py` не добавляет одинаковые детали поста повторно.

Выйдите из PostgreSQL. Выполните команду:

```sql
\q
```

## Как остановить проект

Остановите PostgreSQL. Выполните команду:

```bash
docker compose down
```

Docker хранит данные PostgreSQL в отдельном volume. Если нужно удалить контейнеры и эти локальные данные PostgreSQL, выполните команду:

```bash
docker compose down -v
```

Отключите виртуальное окружение Python. Выполните команду:

```bash
deactivate
```

## Ограничения

Скрипт `elt_2_load_dds.py` не добавляет новую строку в таблицу `dds.s_post_details`, если для поста уже есть такая же пара полей `title` и `body`. Для текущего источника этого достаточно, потому что источник `jsonplaceholder` отдаёт статичный набор тестовых данных.
