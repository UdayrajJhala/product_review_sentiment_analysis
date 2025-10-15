# How to run Kafka
Produce: python3 google_forms_producer.py
Consume docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic reviews_raw --from-beginning