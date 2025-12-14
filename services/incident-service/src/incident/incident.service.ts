import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateIncidentDto } from './dto/create-incident.dto';
import { UpdateIncidentStatusDto } from './dto/update-incident-status.dto';
import { IncidentStatus, IncidentSeverity } from './enums/incident.enums';

@Injectable()
export class IncidentService {
  private readonly logger = new Logger(IncidentService.name);

  constructor(private readonly prisma: PrismaService) {}

  async create(createIncidentDto: CreateIncidentDto) {
    this.logger.log('Creating incident', {
      patientId: createIncidentDto.patientId,
      type: createIncidentDto.type,
      severity: createIncidentDto.severity,
    });

    return this.prisma.incident.create({
      data: {
        patientId: createIncidentDto.patientId,
        deviceId: createIncidentDto.deviceId,
        severity: createIncidentDto.severity,
        type: createIncidentDto.type,
        status: IncidentStatus.OPEN,
        details: createIncidentDto.details || {},
      },
    });
  }

  async findAll(filters: {
    status?: string;
    severity?: string;
    patientId?: string;
    page?: number;
    limit?: number;
  }) {
    const page = filters.page || 1;
    const limit = Math.min(filters.limit || 20, 100); // Max 100 per page
    const skip = (page - 1) * limit;

    const where: any = {};
    if (filters.status) {
      where.status = filters.status;
    }
    if (filters.severity) {
      where.severity = filters.severity;
    }
    if (filters.patientId) {
      where.patientId = filters.patientId;
    }

    const [incidents, total] = await Promise.all([
      this.prisma.incident.findMany({
        where,
        skip,
        take: limit,
        orderBy: {
          createdAt: 'desc',
        },
      }),
      this.prisma.incident.count({ where }),
    ]);

    return {
      data: incidents,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async findOne(id: string) {
    return this.prisma.incident.findUnique({
      where: { id },
    });
  }

  async updateStatus(id: string, updateStatusDto: UpdateIncidentStatusDto) {
    this.logger.log('Updating incident status', {
      id,
      status: updateStatusDto.status,
    });

    return this.prisma.incident.update({
      where: { id },
      data: {
        status: updateStatusDto.status,
        updatedAt: new Date(),
      },
    });
  }

  async createFromAlert(alertEvent: any) {
    this.logger.log('Creating incident from alert', {
      eventId: alertEvent.event_id,
      patientId: alertEvent.patient_id,
      alertType: alertEvent.alert_type,
    });

    // Map alert severity to incident severity
    const severityMap: Record<string, string> = {
      low: IncidentSeverity.LOW,
      medium: IncidentSeverity.MEDIUM,
      high: IncidentSeverity.HIGH,
      critical: IncidentSeverity.CRITICAL,
    };

    const severity = severityMap[alertEvent.severity?.toLowerCase()] || IncidentSeverity.MEDIUM;

    return this.create({
      patientId: alertEvent.patient_id,
      deviceId: alertEvent.device_id,
      severity,
      type: alertEvent.alert_type || 'unknown',
      details: {
        eventId: alertEvent.event_id,
        sourceEventId: alertEvent.source_event_id,
        timestamp: alertEvent.timestamp,
        condition: alertEvent.condition,
        recommendedActions: alertEvent.recommended_actions,
        patientContext: alertEvent.patient_context,
        alertMetadata: alertEvent.alert_metadata,
      },
    });
  }
}

