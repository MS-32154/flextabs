from .flextabs_demo import create_demo_app


def main():
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
    print("👋 FlexTabs Demo finished. Thanks for trying it!")


if __name__ == "__main__":
    main()
