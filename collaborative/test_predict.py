from .api import get_recommendations

if __name__ == "__main__":
    print(
        get_recommendations(
            [
                ("SOAUWYT12A81C206F1", 23),
                ("SOFPXXK12A6D4FA1D9", 15),
                ("SOLFUPR12A6D4F9A3D", 5),
                ("SOMAKEB12A8C1322D2", 6),
            ]
        )
    )
