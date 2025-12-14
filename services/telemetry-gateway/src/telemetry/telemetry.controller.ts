import { Controller, Post, Body, HttpCode, HttpStatus, BadRequestException } from '@nestjs/common';
import { TelemetryService } from './telemetry.service';
import { TelemetryDto } from '../dto/telemetry.dto';

@Controller('api')
export class TelemetryController {
  constructor(private readonly telemetryService: TelemetryService) {}

  @Post('telemetry')
  @HttpCode(HttpStatus.OK)
  async receiveTelemetry(@Body() dto: TelemetryDto) {
    try {
      const result = await this.telemetryService.processTelemetry(dto);
      return {
        success: true,
        eventId: result.eventId,
        message: 'Telemetry received and processed',
      };
    } catch (error) {
      throw new BadRequestException({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to process telemetry',
      });
    }
  }
}

