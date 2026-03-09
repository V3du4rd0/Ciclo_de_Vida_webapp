from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask import render_template, redirect, url_for

import json
import os
import pandas as pd
import numpy as np
import uuid
import re
from functools import lru_cache
from rapidfuzz import fuzz
from deep_translator import GoogleTranslator



#app = Flask(__name__, static_folder=".", static_url_path="")
app = Flask(__name__)

CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

translator = GoogleTranslator(source='es', target='en')


@lru_cache(maxsize=2048)
def translate_es_en(text):
    try:
        return translator.translate(text)
    except Exception:
        return text


CMLIA_df = pd.read_excel(
    "./databases/CML-IA_aug_2016.xls",
    sheet_name="characterisation factors",
    dtype=str
)

TRACI_df = pd.read_excel(
    "./databases/traci_2_2.xlsx",
    sheet_name="Substances",
    dtype=str
)

# ----- preprocess CMLIA column names
row1 = CMLIA_df.iloc[1, 10:]
row4 = CMLIA_df.iloc[4, 10:]
new_cols = []

for r1, r4 in zip(row1, row4):
    parts = []
    if pd.notna(r1) and str(r1).strip():
        parts.append(str(r1).strip())
    if pd.notna(r4) and str(r4).strip():
        parts.append(str(r4).strip())
    new_cols.append(' - '.join(parts) if parts else '')

CMLIA_df.columns = list(CMLIA_df.columns[:10]) + new_cols

CMLIA_df.columns.values[1] = "cas no."
CMLIA_df.columns.values[2] = "cas no. (other format)"
CMLIA_df.columns.values[3] = "ecoinvent ID old"
CMLIA_df.columns.values[4] = "DS ID"
CMLIA_df.columns.values[5] = "Meta ID"
CMLIA_df.columns.values[6] = "group"
CMLIA_df.columns.values[7] = "initial emission or extraction"
CMLIA_df.columns.values[8] = "unit"


clean_re = re.compile(r'\s*\(.*?\)\s*')

def clean_parentheses(s):
    return clean_re.sub('', str(s)).strip().lower()


def batch_search(dataset, keywords, threshold=85):

    if "Characterisation factors" in dataset.columns:
        series_raw = dataset["Characterisation factors"].astype(str)
        dataset_name = "CMLIA"
    elif "Substance Name" in dataset.columns:
        series_raw = dataset["Substance Name"].astype(str)
        dataset_name = "TRACI"
    else:
        dataset_name = "Unknown"
        return []

    series_clean = series_raw.str.lower().apply(clean_parentheses)

    blob = ",".join(keywords)
    translated_blob = translate_es_en(blob)
    translated_list = [clean_parentheses(x) for x in translated_blob.split(",")]

    results = []
    index_map = {}

    for idx, text in series_clean.items():
        if len(text) >= 3:
            token = text[:3]
            index_map.setdefault(token, []).append(idx)

    for original_key, translated in zip(keywords, translated_list):

        if not translated:
            results.append({
                "spanish": original_key,
                "english": translated,
                "dataset": dataset_name,
                "matches": []
            })
            continue

        token = translated[:3]
        candidate_indices = index_map.get(token, [])
        found_rows = []

        for idx in candidate_indices:
            cand = series_clean.iloc[idx]
            score = max(
                fuzz.ratio(cand, translated),
                fuzz.partial_ratio(cand, translated)
            )

            if score >= threshold:
                row = dataset.iloc[idx]
                clean_row = {
                    col: val for col, val in row.items()
                    if pd.notna(val) and str(val).strip() != ""
                }
                found_rows.append(clean_row)

        results.append({
            "spanish": original_key,
            "english": translated,
            "dataset": dataset_name,
            "matches": found_rows
        })

    return results


