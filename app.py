import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import gc

# -----------------------------------
# CONFIGURACIÓN
# -----------------------------------
st.set_page_config(
    page_title="Validador PDF",
    page_icon="📄",
    layout="wide"
)

# -----------------------------------
# MENSAJE PERSONAL
# -----------------------------------
st.markdown(
    """
    <div style="
        background-color:#f5f5f5;
        padding:18px;
        border-radius:10px;
        text-align:center;
        font-size:20px;
        font-weight:600;
        color:#333;
        border:1px solid #ddd;
        margin-bottom:15px;
    ">
        CON TODO MI AMOR PARA TI MI
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------
# SESSION STATE
# -----------------------------------
if "cedula" not in st.session_state:
    st.session_state.cedula = ""

if "nombre" not in st.session_state:
    st.session_state.nombre = ""

if "fecha_inicio" not in st.session_state:
    st.session_state.fecha_inicio = datetime.today().date()

if "fecha_fin" not in st.session_state:
    st.session_state.fecha_fin = datetime.today().date()

if "files" not in st.session_state:
    st.session_state.files = None

if "analizar" not in st.session_state:
    st.session_state.analizar = False


# -----------------------------------
# FUNCIONES
# -----------------------------------
def limpiar_formulario():
    st.session_state.cedula = ""
    st.session_state.nombre = ""
    st.session_state.fecha_inicio = datetime.today().date()
    st.session_state.fecha_fin = datetime.today().date()

def refrescar_archivos():
    st.session_state.files = None
    st.session_state.analizar = False
    st.rerun()


# -----------------------------------
# TÍTULO
# -----------------------------------
st.title("Validador de Documentos PDF")


# -----------------------------------
# BOTONES
# -----------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Refrescar archivos"):
        refrescar_archivos()

with col2:
    if st.button("Limpiar información"):
        limpiar_formulario()
        st.rerun()

with col3:
    with st.expander("Información"):
        st.write("""
Validación de documentos PDF:
- Cédula
- Nombre
- Rango de fechas
""")


# -----------------------------------
# PARÁMETROS
# -----------------------------------
st.header("Parámetros de validación")

cedula = st.text_input("Número de documento", key="cedula")
nombre_completo = st.text_input("Nombre completo", key="nombre")

fecha_inicio = st.date_input("Fecha inicio", key="fecha_inicio")
fecha_fin = st.date_input("Fecha fin", key="fecha_fin")


# -----------------------------------
# ARCHIVOS
# -----------------------------------
st.session_state.files = st.file_uploader(
    "Subir documentos PDF",
    type=["pdf"],
    accept_multiple_files=True
)

uploaded_files = st.session_state.files


# -----------------------------------
# BOTONES CONTROL
# -----------------------------------
colA, colB = st.columns(2)

with colA:
    if st.button("Analizar documentos"):
        st.session_state.analizar = True

with colB:
    if st.button("Reiniciar análisis"):
        st.session_state.analizar = False
        st.rerun()


# -----------------------------------
# MENSAJE ESPERA
# -----------------------------------
if uploaded_files and not st.session_state.analizar:
    st.info("Cargue los archivos y presione Analizar documentos para continuar.")


# -----------------------------------
# DETECCIÓN DE FECHAS
# -----------------------------------
def extraer_fechas(texto):

    texto = texto.lower().replace("\n", " ")

    meses = {
        "enero": 1, "febrero": 2, "marzo": 3,
        "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9,
        "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12
    }

    fechas = []

    patrones = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b",
    ]

    for patron in patrones:
        for f in re.findall(patron, texto):
            try:
                f = f.replace("-", "/").replace(".", "/")
                partes = f.split("/")

                if len(partes[0]) == 4:
                    fecha = datetime.strptime(f, "%Y/%m/%d")
                else:
                    fecha = datetime.strptime(f, "%d/%m/%Y")

                fechas.append(fecha.date())
            except:
                pass

    palabras = texto.split()

    dias = []
    meses_encontrados = []
    años = []

    for p in palabras:
        if p.isdigit() and len(p) == 4:
            años.append(int(p))
        elif p.isdigit() and 1 <= int(p) <= 31:
            dias.append(int(p))
        elif p in meses:
            meses_encontrados.append(meses[p])

    for anio in años:
        for mes in meses_encontrados:
            for dia in dias:
                try:
                    fechas.append(datetime(anio, mes, dia).date())
                except:
                    pass

    return list(set(fechas))


# -----------------------------------
# PROCESO
# -----------------------------------
if uploaded_files and st.session_state.analizar:

    resultados = []

    st.success(f"{len(uploaded_files)} archivo(s) cargado(s)")

    progress = st.progress(0)
    status = st.empty()

    for i, archivo in enumerate(uploaded_files):

        status.text(f"Procesando {archivo.name}")

        texto = ""

        try:
            with pdfplumber.open(archivo) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt:
                        texto += txt + "\n"

            texto_up = texto.upper()

            cumple_cedula = cedula in texto
            palabras = nombre_completo.upper().split()
            cumple_nombre = all(p in texto_up for p in palabras)

            fechas = extraer_fechas(texto)

            fecha_valida = False
            fecha_encontrada = ""

            for f in fechas:
                if fecha_inicio <= f <= fecha_fin:
                    fecha_valida = True
                    fecha_encontrada = str(f)
                    break

            estado_final = "CUMPLE" if (
                cumple_cedula and cumple_nombre and fecha_valida
            ) else "NO CUMPLE"

            resultados.append({
                "Archivo": archivo.name,
                "Documento valido": "Si" if cumple_cedula else "No",
                "Nombre valido": "Si" if cumple_nombre else "No",
                "Fecha encontrada": fecha_encontrada or "No encontrada",
                "Fecha valida": "Si" if fecha_valida else "No",
                "Resultado final": estado_final
            })

        except:
            resultados.append({
                "Archivo": archivo.name,
                "Documento valido": "Error",
                "Nombre valido": "Error",
                "Fecha encontrada": "Error",
                "Fecha valida": "Error",
                "Resultado final": "Error PDF"
            })

        gc.collect()
        progress.progress((i + 1) / len(uploaded_files))

    status.empty()

    df = pd.DataFrame(resultados)

    st.success("Validación completada")
    st.dataframe(df, use_container_width=True)

    file_excel = "resultado_validacion.xlsx"
    df.to_excel(file_excel, index=False)

    with open(file_excel, "rb") as f:
        st.download_button(
            "Descargar Excel",
            f,
            file_name=file_excel
        )
