# Сервис обработки платежей
Асинхронный микросервис обработки платежей на базе **FastAPI**, **PostgreSQL** и **RabbitMQ**
Система состоит из четырёх компонентов:

| Component | Responsibility |
|-----------|----------------|
| `payment_consumer`    | Outbox Relay, RabbitMQ producer и consumer; эмулирует обработку платежей и отправляет webhook |
| `payment_service`       | HTTP API для создания и получения платежей |
| `PostgreSQL`  | основное хранилище платежей и Outbox-сообщений |
| `RabbitMQ` | брокер сообщений с retry-механизмом и Dead Letter Queue |

## Ключевые особенности
1. Асинхронная работа всех компонентов системы, идемпотентность POST запросов
2. Transactional Outbox — предотвращает потерю события между сохранением платежа и публикацией сообщения.
3. Retry mechanism — повторная обработка сообщений после ошибок.
4. Dead Letter Queue — изоляция сообщений, которые не удалось обработать после допустимого количества попыток или после истечения TTL.

## Getting started
Для запуска необходимо только наличие Docker и Docker Compose
1. В основной директории создать `.env` файл:
```
DATABASE_URL=postgresql+asyncpg://postgres:admin@postgresql:5432/postgres
RABBITMQ_URL=amqp://guest:guest@rabbit:5672
API_KEY=MY_SECRET_API_KEY
```
2. Запустить билд и сам проект:

`docker-compose up -d --build`

3. Swagger для FastAPI доступен по адресу `http://localhost:8000/docs`, UI RabbitMQ - `http://localhost:15672` (логин/пароль - guest/guest).

## Примеры запросов
- Создание нового платежа
```commandline
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/payments/' \
  -H 'accept: */*' \
  -H 'X-Idempotency-Key: 7e1c39b6-ae2b-41a9-9f71-6bff5dbe49e1' \
  -H 'X-API-Key: MY_SECRET_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
  "amount": 10,
  "currency": "RUB",
  "description": "Subscription payment",
  "payment_metadata": {"region": "RU", "service": "Bank"},
  "webhook_url": "http://127.0.0.1:8000/api/v1/notify"
}'
```
Создаёт запись в таблицах `payments` со статусом pending и `outbox` с sent_at = null. Далее, consumer публикует сообщение из `outbox` в Rabbit, обновляя sent_at. После попадания сообщения в очередь, оно извлекается асинхронно обрабатывается этим же consumer, эмулируя оплату и обновляя статус в `payments` в соответствии с исходом "платежа" и отправляет запрос на webhook_url в `payment_service`.

- Для тестирования GET запроса можно взять ID, который возвращается после POST запроса - `payment_id`, или же достать ID любого платежа (клиент PostgreSQL или Docker Desktop не нужны):

Чтобы посмтреть все текущие платеж, выполняем в консоли команду:

`docker compose exec postgresql psql -U postgres -d postgres -c "SELECT payment_id FROM payments;"`

берём любой ID используем в запросе ниже вместо тестового `2369ef1f-3dea-4d37-b107-5654ac909300`:
```commandline
curl -X 'GET' \
  'http://127.0.0.1:8000/api/v1/payments/2369ef1f-3dea-4d37-b107-5654ac909300' \
  -H 'accept: */*' \
  -H 'X-API-Key: MY_SECRET_API_KEY'
```

## Стек технологий
- **FastAPI** + Pydantic v2
- **SQLAlchemy 2.0** (асинхронный режим)
- **PostgreSQL**
- **RabbitMQ** (FastStream)
- **Alembic** (миграции)
- **Docker** + docker-compose