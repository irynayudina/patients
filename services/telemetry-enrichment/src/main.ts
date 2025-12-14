import { NestFactory } from '@nestjs/core';
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

  console.log(`Telemetry Enrichment Service is starting...`);

  // Graceful shutdown handler
  const shutdown = async (signal: string) => {
    console.log(`Received ${signal}, starting graceful shutdown...`);
    const shutdownTimeout = setTimeout(() => {
      console.error('Graceful shutdown timeout exceeded, forcing exit');
      process.exit(1);
    }, configService.gracefulShutdownTimeoutMs);

    try {
      await app.close();
      clearTimeout(shutdownTimeout);
      console.log('Application closed successfully');
      process.exit(0);
    } catch (error) {
      clearTimeout(shutdownTimeout);
      console.error('Error during shutdown:', error);
      process.exit(1);
    }
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  // Handle uncaught exceptions
  process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
    shutdown('uncaughtException');
  });

  // Handle unhandled promise rejections
  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled rejection at:', promise, 'reason:', reason);
    shutdown('unhandledRejection');
  });

  console.log(`Telemetry Enrichment Service is running`);
}

bootstrap();

