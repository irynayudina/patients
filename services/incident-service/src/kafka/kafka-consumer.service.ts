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
  private connectionRetryAttempts = 0;

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
    // Don't throw error if Kafka is unavailable - retry in background
    this.connectWithRetry().catch((error) => {
      this.logger.warn('Initial Kafka connection failed, will retry in background', {
        error: error instanceof Error ? error.message : String(error),
      });
    });
  }

  async onModuleDestroy() {
    await this.disconnect();
  }

  private async connectWithRetry(): Promise<void> {
    const maxAttempts = this.configService.kafkaConnectionRetryAttempts;
    const retryDelay = this.configService.kafkaConnectionRetryDelay;

    while (this.connectionRetryAttempts < maxAttempts) {
      try {
        await this.connect();
        this.connectionRetryAttempts = 0; // Reset on success
        return;
      } catch (error) {
        this.connectionRetryAttempts++;
        this.logger.warn(
          `Failed to connect to Kafka (attempt ${this.connectionRetryAttempts}/${maxAttempts})`,
          {
            error: error instanceof Error ? error.message : String(error),
          },
        );

        if (this.connectionRetryAttempts < maxAttempts) {
          this.logger.log(`Retrying connection in ${retryDelay}ms...`);
          await new Promise((resolve) => setTimeout(resolve, retryDelay));
        } else {
          this.logger.error('Max retry attempts reached. Service will continue without Kafka connection.');
          // Don't throw - allow service to start without Kafka
          return;
        }
      }
    }
  }

  private async connect() {
    if (this.isConnected) {
      return;
    }

    this.logger.log('Connecting to Kafka...');
    await this.consumer.connect();
    this.isConnected = true;
    this.logger.log('Successfully connected to Kafka');

    // If message handler is already set, start consuming
    if (this.messageHandler) {
      await this.subscribe();
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

  async startConsuming() {
    if (!this.messageHandler) {
      throw new Error('Message handler must be set before starting consumption');
    }

    if (!this.isConnected) {
      // Try to connect if not already connected
      await this.connectWithRetry();
    }

    if (this.isConnected) {
      await this.subscribe();
    } else {
      this.logger.warn('Kafka not connected, consumption will start when connection is established');
    }
  }

  private async subscribe() {
    if (!this.isConnected) {
      return;
    }

    const topic = this.configService.kafkaTopicAlerts;
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
            this.logger.debug('Received alert event', {
              eventId: event.event_id,
              patientId: event.patient_id,
              alertType: event.alert_type,
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
      // Don't throw - allow service to continue
    }
  }

  setMessageHandler(handler: (message: any) => Promise<void>) {
    this.messageHandler = handler;
    
    // If already connected, start consuming immediately
    if (this.isConnected) {
      this.subscribe().catch((error) => {
        this.logger.error('Failed to start consuming after setting handler', error);
      });
    }
  }

  // Method to manually retry connection (can be called from health check or admin endpoint)
  async retryConnection(): Promise<boolean> {
    if (this.isConnected) {
      return true;
    }

    try {
      await this.connectWithRetry();
      return this.isConnected;
    } catch (error) {
      this.logger.error('Manual connection retry failed', error);
      return false;
    }
  }

  get isKafkaConnected(): boolean {
    return this.isConnected;
  }
}

