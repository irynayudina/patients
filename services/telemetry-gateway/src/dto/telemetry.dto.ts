import { IsString, IsNotEmpty, IsObject, IsOptional, IsNumber, ValidateNested, IsISO8601, ValidateIf, Validate } from 'class-validator';
import { Type } from 'class-transformer';

export class MetricsDto {
  @IsNumber()
  @IsOptional()
  hr?: number;

  @IsNumber()
  @IsOptional()
  spo2?: number;

  @IsNumber()
  @IsOptional()
  temp?: number;
}

export class MetaDto {
  @IsNumber()
  @IsOptional()
  battery?: number;

  @IsString()
  @IsOptional()
  firmware?: string;
}

export class TelemetryDto {
  @IsString()
  @IsNotEmpty()
  deviceId: string;

  @IsString()
  @IsISO8601()
  @IsNotEmpty()
  timestamp: string;

  @IsObject()
  @ValidateNested()
  @Type(() => MetricsDto)
  @IsNotEmpty()
  @Validate((value: MetricsDto) => {
    return value.hr !== undefined || value.spo2 !== undefined || value.temp !== undefined;
  }, {
    message: 'At least one metric (hr, spo2, or temp) must be provided',
  })
  metrics: MetricsDto;

  @IsObject()
  @ValidateNested()
  @Type(() => MetaDto)
  @IsOptional()
  meta?: MetaDto;
}

