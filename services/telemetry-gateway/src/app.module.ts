import { Module, ValidationPipe } from '@nestjs/common';
import { APP_PIPE } from '@nestjs/core';
import { TelemetryController } from './telemetry/telemetry.controller';
import { TelemetryGrpcController } from './telemetry/telemetry-grpc.controller';
import { TelemetryService } from './telemetry/telemetry.service';
import { KafkaService } from './kafka/kafka.service';
import { RegistryService } from './registry/registry.service';
import { ConfigService } from './config/config.service';

@Module({
  imports: [],
  controllers: [TelemetryController, TelemetryGrpcController],
  providers: [
    TelemetryService,
    KafkaService,
    RegistryService,
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
export class AppModule {}

