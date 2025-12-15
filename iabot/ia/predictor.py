import os
import django
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from sklearn.ensemble import RandomForestClassifier
from django.utils import timezone

# === 1. Configurar Django ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iabot.settings")
django.setup()

from base.models import Accion, DecisionBot

# === 2. Ruta absoluta al archivo CSV ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ruta_csv = os.path.join(BASE_DIR, "datos", "copec_historico.csv")

log = []  # 📝 Diagnóstico visible

# === 3. Cargar archivo CSV ===
try:
    df = pd.read_csv(ruta_csv)
    log.append(f"✅ Archivo leído: {ruta_csv}")
except Exception as e:
    print(f"❌ Error al leer CSV: {e}")
    exit()

# === 4. Renombrar columnas ===
df = df.rename(columns={
    "Fecha": "fecha",
    "Último": "cierre",
    "Apertura": "apertura",
    "Máximo": "maximo",
    "Mínimo": "minimo",
    "Vol.": "volumen"
})

# === 5. Limpiar valores numéricos ===
for col in ["apertura", "cierre", "maximo", "minimo"]:
    df[col] = df[col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)

df["volumen"] = df["volumen"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
df["volumen"] = df["volumen"].str.replace("K", "e3", regex=False).str.replace("M", "e6", regex=False).astype(float)

# === 6. Preparar índice de fechas ===
df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True)
df.sort_values("fecha", inplace=True)
df.set_index("fecha", inplace=True)

log.append(f"✅ Total de filas cargadas: {len(df)}")

# === 7. Calcular indicadores técnicos ===
df["rsi"] = RSIIndicator(close=df["cierre"], window=14).rsi()
macd = MACD(close=df["cierre"], window_slow=26, window_fast=12, window_sign=9)
df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()

df.dropna(inplace=True)
log.append(f"✅ Filas después de limpiar NaNs: {len(df)}")

# === 8. Crear etiqueta de predicción ===
df["sube"] = (df["cierre"].shift(-1) > df["cierre"]).astype(int)

features = ["apertura", "cierre", "maximo", "minimo", "volumen", "rsi", "macd", "macd_signal"]
X = df[features][:-1]
y = df["sube"][:-1]

log.append(f"🧠 Filas para entrenamiento: {len(X)}")

# === 9. Modelo IA y registro ===
if len(X) < 10:
    log.append("❌ No hay suficientes datos para entrenar. Se requieren al menos 10 registros válidos.")
else:
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X, y)

    X_ultimo = df[features].iloc[[-1]]
    pred = modelo.predict(X_ultimo)[0]
    confianza = modelo.predict_proba(X_ultimo)[0].max()
    precio = float(df["cierre"].iloc[-1])

    accion_obj, _ = Accion.objects.get_or_create(
        simbolo="COPEC",
        defaults={"nombre": "Empresas Copec", "precio_actual": precio}
    )

    DecisionBot.objects.create(
        accion=accion_obj,
        tipo_decision="compra" if pred == 1 else "venta",
        motivo="Basado en RSI, MACD y patrones de precios históricos.",
        score_confianza=confianza,
        precio_objetivo=precio * (1.03 if pred == 1 else 0.97),
        ejecutada=False,
        fecha_decision=timezone.now()
    )

    log.append(f"✅ Decisión registrada: {'COMPRA' if pred == 1 else 'VENTA'} con confianza de {round(confianza*100,2)}%")

# === 10. Mostrar traza en dashboard ===
print(" | ".join(log))