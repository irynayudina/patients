import { NestFactory } from '@nestjs/core';
import { MicroserviceOptions, Transport } from '@nestjs/microservices';
import { join } from 'path';
import { AppModule } from './app.module';

async function bootstrap() {
  // HTTP server
  const app = await NestFactory.create(AppModule);
  
  // gRPC microservice
  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.GRPC,
    options: {
      package: 'telemetry',
      protoPath: join(__dirname, '../proto/telemetry.proto'),
      url: `0.0.0.0:${process.env.GRPC_PORT || 50051}`,
    },
  });

  // Kafka microservice
  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.KAFKA,
    options: {
      client: {
        clientId: 'nestjs-service',
        brokers: (process.env.KAFKA_BROKERS || 'localhost:29092').split(','),
      },
      consumer: {
        groupId: 'nestjs-service-group',
      },
    },
  });

  await app.startAllMicroservices();
  
  const port = process.env.PORT || 3000;
  await app.listen(port);
  
  console.log(`NestJS service is running on: http://0.0.0.0:${port}`);
  console.log(`gRPC service is running on: 0.0.0.0:${process.env.GRPC_PORT || 50051}`);
}

bootstrap();

