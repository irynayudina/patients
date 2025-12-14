import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ClientGrpc, ClientProxyFactory, Transport } from '@nestjs/microservices';
import { join } from 'path';
import { ConfigService } from '../config/config.service';
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';

@Injectable()
export class RegistryService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(RegistryService.name);
  private registryClient: any;
  private isConnected = false;

  constructor(private readonly configService: ConfigService) {}

  async onModuleInit() {
    if (this.configService.registryEnabled) {
      await this.connect();
    } else {
      this.logger.log('Registry service is disabled (REGISTRY_ENABLED=false)');
    }
  }

  async onModuleDestroy() {
    if (this.isConnected && this.registryClient) {
      this.registryClient.close();
      this.isConnected = false;
    }
  }

  private async connect() {
    try {
      const protoPath = join(__dirname, '../../../proto/registry.proto');
      const packageDefinition = protoLoader.loadSync(protoPath, {
        keepCase: true,
        longs: String,
        enums: String,
        defaults: true,
        oneofs: true,
      });

      const registryProto = grpc.loadPackageDefinition(packageDefinition) as any;
      const RegistryService = registryProto.registry.Registry;

      this.registryClient = new RegistryService(
        this.configService.registryGrpcUrl,
        grpc.credentials.createInsecure(),
      );

      this.isConnected = true;
      this.logger.log(`Connected to Registry service at ${this.configService.registryGrpcUrl}`);
    } catch (error) {
      this.logger.error('Failed to connect to Registry service', error);
      // Don't throw - allow service to continue without registry validation
    }
  }

  async verifyDevice(deviceId: string): Promise<boolean> {
    if (!this.configService.registryEnabled) {
      this.logger.debug('Registry validation is disabled, skipping device verification');
      return true;
    }

    if (!this.isConnected || !this.registryClient) {
      this.logger.warn('Registry client not connected, skipping device verification');
      return true; // Allow through if registry is unavailable
    }

    return new Promise((resolve) => {
      const request = {
        version: '1.0.0',
        device_id: deviceId,
      };

      const deadline = new Date();
      deadline.setSeconds(deadline.getSeconds() + 5);

      this.registryClient.GetDevice(
        request,
        { deadline: deadline.getTime() },
        (error: any, response: any) => {
          if (error) {
            this.logger.warn(`Device verification failed for ${deviceId}`, {
              error: error.message,
            });
            // If registry is unavailable, allow the request through
            resolve(true);
            return;
          }

          if (response.status === 1) {
            // STATUS_SUCCESS
            this.logger.debug(`Device ${deviceId} verified successfully`);
            resolve(true);
          } else {
            this.logger.warn(`Device ${deviceId} not found in registry`);
            resolve(false);
          }
        },
      );
    });
  }
}

