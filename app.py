# app.py
# Pastel Eye Colorizer - Main application entry point
# This file imports and runs the modular application from src/

try:
    # Try to import from the modular structure
    from src.main import main

    if __name__ == "__main__":
        main()

except ImportError:
    # Fallback: if modular structure is not available, run the basic version
    print("Modular structure not found, running fallback version...")

    # Import the modular components if they exist
    try:
        from src.ui import create_ui

        if __name__ == "__main__":
            demo = create_ui()
            demo.queue().launch()

    except ImportError:
        print(
            "Error: Cannot find modular components in src/. Please ensure the modular structure is properly set up."
        )
        print(
            "Expected files: src/main.py, src/ui.py, src/core.py, src/config.py, src/generators.py"
        )
        raise
