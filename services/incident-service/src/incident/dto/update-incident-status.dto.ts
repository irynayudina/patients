import { IsEnum } from 'class-validator';
import { IncidentStatus } from '../enums/incident.enums';

export class UpdateIncidentStatusDto {
  @IsEnum(IncidentStatus)
  status: IncidentStatus;
}

