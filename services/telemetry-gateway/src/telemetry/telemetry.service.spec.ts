import { Test, TestingModule } from '@nestjs/testing';
import { TelemetryService } from './telemetry.service';
import { KafkaService } from '../kafka/kafka.service';
import { RegistryService } from '../registry/registry.service';
import { TelemetryDto } from '../dto/telemetry.dto';

describe('TelemetryService', () => {
  let service: TelemetryService;
  let kafkaService: jest.Mocked<KafkaService>;
  let registryService: jest.Mocked<RegistryService>;

  beforeEach(async () => {
    const mockKafkaService = {
      produceRawTelemetry: jest.fn().mockResolvedValue(undefined),
    };

    const mockRegistryService = {
      verifyDevice: jest.fn().mockResolvedValue(true),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        TelemetryService,
        {
          provide: KafkaService,
          useValue: mockKafkaService,
        },
        {
          provide: RegistryService,
          useValue: mockRegistryService,
        },
      ],
    }).compile();

    service = module.get<TelemetryService>(TelemetryService);
    kafkaService = module.get(KafkaService);
    registryService = module.get(RegistryService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should process telemetry successfully', async () => {
    const dto: TelemetryDto = {
      deviceId: 'device_123',
      timestamp: '2024-01-15T10:30:00.000Z',
      metrics: {
        hr: 72,
        spo2: 98,
        temp: 98.6,
      },
      meta: {
        battery: 85,
        firmware: 'v1.0.0',
      },
    };

    const result = await service.processTelemetry(dto);

    expect(result.success).toBe(true);
    expect(result.eventId).toBeDefined();
    expect(result.eventId).toMatch(/^evt_/);
    expect(registryService.verifyDevice).toHaveBeenCalledWith('device_123');
    expect(kafkaService.produceRawTelemetry).toHaveBeenCalled();
  });

  it('should reject telemetry if device not found in registry', async () => {
    registryService.verifyDevice.mockResolvedValue(false);

    const dto: TelemetryDto = {
      deviceId: 'device_unknown',
      timestamp: '2024-01-15T10:30:00.000Z',
      metrics: {
        hr: 72,
      },
    };

    await expect(service.processTelemetry(dto)).rejects.toThrow('Device device_unknown not found in registry');
    expect(kafkaService.produceRawTelemetry).not.toHaveBeenCalled();
  });

  it('should transform metrics correctly', async () => {
    const dto: TelemetryDto = {
      deviceId: 'device_123',
      timestamp: '2024-01-15T10:30:00.000Z',
      metrics: {
        hr: 72,
        spo2: 98,
        temp: 98.6,
      },
    };

    await service.processTelemetry(dto);

    expect(kafkaService.produceRawTelemetry).toHaveBeenCalledWith(
      expect.objectContaining({
        event_type: 'telemetry.raw',
        device_id: 'device_123',
        measurements: expect.arrayContaining([
          expect.objectContaining({ metric: 'heart_rate', value: 72, unit: 'bpm' }),
          expect.objectContaining({ metric: 'oxygen_saturation', value: 98, unit: 'percent' }),
          expect.objectContaining({ metric: 'temperature', value: 98.6, unit: 'fahrenheit' }),
        ]),
      }),
    );
  });
});

