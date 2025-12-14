import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '../config/config.service';
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { join } from 'path';

interface Device {
  device_id: string;
  device_type?: string;
  patient_id?: string;
  status?: number;
  metadata?: { [key: string]: string };
  registered_at?: string;
  updated_at?: string;
}

interface Patient {
  patient_id: string;
  age?: number;
  gender?: number; // 0=UNSPECIFIED, 1=MALE, 2=FEMALE, 3=OTHER
  medical_conditions?: string[];
  medications?: string[];
  allergies?: string[];
  metadata?: { [key: string]: string };
  registered_at?: string;
  updated_at?: string;
}

interface ThresholdProfile {
  profile_id?: string;
  patient_id?: string;
  device_id?: string;
  heart_rate?: any;
  blood_pressure?: any;
  temperature?: any;
  oxygen_saturation?: any;
  respiratory_rate?: any;
  created_at?: string;
  updated_at?: string;
}

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
      this.logger.log('Disconnected from Registry service');
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
      throw error;
    }
  }

  private async callWithRetry<T>(
    operation: () => Promise<T>,
    operationName: string,
  ): Promise<T> {
    const maxRetries = this.configService.registryMaxRetries;
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;
        this.logger.warn(
          `${operationName} failed (attempt ${attempt}/${maxRetries})`,
          {
            error: error instanceof Error ? error.message : String(error),
          },
        );

        if (attempt < maxRetries) {
          const delay = this.configService.registryRetryDelayMs * attempt;
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }
    }

    this.logger.error(`${operationName} failed after ${maxRetries} attempts`, {
      error: lastError?.message,
    });
    throw lastError || new Error(`${operationName} failed`);
  }

  async getDevice(deviceId: string): Promise<Device | null> {
    if (!this.configService.registryEnabled) {
      this.logger.debug('Registry is disabled, returning null for device lookup');
      return null;
    }

    if (!this.isConnected || !this.registryClient) {
      this.logger.warn('Registry client not connected');
      return null;
    }

    return this.callWithRetry(
      () =>
        new Promise<Device | null>((resolve, reject) => {
          const request = {
            version: '1.0.0',
            device_id: deviceId,
          };

          const deadline = new Date();
          deadline.setMilliseconds(
            deadline.getMilliseconds() + this.configService.registryTimeoutMs,
          );

          this.registryClient.GetDevice(
            request,
            { deadline: deadline.getTime() },
            (error: any, response: any) => {
              if (error) {
                if (error.code === grpc.status.NOT_FOUND) {
                  this.logger.debug(`Device ${deviceId} not found in registry`);
                  resolve(null);
                  return;
                }
                reject(error);
                return;
              }

              if (response.status === 1) {
                // STATUS_SUCCESS
                const device: Device = {
                  device_id: response.device?.device_id || deviceId,
                  device_type: response.device?.device_type,
                  patient_id: response.device?.patient_id,
                  status: response.device?.status,
                  metadata: response.device?.metadata || {},
                  registered_at: response.device?.registered_at,
                  updated_at: response.device?.updated_at,
                };
                resolve(device);
              } else if (response.status === 2) {
                // STATUS_NOT_FOUND
                resolve(null);
              } else {
                reject(new Error(`Registry returned status: ${response.status}`));
              }
            },
          );
        }),
      'GetDevice',
    );
  }

  async getPatient(patientId: string): Promise<Patient | null> {
    if (!this.configService.registryEnabled) {
      this.logger.debug('Registry is disabled, returning null for patient lookup');
      return null;
    }

    if (!this.isConnected || !this.registryClient) {
      this.logger.warn('Registry client not connected');
      return null;
    }

    return this.callWithRetry(
      () =>
        new Promise<Patient | null>((resolve, reject) => {
          const request = {
            version: '1.0.0',
            patient_id: patientId,
          };

          const deadline = new Date();
          deadline.setMilliseconds(
            deadline.getMilliseconds() + this.configService.registryTimeoutMs,
          );

          this.registryClient.GetPatient(
            request,
            { deadline: deadline.getTime() },
            (error: any, response: any) => {
              if (error) {
                if (error.code === grpc.status.NOT_FOUND) {
                  this.logger.debug(`Patient ${patientId} not found in registry`);
                  resolve(null);
                  return;
                }
                reject(error);
                return;
              }

              if (response.status === 1) {
                // STATUS_SUCCESS
                const patient: Patient = {
                  patient_id: response.patient?.patient_id || patientId,
                  age: response.patient?.age,
                  gender: response.patient?.gender,
                  medical_conditions: response.patient?.medical_conditions || [],
                  medications: response.patient?.medications || [],
                  allergies: response.patient?.allergies || [],
                  metadata: response.patient?.metadata || {},
                  registered_at: response.patient?.registered_at,
                  updated_at: response.patient?.updated_at,
                };
                resolve(patient);
              } else if (response.status === 2) {
                // STATUS_NOT_FOUND
                resolve(null);
              } else {
                reject(new Error(`Registry returned status: ${response.status}`));
              }
            },
          );
        }),
      'GetPatient',
    );
  }

  async getThresholdProfile(
    patientId: string,
    deviceId?: string,
  ): Promise<ThresholdProfile | null> {
    if (!this.configService.registryEnabled) {
      this.logger.debug('Registry is disabled, returning null for threshold profile lookup');
      return null;
    }

    if (!this.isConnected || !this.registryClient) {
      this.logger.warn('Registry client not connected');
      return null;
    }

    return this.callWithRetry(
      () =>
        new Promise<ThresholdProfile | null>((resolve, reject) => {
          const request: any = {
            version: '1.0.0',
            patient_id: patientId,
          };
          if (deviceId) {
            request.device_id = deviceId;
          }

          const deadline = new Date();
          deadline.setMilliseconds(
            deadline.getMilliseconds() + this.configService.registryTimeoutMs,
          );

          this.registryClient.GetThresholdProfile(
            request,
            { deadline: deadline.getTime() },
            (error: any, response: any) => {
              if (error) {
                if (error.code === grpc.status.NOT_FOUND) {
                  this.logger.debug(
                    `Threshold profile not found for patient ${patientId}`,
                  );
                  resolve(null);
                  return;
                }
                reject(error);
                return;
              }

              if (response.status === 1) {
                // STATUS_SUCCESS
                const profile: ThresholdProfile = {
                  profile_id: response.profile?.profile_id,
                  patient_id: response.profile?.patient_id,
                  device_id: response.profile?.device_id,
                  heart_rate: response.profile?.heart_rate,
                  blood_pressure: response.profile?.blood_pressure,
                  temperature: response.profile?.temperature,
                  oxygen_saturation: response.profile?.oxygen_saturation,
                  respiratory_rate: response.profile?.respiratory_rate,
                  created_at: response.profile?.created_at,
                  updated_at: response.profile?.updated_at,
                };
                resolve(profile);
              } else if (response.status === 2) {
                // STATUS_NOT_FOUND
                resolve(null);
              } else {
                reject(new Error(`Registry returned status: ${response.status}`));
              }
            },
          );
        }),
      'GetThresholdProfile',
    );
  }
}

