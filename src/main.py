# main.py
# Main application entry point using modular structure

from .ui import create_ui


def main():
    """Main application entry point"""
    demo = create_ui()
    # Launch configuration for both Hugging Face Spaces and local use
    demo.queue().launch()


if __name__ == "__main__":
    main()