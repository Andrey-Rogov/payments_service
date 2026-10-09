import asyncio

from logging import getLogger
from faststream import FastStream

from consumers import rabbit, service

logger = getLogger("output")
app = FastStream(rabbit)


@app.after_startup
async def start_relay():
    asyncio.create_task(relay_process())  # only create task, cause faststream already runs event loop


async def relay_process():
    """
    Relay process для реализации Outbox pattern - проверяет таблицу outbox и создаёт
    сообщения в очереди, помечая их как отправленные (sent_at = now())
    """
    while True:
        await service.publish_from_outbox()
        await asyncio.sleep(5)
