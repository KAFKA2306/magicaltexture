from .ui import create_ui
def main():
    """Main application entry point"""
    demo = create_ui()
    demo.queue().launch()
if __name__ == "__main__":
    main()
