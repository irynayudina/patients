import { Injectable, Logger } from '@nestjs/common';
import { v4 as uuidv4 } from 'uuid';
import { KafkaService } from '../kafka/kafka.service';
import { RegistryService } from '../registry/registry.service';
import { TelemetryDto } from '../dto/telemetry.dto';

@Injectable()
export class TelemetryService {
  private readonly logger = new Logger(TelemetryService.name);

  constructor(
    private readonly kafkaService: KafkaService,
    private readonly registryService: RegistryService,
  ) {}

  async processTelemetry(dto: TelemetryDto): Promise<{ eventId: string; success: boolean }> {
    // Verify device exists (if registry is enabled)
    const deviceVerified = await this.registryService.verifyDevice(dto.deviceId);
    if (!deviceVerified) {
      throw new Error(`Device ${dto.deviceId} not found in registry`);
    }

    // Transform DTO to Kafka event format
    const event = this.transformToKafkaEvent(dto);

    // Produce to Kafka
    await this.kafkaService.produceRawTelemetry(event);

    this.logger.log('Telemetry processed successfully', {
      eventId: event.event_id,
      traceId: event.trace_id,
      deviceId: dto.deviceId,
    });

    return {
      eventId: event.event_id,
      success: true,
    };
  }

  private transformToKafkaEvent(dto: TelemetryDto): any {
    const eventId = `evt_${uuidv4()}`;
    const traceId = `trace_${uuidv4()}`;
    const timestamp = dto.timestamp || new Date().toISOString();

    // Transform metrics to measurements array
    const measurements: any[] = [];

    if (dto.metrics.hr !== undefined && dto.metrics.hr !== null) {
      measurements.push({
        metric: 'heart_rate',
        value: dto.metrics.hr,
        unit: 'bpm',
      });
    }

    if (dto.metrics.spo2 !== undefined && dto.metrics.spo2 !== null) {
      measurements.push({
        metric: 'oxygen_saturation',
        value: dto.metrics.spo2,
        unit: 'percent',
      });
    }

    if (dto.metrics.temp !== undefined && dto.metrics.temp !== null) {
      measurements.push({
        metric: 'temperature',
        value: dto.metrics.temp,
        unit: 'fahrenheit',
      });
    }

    if (measurements.length === 0) {
      throw new Error('At least one metric must be provided');
    }

    // Build metadata object
    const metadata: any = {};
    if (dto.meta?.battery !== undefined && dto.meta.battery !== null) {
      metadata.battery_level = dto.meta.battery;
    }
    if (dto.meta?.firmware) {
      metadata.firmware_version = dto.meta.firmware;
    }

    return {
      event_id: eventId,
      trace_id: traceId,
      event_type: 'telemetry.raw',
      version: '1.0.0',
      timestamp: timestamp,
      device_id: dto.deviceId,
      measurements: measurements,
      ...(Object.keys(metadata).length > 0 && { metadata }),
    };
  }
}

