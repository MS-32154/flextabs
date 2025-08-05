from .flextabs_demo import FlexTabsDemo

if __name__ == "__main__":
    try:
        demo = FlexTabsDemo()
        demo.run()

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
