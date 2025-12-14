import { Injectable } from '@nestjs/common';

@Injectable()
export class ConfigService {
  get port(): number {
    return parseInt(process.env.PORT || '3004', 10);
  }

  get databaseUrl(): string {
    return process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/patient_monitoring';
  }

  get kafkaBrokers(): string[] {
    return (process.env.KAFKA_BROKERS || 'localhost:29092').split(',');
  }

  get kafkaClientId(): string {
    return process.env.KAFKA_CLIENT_ID || 'notification-service';
  }

  get kafkaConsumerGroup(): string {
    return process.env.KAFKA_CONSUMER_GROUP || 'notification-service-group';
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

  get redisHost(): string {
    return process.env.REDIS_HOST || 'localhost';
  }

  get redisPort(): number {
    return parseInt(process.env.REDIS_PORT || '6379', 10);
  }

  get redisPassword(): string | undefined {
    return process.env.REDIS_PASSWORD;
  }

  get redisEnabled(): boolean {
    return process.env.REDIS_ENABLED !== 'false';
  }

  get rateLimitWindowMs(): number {
    return parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000', 10); // Default 1 minute
  }

  get rateLimitMaxNotifications(): number {
    return parseInt(process.env.RATE_LIMIT_MAX_NOTIFICATIONS || '10', 10); // Default 10 per window
  }

  get logLevel(): string {
    return process.env.LOG_LEVEL || 'info';
  }
}

