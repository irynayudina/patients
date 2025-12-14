import { Module, OnModuleInit } from '@nestjs/common';
import { ConfigService } from './config/config.service';
import { RegistryService } from './registry/registry.service';
import { KafkaConsumerService } from './kafka/kafka-consumer.service';
import { KafkaProducerService } from './kafka/kafka-producer.service';
import { EnrichmentService } from './enrichment/enrichment.service';

@Module({
  imports: [],
  controllers: [],
  providers: [
    ConfigService,
    RegistryService,
    KafkaConsumerService,
    KafkaProducerService,
    EnrichmentService,
  ],
})
export class AppModule implements OnModuleInit {
  constructor(
    private readonly kafkaConsumer: KafkaConsumerService,
    private readonly enrichmentService: EnrichmentService,
  ) {}

  async onModuleInit() {
    // Set up message handler for Kafka consumer after all services are initialized
    this.kafkaConsumer.setMessageHandler(async (message) => {
      await this.enrichmentService.enrichTelemetry(message);
    });
    // Start consuming after handler is set
    await this.kafkaConsumer.startConsuming();
  }
}

