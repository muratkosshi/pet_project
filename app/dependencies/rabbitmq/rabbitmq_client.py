import pika
import json
import logging

RABBITMQ_HOST = "rabbitmq"  # Имя контейнера в Docker Compose
RABBITMQ_QUEUE = "presentation_updates"

# 📌 Подключаемся к RabbitMQ
def get_rabbitmq_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    return channel, connection

# 📢 Функция отправки сообщения в очередь RabbitMQ
def publish_update(uuid: str, task_id: str, status: str):
    channel, connection = get_rabbitmq_channel()
    message = json.dumps({"uuid": uuid, "task_id": task_id, "status": status})
    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),  # Сообщение сохраняется при сбое
    )
    logging.info(f"📢 [RabbitMQ] Отправлен статус: {message}")
    connection.close()
