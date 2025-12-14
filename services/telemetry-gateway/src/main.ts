import { NestFactory } from '@nestjs/core';
import { MicroserviceOptions, Transport } from '@nestjs/microservices';
import { join } from 'path';
import { AppModule } from './app.module';
import { ConfigService } from './config/config.service';
import { WinstonModule } from 'nest-winston';
import * as winston from 'winston';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    logger: WinstonModule.createLogger({
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.errors({ stack: true }),
            winston.format.json(),
          ),
        }),
      ],
    }),
  });

  const configService = app.get(ConfigService);

  // Enable CORS if needed
  app.enableCors();

  // Connect gRPC microservice
  // Proto path: in dev it's ../../../proto, in production (dist) it's ../proto
  const protoPath = join(__dirname, '../proto/telemetry_gateway.proto');
  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.GRPC,
    options: {
      package: 'telemetry.gateway',
      protoPath: protoPath,
      url: `0.0.0.0:${configService.grpcPort}`,
    },
  });

  // Start all microservices
  await app.startAllMicroservices();

  // Start HTTP server
  const port = configService.port;
  await app.listen(port);

  console.log(`Telemetry Gateway HTTP server is running on: http://0.0.0.0:${port}`);
  console.log(`Telemetry Gateway gRPC server is running on: 0.0.0.0:${configService.grpcPort}`);

  // Graceful shutdown
  const shutdown = async (signal: string) => {
    console.log(`Received ${signal}, starting graceful shutdown...`);
    try {
      await app.close();
      console.log('Application closed successfully');
      process.exit(0);
    } catch (error) {
      console.error('Error during shutdown:', error);
      process.exit(1);
    }
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

bootstrap();

