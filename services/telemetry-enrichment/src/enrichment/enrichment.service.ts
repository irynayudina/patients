import { Injectable, Logger } from '@nestjs/common';
import { RegistryService } from '../registry/registry.service';
import { KafkaProducerService } from '../kafka/kafka-producer.service';
import { v4 as uuidv4 } from 'uuid';

interface NormalizedTelemetryEvent {
  event_id: string;
  event_type: string;
  version?: string;
  timestamp: string;
  source_event_id?: string;
  device_id: string;
  patient_id?: string;
  vitals: any;
  validation_status?: string;
  normalization_metadata?: any;
}

interface EnrichedTelemetryEvent {
  event_id: string;
  trace_id: string;
  event_type: string;
  version: string;
  timestamp: string;
  source_event_id: string;
  device_id: string;
  patient_id?: string;
  orphan?: boolean;
  patientProfile?: {
    age?: number;
    sex?: string;
  };
  thresholds?: any;
  vitals: any;
  enrichment_metadata: {
    enriched_at: string;
    enrichment_sources: string[];
  };
}

@Injectable()
export class EnrichmentService {
  private readonly logger = new Logger(EnrichmentService.name);

  constructor(
    private readonly registryService: RegistryService,
    private readonly kafkaProducer: KafkaProducerService,
  ) {}

  async enrichTelemetry(normalizedEvent: NormalizedTelemetryEvent): Promise<void> {
    try {
      this.logger.debug('Enriching telemetry event', {
        eventId: normalizedEvent.event_id,
        deviceId: normalizedEvent.device_id,
      });

      const deviceId = normalizedEvent.device_id;
      let patientId = normalizedEvent.patient_id;
      let orphan = false;

      // Step 1: Get device to map deviceId -> patientId
      const device = await this.registryService.getDevice(deviceId);
      if (device && device.patient_id) {
        patientId = device.patient_id;
        this.logger.debug('Mapped device to patient', {
          deviceId,
          patientId,
        });
      } else {
        // Device not found or not linked to patient
        if (!patientId) {
          orphan = true;
          this.logger.warn('Device not linked to patient, marking as orphan', {
            deviceId,
            eventId: normalizedEvent.event_id,
          });
        }
      }

      // Step 2: Get patient info and thresholds (if patientId is available)
      let patientProfile: { age?: number; sex?: string } | undefined;
      let thresholds: any | undefined;
      const enrichmentSources: string[] = [];

      if (patientId && !orphan) {
        try {
          // Get patient info
          const patient = await this.registryService.getPatient(patientId);
          if (patient) {
            enrichmentSources.push('patient_registry');
            patientProfile = {
              age: patient.age,
              sex: this.mapGenderToString(patient.gender),
            };
            this.logger.debug('Retrieved patient profile', {
              patientId,
              age: patient.age,
              gender: patient.gender,
            });
          }

          // Get thresholds
          const thresholdProfile = await this.registryService.getThresholdProfile(
            patientId,
            deviceId,
          );
          if (thresholdProfile) {
            enrichmentSources.push('threshold_registry');
            thresholds = {
              heart_rate: thresholdProfile.heart_rate,
              blood_pressure: thresholdProfile.blood_pressure,
              temperature: thresholdProfile.temperature,
              oxygen_saturation: thresholdProfile.oxygen_saturation,
              respiratory_rate: thresholdProfile.respiratory_rate,
            };
            this.logger.debug('Retrieved threshold profile', {
              patientId,
              deviceId,
            });
          }
        } catch (error) {
          this.logger.error('Error fetching patient info or thresholds', {
            error: error instanceof Error ? error.message : String(error),
            patientId,
            deviceId,
          });
          // Continue with enrichment even if patient/threshold lookup fails
        }
      }

      // Step 3: Build enriched event
      // Extract trace_id from source event, or generate new one if missing
      const traceId = (normalizedEvent as any).trace_id || `trace_${uuidv4()}`;
      
      const enrichedEvent: EnrichedTelemetryEvent = {
        event_id: uuidv4(),
        trace_id: traceId,
        event_type: 'telemetry.enriched',
        version: normalizedEvent.version || '1.0.0',
        timestamp: new Date().toISOString(),
        source_event_id: normalizedEvent.event_id,
        device_id: deviceId,
        patient_id: patientId || undefined,
        ...(orphan && { orphan: true }),
        ...(patientProfile && { patientProfile }),
        ...(thresholds && { thresholds }),
        vitals: normalizedEvent.vitals,
        enrichment_metadata: {
          enriched_at: new Date().toISOString(),
          enrichment_sources: enrichmentSources.length > 0 ? enrichmentSources : ['none'],
        },
      };

      // Step 4: Produce enriched event
      await this.kafkaProducer.produceEnrichedTelemetry(enrichedEvent);

      this.logger.log('Successfully enriched and produced telemetry event', {
        eventId: enrichedEvent.event_id,
        traceId: enrichedEvent.trace_id,
        sourceEventId: normalizedEvent.event_id,
        deviceId,
        patientId: patientId || 'none',
        orphan,
      });
    } catch (error) {
      this.logger.error('Error enriching telemetry', {
        error: error instanceof Error ? error.message : String(error),
        eventId: normalizedEvent.event_id,
        deviceId: normalizedEvent.device_id,
      });
      throw error;
    }
  }

  private mapGenderToString(gender?: number): string | undefined {
    if (gender === undefined || gender === null) {
      return undefined;
    }
    // GENDER_UNSPECIFIED = 0, GENDER_MALE = 1, GENDER_FEMALE = 2, GENDER_OTHER = 3
    switch (gender) {
      case 1:
        return 'male';
      case 2:
        return 'female';
      case 3:
        return 'other';
      default:
        return 'unknown';
    }
  }
}

