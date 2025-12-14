import { Injectable } from '@nestjs/common';

@Injectable()
export class ConfigService {
  get port(): number {
    return parseInt(process.env.PORT || '3002', 10);
  }

  get kafkaBrokers(): string[] {
    return (process.env.KAFKA_BROKERS || 'localhost:29092').split(',');
  }

  get kafkaClientId(): string {
    return process.env.KAFKA_CLIENT_ID || 'telemetry-enrichment';
  }

  get kafkaConsumerGroup(): string {
    return process.env.KAFKA_CONSUMER_GROUP || 'telemetry-enrichment-group';
  }

  get kafkaTopicNormalized(): string {
    return process.env.KAFKA_TOPIC_NORMALIZED || 'telemetry.normalized';
  }

  get kafkaTopicEnriched(): string {
    return process.env.KAFKA_TOPIC_ENRICHED || 'telemetry.enriched';
  }

  get registryGrpcUrl(): string {
    return process.env.REGISTRY_GRPC_URL || 'localhost:50051';
  }

  get registryEnabled(): boolean {
    return process.env.REGISTRY_ENABLED !== 'false';
  }

  get registryTimeoutMs(): number {
    return parseInt(process.env.REGISTRY_TIMEOUT_MS || '5000', 10);
  }

  get registryMaxRetries(): number {
    return parseInt(process.env.REGISTRY_MAX_RETRIES || '3', 10);
  }

  get registryRetryDelayMs(): number {
    return parseInt(process.env.REGISTRY_RETRY_DELAY_MS || '1000', 10);
  }

  get logLevel(): string {
    return process.env.LOG_LEVEL || 'info';
  }

  get gracefulShutdownTimeoutMs(): number {
    return parseInt(process.env.GRACEFUL_SHUTDOWN_TIMEOUT_MS || '30000', 10);
  }
}

