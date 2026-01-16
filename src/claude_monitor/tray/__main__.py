"""Entry point for claude-monitor-tray command."""

import argparse
import logging
import sys
from pathlib import Path


def setup_logging() -> None:
    """Setup logging for the tray application."""
    log_dir = Path.home() / ".claude-monitor"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "tray.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="claude-monitor-tray",
        description="System tray monitor for Claude Code usage",
    )
    parser.add_argument(
        "--plan",
        choices=["pro", "max5", "max20", "custom"],
        default=None,
        help="Plan type (pro, max5, max20, custom)",
    )
    parser.add_argument(
        "--refresh-rate",
        type=int,
        default=None,
        help="Refresh rate in seconds (default: 60)",
    )
    return parser.parse_args()


def kill_existing_instances() -> None:
    """Kill any existing tray app instances."""
    import os
    import signal
    import subprocess

    try:
        # Find and kill existing instances (excluding current process)
        current_pid = os.getpid()
        result = subprocess.run(
            ["pgrep", "-f", "claude-monitor-tray"],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            for pid_str in result.stdout.strip().split("\n"):
                if pid_str:
                    pid = int(pid_str)
                    if pid != current_pid:
                        os.kill(pid, signal.SIGTERM)
    except Exception:
        pass  # Ignore errors


def main() -> int:
    """Main entry point for the tray application."""
    # Kill existing instances first
    kill_existing_instances()

    # Parse args first
    args = parse_args()

    # Check dependencies
    from claude_monitor.tray import check_dependencies

    available, error_message = check_dependencies()
    if not available:
        print(error_message, file=sys.stderr)
        return 1

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting Claude Monitor Tray application")

        # Load and update settings from CLI args
        from claude_monitor.tray.settings import TraySettingsManager

        settings_manager = TraySettingsManager()
        settings = settings_manager.load()

        # Override from CLI args
        if args.plan:
            settings.plan = args.plan
            settings_manager.save(settings)
            logger.info(f"Plan set to: {args.plan}")

        if args.refresh_rate:
            settings.refresh_rate = args.refresh_rate
            settings_manager.save(settings)

        # Import and run app
        from claude_monitor.tray.app import TrayApplication

        app = TrayApplication(sys.argv)
        app.start()

        return app.exec()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
