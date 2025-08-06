from .flextabs_demo import create_demo_app

if __name__ == "__main__":
    try:
        app = create_demo_app()

        print("Tab Manager Demo Started!")
        print("Try these features:")
        print("• Switch opener types using radio buttons")
        print("• Use keyboard shortcuts (F1-F4, Ctrl+W, Ctrl+Tab)")
        print("• Right-click tabs to close them")
        print("• Try closing the unclosable 'System' tab")
        print("• Add dynamic tabs from the Home tab")
        print("• Change settings in the Settings tab")

        app.mainloop()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("📦 Make sure FlexTabs library is installed and in your Python path")
        print("💡 Place this demo file in the same directory as the flextabs package")

    except Exception as e:
        print(f"💥 Demo Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("👋 FlexTabs Demo finished. Thanks for trying it!")
