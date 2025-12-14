import { Module, ValidationPipe, OnModuleInit, Logger } from '@nestjs/common';
import { APP_PIPE } from '@nestjs/core';
import { NotificationController } from './notification/notification.controller';
import { NotificationService } from './notification/notification.service';
import { RateLimitService } from './notification/rate-limit.service';
import { HealthController } from './health/health.controller';
import { PrismaService } from './prisma/prisma.service';
import { KafkaConsumerService } from './kafka/kafka-consumer.service';
import { ConfigService } from './config/config.service';

@Module({
  imports: [],
  controllers: [NotificationController, HealthController],
  providers: [
    NotificationService,
    RateLimitService,
    PrismaService,
    KafkaConsumerService,
    ConfigService,
    {
      provide: APP_PIPE,
      useValue: new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    },
  ],
})
export class AppModule implements OnModuleInit {
  private readonly logger = new Logger(AppModule.name);

  constructor(
    private readonly kafkaConsumer: KafkaConsumerService,
    private readonly notificationService: NotificationService,
  ) {}

  async onModuleInit() {
    // Set up Kafka message handler
    this.kafkaConsumer.setMessageHandler(async (alertEvent) => {
      try {
        await this.notificationService.createFromAlert(alertEvent);
      } catch (error) {
        // Log error but don't throw - allow consumer to continue
        this.logger.error('Error creating notification from alert', {
          error: error instanceof Error ? error.message : String(error),
          eventId: alertEvent.event_id,
        });
      }
    });

    // Start consuming (will retry connection if needed)
    this.kafkaConsumer.startConsuming().catch((error) => {
      this.logger.error('Failed to start Kafka consumption', {
        error: error instanceof Error ? error.message : String(error),
      });
    });
  }
}

