import { Module, ValidationPipe, OnModuleInit, Logger } from '@nestjs/common';
import { APP_PIPE } from '@nestjs/core';
import { IncidentController } from './incident/incident.controller';
import { IncidentService } from './incident/incident.service';
import { HealthController } from './health/health.controller';
import { PrismaService } from './prisma/prisma.service';
import { KafkaConsumerService } from './kafka/kafka-consumer.service';
import { ConfigService } from './config/config.service';

@Module({
  imports: [],
  controllers: [IncidentController, HealthController],
  providers: [
    IncidentService,
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
    private readonly incidentService: IncidentService,
  ) {}

  async onModuleInit() {
    // Set up Kafka message handler
    this.kafkaConsumer.setMessageHandler(async (alertEvent) => {
      try {
        await this.incidentService.createFromAlert(alertEvent);
      } catch (error) {
        // Log error but don't throw - allow consumer to continue
        this.logger.error('Error creating incident from alert', {
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

