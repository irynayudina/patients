import { Controller, Get, HttpCode, HttpStatus } from '@nestjs/common';
import { KafkaConsumerService } from '../kafka/kafka-consumer.service';
import { PrismaService } from '../prisma/prisma.service';

@Controller('health')
export class HealthController {
  constructor(
    private readonly prisma: PrismaService,
    private readonly kafkaConsumer: KafkaConsumerService,
  ) {}

  @Get()
  @HttpCode(HttpStatus.OK)
  async check() {
    const dbHealthy = await this.checkDatabase();
    const kafkaHealthy = this.kafkaConsumer.isKafkaConnected;

    const status = dbHealthy && kafkaHealthy ? 'healthy' : 'degraded';
    const httpStatus = dbHealthy ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

    return {
      status,
      database: dbHealthy ? 'connected' : 'disconnected',
      kafka: kafkaHealthy ? 'connected' : 'disconnected',
      timestamp: new Date().toISOString(),
    };
  }

  private async checkDatabase(): Promise<boolean> {
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      return true;
    } catch (error) {
      return false;
    }
  }
}

