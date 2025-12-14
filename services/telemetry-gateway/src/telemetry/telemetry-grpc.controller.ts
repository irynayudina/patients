import { Controller, Logger } from '@nestjs/common';
import { GrpcMethod } from '@nestjs/microservices';
import { TelemetryService } from './telemetry.service';
import { TelemetryDto } from '../dto/telemetry.dto';

@Controller()
export class TelemetryGrpcController {
  private readonly logger = new Logger(TelemetryGrpcController.name);

  constructor(private readonly telemetryService: TelemetryService) {}

  @GrpcMethod('TelemetryGateway', 'SendMeasurements')
  async sendMeasurements(data: any): Promise<any> {
    try {
      // Transform gRPC request to DTO
      const dto = this.transformGrpcToDto(data);

      // Process telemetry
      const result = await this.telemetryService.processTelemetry(dto);

      return {
        version: '1.0.0',
        status: 1, // STATUS_SUCCESS
        message: 'Measurements received and processed',
        event_id: result.eventId,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      this.logger.error('Error processing gRPC request', error);

      // Determine status based on error
      let status = 4; // STATUS_INTERNAL_ERROR
      if (error instanceof Error && error.message.includes('not found')) {
        status = 3; // STATUS_DEVICE_NOT_FOUND
      } else if (error instanceof Error && error.message.includes('validation')) {
        status = 2; // STATUS_VALIDATION_ERROR
      }

      return {
        version: '1.0.0',
        status: status,
        message: error instanceof Error ? error.message : 'Internal error',
        event_id: '',
        timestamp: new Date().toISOString(),
      };
    }
  }

  private transformGrpcToDto(data: any): TelemetryDto {
    // Transform gRPC measurements array to metrics object
    const metrics: any = {};
    const meta: any = {};

    if (data.measurements && Array.isArray(data.measurements)) {
      for (const measurement of data.measurements) {
        const metricName = measurement.metric?.toLowerCase();
        if (metricName === 'heart_rate' || metricName === 'hr') {
          metrics.hr = measurement.value;
        } else if (metricName === 'oxygen_saturation' || metricName === 'spo2') {
          metrics.spo2 = measurement.value;
        } else if (metricName === 'temperature' || metricName === 'temp') {
          metrics.temp = measurement.value;
        }
      }
    }

    // Extract metadata
    if (data.device_metadata) {
      if (data.device_metadata.battery !== undefined || data.device_metadata.battery_level !== undefined) {
        meta.battery = parseFloat(data.device_metadata.battery || data.device_metadata.battery_level);
      }
      if (data.device_metadata.firmware || data.device_metadata.firmware_version) {
        meta.firmware = data.device_metadata.firmware || data.device_metadata.firmware_version;
      }
    }

    return {
      deviceId: data.device_id,
      timestamp: data.timestamp || new Date().toISOString(),
      metrics: metrics,
      meta: Object.keys(meta).length > 0 ? meta : undefined,
    };
  }
}

