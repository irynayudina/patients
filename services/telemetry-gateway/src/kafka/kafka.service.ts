import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import { Kafka, Producer, KafkaConfig, ProducerConfig } from 'kafkajs';
import { ConfigService } from '../config/config.service';

@Injectable()
export class KafkaService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(KafkaService.name);
  private kafka: Kafka;
  private producer: Producer;
  private isConnected = false;

  constructor(private readonly configService: ConfigService) {
    const kafkaConfig: KafkaConfig = {
      clientId: this.configService.kafkaClientId,
      brokers: this.configService.kafkaBrokers,
      retry: {
        retries: 8,
        initialRetryTime: 100,
        multiplier: 2,
        maxRetryTime: 30000,
      },
    };

    this.kafka = new Kafka(kafkaConfig);

    const producerConfig: ProducerConfig = {
      maxInFlightRequests: 1,
      idempotent: true,
      transactionTimeout: 30000,
    };

    this.producer = this.kafka.producer(producerConfig);
  }

  async onModuleInit() {
    await this.connect();
  }

  async onModuleDestroy() {
    await this.disconnect();
  }

  private async connect() {
    try {
      this.logger.log('Connecting to Kafka...');
      await this.producer.connect();
      this.isConnected = true;
      this.logger.log('Successfully connected to Kafka');
    } catch (error) {
      this.logger.error('Failed to connect to Kafka', error);
      throw error;
    }
  }

  private async disconnect() {
    if (this.isConnected) {
      try {
        this.logger.log('Disconnecting from Kafka...');
        await this.producer.disconnect();
        this.isConnected = false;
        this.logger.log('Successfully disconnected from Kafka');
      } catch (error) {
        this.logger.error('Error disconnecting from Kafka', error);
      }
    }
  }

  async produceRawTelemetry(event: any): Promise<void> {
    if (!this.isConnected) {
      throw new Error('Kafka producer is not connected');
    }

    const topic = this.configService.kafkaTopicRaw;
    const maxRetries = 3;
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        await this.producer.send({
          topic,
          messages: [
            {
              key: event.device_id,
              value: JSON.stringify(event),
              timestamp: Date.now().toString(),
            },
          ],
        });

        this.logger.debug(`Successfully produced event to ${topic}`, {
          eventId: event.event_id,
          deviceId: event.device_id,
        });
        return;
      } catch (error) {
        lastError = error as Error;
        this.logger.warn(`Failed to produce event (attempt ${attempt}/${maxRetries})`, {
          error: error instanceof Error ? error.message : String(error),
          eventId: event.event_id,
        });

        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }
    }

    this.logger.error(`Failed to produce event after ${maxRetries} attempts`, {
      error: lastError?.message,
      eventId: event.event_id,
    });
    throw lastError || new Error('Failed to produce event to Kafka');
  }
}

