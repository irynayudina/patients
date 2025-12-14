import { IsString, IsOptional, IsObject, IsEnum } from 'class-validator';
import { IncidentSeverity } from '../enums/incident.enums';

export class CreateIncidentDto {
  @IsString()
  patientId: string;

  @IsString()
  @IsOptional()
  deviceId?: string;

  @IsEnum(IncidentSeverity)
  severity: string;

  @IsString()
  type: string;

  @IsObject()
  @IsOptional()
  details?: Record<string, any>;
}

