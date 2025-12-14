import {
  Controller,
  Get,
  Post,
  Patch,
  Param,
  Query,
  Body,
  HttpCode,
  HttpStatus,
  NotFoundException,
} from '@nestjs/common';
import { IncidentService } from './incident.service';
import { QueryIncidentsDto } from './dto/query-incidents.dto';
import { UpdateIncidentStatusDto } from './dto/update-incident-status.dto';

@Controller('incidents')
export class IncidentController {
  constructor(private readonly incidentService: IncidentService) {}

  @Get()
  @HttpCode(HttpStatus.OK)
  async findAll(@Query() query: QueryIncidentsDto) {
    return this.incidentService.findAll({
      status: query.status,
      severity: query.severity,
      patientId: query.patientId,
      page: query.page,
      limit: query.limit,
    });
  }

  @Get(':id')
  @HttpCode(HttpStatus.OK)
  async findOne(@Param('id') id: string) {
    const incident = await this.incidentService.findOne(id);
    if (!incident) {
      throw new NotFoundException(`Incident with ID ${id} not found`);
    }
    return incident;
  }

  @Patch(':id')
  @HttpCode(HttpStatus.OK)
  async updateStatus(
    @Param('id') id: string,
    @Body() updateStatusDto: UpdateIncidentStatusDto,
  ) {
    const incident = await this.incidentService.findOne(id);
    if (!incident) {
      throw new NotFoundException(`Incident with ID ${id} not found`);
    }
    return this.incidentService.updateStatus(id, updateStatusDto);
  }
}
