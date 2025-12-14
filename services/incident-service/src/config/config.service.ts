import { Injectable } from '@nestjs/common';

@Injectable()
export class ConfigService {
  get port(): number {
    return parseInt(process.env.PORT || '3003', 10);
  }

  get databaseUrl(): string {
    return process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/patient_monitoring';
  }

  get kafkaBrokers(): string[] {
    return (process.env.KAFKA_BROKERS || 'localhost:29092').split(',');
  }

  get kafkaClientId(): string {
    return process.env.KAFKA_CLIENT_ID || 'incident-service';
  }

  get kafkaConsumerGroup(): string {
    return process.env.KAFKA_CONSUMER_GROUP || 'incident-service-group';
  }

  get kafkaTopicAlerts(): string {
    return process.env.KAFKA_TOPIC_ALERTS || 'alerts.raised';
  }

  get kafkaConnectionRetryAttempts(): number {
    return parseInt(process.env.KAFKA_CONNECTION_RETRY_ATTEMPTS || '10', 10);
  }

  get kafkaConnectionRetryDelay(): number {
    return parseInt(process.env.KAFKA_CONNECTION_RETRY_DELAY || '5000', 10);
  }

  get logLevel(): string {
    return process.env.LOG_LEVEL || 'info';
  }
}

