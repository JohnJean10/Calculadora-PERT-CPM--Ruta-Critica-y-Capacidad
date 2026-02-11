# Datos de modelos RK Power
# Familia A: 80-100 KW
# Familia B: 130-150, 180-230 KW
# Familia C: 250-275, 300-400 KW
# Familia D: 500, 600 KW

FAMILIAS = {
    "A": ["80-100KW"],
    "B": ["130-150KW", "180-230KW"],
    "C": ["250-275KW", "300-400KW"],
    "D": ["500KW", "600KW"]
}

# Factores de escala respecto al modelo base (80-100KW)
FACTORES_ESCALA = {
    "80-100KW": 1.0,
    "130-150KW": 1.25,
    "180-230KW": 1.7,
    "250-275KW": 2.0,
    "300-400KW": 2.5,
    "500KW": 3.5,
    "600KW": 4.0
}
