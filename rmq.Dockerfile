# Use official RabbitMQ image
FROM rabbitmq:3-management

# Expose default RabbitMQ ports
EXPOSE 5672 15672

# Optional: Add your custom configuration or setup
# COPY custom_config.conf /etc/rabbitmq/rabbitmq.conf

# Run RabbitMQ server by default
CMD ["rabbitmq-server"]
