import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import { Kafka, Consumer, KafkaConfig, ConsumerConfig } from 'kafkajs';
import { ConfigService } from '../config/config.service';

@Injectable()
export class KafkaConsumerService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(KafkaConsumerService.name);
  private kafka: Kafka;
  private consumer: Consumer;
  private isConnected = false;
  private messageHandler?: (message: any) => Promise<void>;

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

    const consumerConfig: ConsumerConfig = {
      groupId: this.configService.kafkaConsumerGroup,
      sessionTimeout: 30000,
      heartbeatInterval: 3000,
      maxInFlightRequests: 1,
      retry: {
        retries: 8,
        initialRetryTime: 100,
        multiplier: 2,
        maxRetryTime: 30000,
      },
    };

    this.consumer = this.kafka.consumer(consumerConfig);
  }

  async onModuleInit() {
    await this.connect();
    // Subscribe will be called after message handler is set in AppModule
  }

  async startConsuming() {
    if (!this.messageHandler) {
      throw new Error('Message handler must be set before starting consumption');
    }
    await this.subscribe();
  }

  async onModuleDestroy() {
    await this.disconnect();
  }

  private async connect() {
    try {
      this.logger.log('Connecting to Kafka...');
      await this.consumer.connect();
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
        await this.consumer.disconnect();
        this.isConnected = false;
        this.logger.log('Successfully disconnected from Kafka');
      } catch (error) {
        this.logger.error('Error disconnecting from Kafka', error);
      }
    }
  }

  private async subscribe() {
    const topic = this.configService.kafkaTopicNormalized;
    try {
      await this.consumer.subscribe({ topic, fromBeginning: false });
      this.logger.log(`Subscribed to topic: ${topic}`);

      await this.consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
          try {
            if (!message.value) {
              this.logger.warn('Received message with no value', {
                topic,
                partition,
                offset: message.offset,
              });
              return;
            }

            const event = JSON.parse(message.value.toString());
            this.logger.debug('Received normalized telemetry event', {
              eventId: event.event_id,
              deviceId: event.device_id,
            });

            if (this.messageHandler) {
              await this.messageHandler(event);
            }
          } catch (error) {
            this.logger.error('Error processing message', {
              error: error instanceof Error ? error.message : String(error),
              topic,
              partition,
              offset: message.offset,
            });
            // Don't throw - allow consumer to continue processing other messages
          }
        },
      });
    } catch (error) {
      this.logger.error('Failed to subscribe to Kafka topic', error);
      throw error;
    }
  }

  setMessageHandler(handler: (message: any) => Promise<void>) {
    this.messageHandler = handler;
  }
}

