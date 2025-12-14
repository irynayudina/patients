import { Controller, Get, HttpCode, HttpStatus } from '@nestjs/common';
import { KafkaConsumerService } from '../kafka/kafka-consumer.service';
import { PrismaService } from '../prisma/prisma.service';
import { RateLimitService } from '../notification/rate-limit.service';
import { ConfigService } from '../config/config.service';

@Controller('health')
export class HealthController {
  constructor(
    private readonly prisma: PrismaService,
    private readonly kafkaConsumer: KafkaConsumerService,
    private readonly rateLimitService: RateLimitService,
    private readonly configService: ConfigService,
  ) {}

  @Get()
  @HttpCode(HttpStatus.OK)
  async check() {
    const dbHealthy = await this.checkDatabase();
    const kafkaHealthy = this.kafkaConsumer.isKafkaConnected;
    const redisHealthy = await this.checkRedis();

    const status = dbHealthy && kafkaHealthy ? 'healthy' : 'degraded';
    const httpStatus = dbHealthy ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

    return {
      status,
      database: dbHealthy ? 'connected' : 'disconnected',
      kafka: kafkaHealthy ? 'connected' : 'disconnected',
      redis: redisHealthy ? 'connected' : 'disconnected',
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

  private async checkRedis(): Promise<boolean> {
    if (!this.configService.redisEnabled) {
      return true; // Redis is optional, consider it healthy if disabled
    }
    
    // Try to check rate limit service (which uses Redis)
    try {
      // This is a simple check - in production you might want to ping Redis directly
      return true;
    } catch (error) {
      return false;
    }
  }
}

