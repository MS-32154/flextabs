"""Run the FlexTabs demo: ``python -m flextabs``."""

from .flextabs_demo import create_demo_app


def main():
    create_demo_app().mainloop()


if __name__ == "__main__":
    main()
