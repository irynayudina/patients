"""Main entry point for device simulator"""
import argparse
import logging
import signal
import sys
from config import settings
from device_simulator import SimulatorManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Device Simulator for Patient Monitoring System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simulate 5 devices, send telemetry every 5 seconds, 5% episode rate
  python main.py --devices 5 --interval 5 --episode-rate 0.05
  
  # Simulate 10 devices, send telemetry every 2 seconds, 10% episode rate
  python main.py --devices 10 --interval 2 --episode-rate 0.1
        """
    )
    
    parser.add_argument(
        '--devices',
        type=int,
        default=settings.default_devices,
        help=f'Number of devices to simulate (default: {settings.default_devices})'
    )
    
    parser.add_argument(
        '--interval',
        type=float,
        default=settings.default_interval,
        help=f'Interval between telemetry sends in seconds (default: {settings.default_interval})'
    )
    
    parser.add_argument(
        '--episode-rate',
        type=float,
        default=settings.default_episode_rate,
        help=f'Probability of episode per interval, 0.0 to 1.0 (default: {settings.default_episode_rate})'
    )
    
    parser.add_argument(
        '--registry-url',
        type=str,
        default=settings.registry_url,
        help=f'Registry service URL (default: {settings.registry_url})'
    )
    
    parser.add_argument(
        '--gateway-grpc-url',
        type=str,
        default=settings.gateway_grpc_url,
        help=f'Telemetry Gateway gRPC URL (default: {settings.gateway_grpc_url})'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default=settings.log_level,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help=f'Log level (default: {settings.log_level})'
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Validate arguments
    if args.devices < 1:
        logger.error("Number of devices must be at least 1")
        sys.exit(1)
    
    if args.interval < 0.1:
        logger.error("Interval must be at least 0.1 seconds")
        sys.exit(1)
    
    if not 0.0 <= args.episode_rate <= 1.0:
        logger.error("Episode rate must be between 0.0 and 1.0")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Device Simulator for Patient Monitoring System")
    logger.info("=" * 60)
    logger.info(f"Devices: {args.devices}")
    logger.info(f"Interval: {args.interval} seconds")
    logger.info(f"Episode Rate: {args.episode_rate * 100:.1f}%")
    logger.info(f"Registry URL: {args.registry_url}")
    logger.info(f"Gateway gRPC URL: {args.gateway_grpc_url}")
    logger.info("=" * 60)
    
    # Create simulator manager
    manager = SimulatorManager(
        registry_url=args.registry_url,
        gateway_grpc_url=args.gateway_grpc_url,
        num_devices=args.devices,
        interval=args.interval,
        episode_rate=args.episode_rate
    )
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\nReceived shutdown signal, stopping simulators...")
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and start
        manager.initialize()
        manager.start_all()
        
        # Keep running
        logger.info("Simulator running. Press Ctrl+C to stop.")
        while True:
            import time
            time.sleep(10)
            stats = manager.get_stats()
            logger.info(
                f"Stats: {stats['num_devices']} devices, "
                f"{stats['total_telemetry_sent']} telemetry sent"
            )
    
    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt, stopping simulators...")
        manager.stop_all()
    except Exception as e:
        logger.error(f"Error in simulator: {e}", exc_info=True)
        manager.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    main()