@app.route("/save", methods=["POST"])
def save_data():
    try:
        data = request.json
        session_id = str(uuid.uuid4())

        data_file = os.path.join(DATA_DIR, f"data_{session_id}.json")
        matrices_file = os.path.join(DATA_DIR, f"matrices_{session_id}.npz")
        impact_file = os.path.join(DATA_DIR, f"impact_{session_id}.json")

        # ----- Save raw input
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # ----- Build matrices
        rows = []
        for process in data["processes"]:
            for m in process["materials"]:
                rows.append({
                    "processName": process["processName"],
                    "descripcion": m["descripcion"],
                    "cantidad": m["cantidad"],
                    "ecamb": m["ecamb"]
                })

        df = pd.DataFrame(rows)

        ec_vars = sorted(df[df["ecamb"] == "EC"]["descripcion"].unique())
        amb_vars = sorted(df[df["ecamb"] == "Amb"]["descripcion"].unique())
        processes = [p["processName"] for p in data["processes"]]

        A = np.zeros((len(ec_vars), len(processes)))
        B = np.zeros((len(amb_vars), len(processes)))

        for j, process in enumerate(processes):
            sub = df[df["processName"] == process]

            for i, var in enumerate(ec_vars):
                row = sub[(sub["descripcion"] == var) & (sub["ecamb"] == "EC")]
                if not row.empty:
                    A[i, j] = float(row["cantidad"].values[0])

            for i, var in enumerate(amb_vars):
                row = sub[(sub["descripcion"] == var) & (sub["ecamb"] == "Amb")]
                if not row.empty:
                    B[i, j] = float(row["cantidad"].values[0])

        demand = data.get("demandVector", [])
        v = np.zeros(len(processes))

        for d in demand:
            if d["proceso"] in processes:
                idx = processes.index(d["proceso"])
                v[idx] = d["cantidad"]

        try:
            A_inv = np.linalg.inv(A)
            w = B @ A_inv @ v
        except np.linalg.LinAlgError:
            w = np.full(len(amb_vars), np.nan)

        np.savez(
            matrices_file,
            A=A,
            B=B,
            v=v,
            w=w,
            amb_vars=np.array(amb_vars, dtype=object)
        )

        matches = batch_search(CMLIA_df, amb_vars)
        matches += batch_search(TRACI_df, amb_vars)

        with open(impact_file, "w", encoding="utf-8") as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)

        return jsonify({
            "message": "Evaluación completada con éxito",
            "session_id": session_id
        })

    except Exception as e:
        print("ERROR EN /save:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/get_matrices")
def get_matrices():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    matrices_file = os.path.join(DATA_DIR, f"matrices_{session_id}.npz")

    if not os.path.exists(matrices_file):
        return jsonify({"error": "Session not found"}), 404

    data = np.load(matrices_file, allow_pickle=True)

    return jsonify({
        "A": data["A"].tolist(),
        "B": data["B"].tolist(),
        "v": data["v"].tolist(),
        "w": data["w"].tolist(),
        "amb_vars": data["amb_vars"].tolist()
    })



@app.route("/impact_data")
def get_impact_data():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    impact_file = os.path.join(DATA_DIR, f"impact_{session_id}.json")

    if not os.path.exists(impact_file):
        return jsonify({"error": "Session not found"}), 404

    with open(impact_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify(data)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/nuevo")
def nuevo():
    return render_template("nuevo.html")


@app.route("/ejemplos")
def ejemplos():
    return render_template("ejemplos.html")


@app.route("/ejemplo/maqueta")
def ejemplo_maqueta():
    return render_template("examples/maqueta.html")


@app.route("/ejemplo/velaria")
def ejemplo_velaria():
    return render_template("examples/velaria.html")


@app.route("/ejemplo/impresion3D")
def ejemplo_impresion3D():
    return render_template("examples/impresion3D.html")


@app.route("/results")
def results():
    session_id = request.args.get("session_id")
    if not session_id:
        return redirect(url_for("index"))

    return render_template("results.html", session_id=session_id)


@app.route("/results_data")
def results_data():
    session_id = request.args.get("session_id")
    data_file = os.path.join(DATA_DIR, f"data_{session_id}.json")

    if not os.path.exists(data_file):
        return jsonify({"data": []})

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for process in data["processes"]:
        for m in process["materials"]:
            rows.append(m)

    return jsonify({"data": rows})



# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
