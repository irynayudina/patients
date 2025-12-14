import { Injectable } from '@nestjs/common';

@Injectable()
export class ConfigService {
  get port(): number {
    return parseInt(process.env.PORT || '3000', 10);
  }

  get grpcPort(): number {
    return parseInt(process.env.GRPC_PORT || '50052', 10);
  }

  get kafkaBrokers(): string[] {
    return (process.env.KAFKA_BROKERS || 'localhost:29092').split(',');
  }

  get kafkaClientId(): string {
    return process.env.KAFKA_CLIENT_ID || 'telemetry-gateway';
  }

  get kafkaTopicRaw(): string {
    return process.env.KAFKA_TOPIC_RAW || 'telemetry.raw';
  }

  get registryGrpcUrl(): string {
    return process.env.REGISTRY_GRPC_URL || 'localhost:50051';
  }

  get registryEnabled(): boolean {
    return process.env.REGISTRY_ENABLED === 'true' || process.env.REGISTRY_ENABLED === '1';
  }

  get logLevel(): string {
    return process.env.LOG_LEVEL || 'info';
  }
}

