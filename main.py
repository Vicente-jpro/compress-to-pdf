"""Entry point for the compress to pdf application."""
from app.gui import CompressToPdfApp


def main() -> None:
    """Instantiate and run the application."""
    app = CompressToPdfApp()
    app.run()


if __name__ == "__main__":
    main()
