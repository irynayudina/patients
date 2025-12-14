# Device Simulator

Realistic device simulator for the Patient Monitoring System. Generates and sends telemetry data with realistic vital signs patterns including baseline values, small noise, and occasional medical episodes (fever spikes, hypoxia, tachycardia).

## Features

- **Realistic Vital Signs Generation**:
  - Baseline values per patient (from threshold profiles)
  - Small Gaussian noise for natural variation
  - Occasional medical episodes with realistic patterns:
    - **Fever Spike**: Temperature rise with increased heart rate
    - **Hypoxia**: Oxygen saturation drop with compensatory heart rate increase
    - **Tachycardia**: Heart rate spike with slight SpO2 decrease

- **Device Management**:
  - Reads patient/device list from Registry service
  - Supports configurable number of virtual devices
  - Uses patient-specific baseline values from threshold profiles

- **Telemetry Delivery**:
  - Primary: gRPC to Telemetry Gateway (preferred)
  - Sends heart rate, oxygen saturation, and temperature measurements
  - Configurable send interval

## Usage

### Command Line Arguments

```bash
python main.py [OPTIONS]
```

**Options:**
- `--devices N`: Number of devices to simulate (default: 5)
- `--interval X`: Interval between telemetry sends in seconds (default: 5)
- `--episode-rate R`: Probability of episode per interval, 0.0 to 1.0 (default: 0.05)
- `--registry-url URL`: Registry service URL (default: http://registry:8000)
- `--gateway-grpc-url URL`: Telemetry Gateway gRPC URL (default: telemetry-gateway:50052)
- `--log-level LEVEL`: Log level - DEBUG, INFO, WARNING, ERROR (default: INFO)

### Examples

```bash
# Simulate 5 devices, send telemetry every 5 seconds, 5% episode rate
python main.py --devices 5 --interval 5 --episode-rate 0.05

# Simulate 10 devices, send telemetry every 2 seconds, 10% episode rate
python main.py --devices 10 --interval 2 --episode-rate 0.1

# High-frequency simulation with more episodes
python main.py --devices 3 --interval 1 --episode-rate 0.15
```

### Docker

```bash
# Build image
docker build -t device-simulator -f services/device-simulator/Dockerfile .

# Run with custom parameters
docker run --rm --network patient-monitoring-network \
  device-simulator \
  python main.py --devices 5 --interval 5 --episode-rate 0.05
```

### Using Make

```bash
# Run simulator (uses defaults from docker-compose)
make simulate

# Or with custom parameters
make simulate DEVICES=10 INTERVAL=2 EPISODE_RATE=0.1
```

## Architecture

The simulator consists of several components:

- **RegistryClient**: Fetches devices and patients from Registry service
- **TelemetryGatewayClient**: gRPC client for sending telemetry
- **VitalGenerator**: Generates realistic vital signs with patterns
- **DeviceSimulator**: Simulates a single device sending telemetry
- **SimulatorManager**: Manages multiple device simulators

## Episode Patterns

### Fever Spike
- Temperature increases (up to 2.5°C above baseline)
- Heart rate increases (up to 15 bpm)
- SpO2 slightly decreases
- Duration: 30-300 seconds
- Intensity follows a bell curve (peaks in middle)

### Hypoxia Episode
- SpO2 drops significantly (up to 10% below baseline)
- Heart rate increases (up to 20 bpm) as compensation
- Temperature slightly increases
- Duration: 30-300 seconds

### Tachycardia Episode
- Heart rate spikes (up to 40 bpm above baseline)
- SpO2 slightly decreases
- Temperature slightly increases
- Duration: 30-300 seconds

## Configuration

Configuration can be provided via:
1. Environment variables (see `config.py`)
2. Command line arguments (takes precedence)

## Requirements

- Python 3.11+
- Registry service running and accessible
- Telemetry Gateway service running with gRPC enabled
- Generated gRPC stubs (created automatically in Dockerfile)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Generate gRPC stubs manually (if needed)
python -m grpc_tools.protoc \
  --proto_path=../../proto \
  --python_out=generated \
  --grpc_python_out=generated \
  ../../proto/telemetry_gateway.proto

# Run locally
python main.py --devices 5 --interval 5
```

