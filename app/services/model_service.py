import os
import pickle
import numpy as np
import pandas as pd
from flask import current_app
from sklearn.base import BaseEstimator, TransformerMixin

# ── 0. WAJIB ADA: BLUEPRINT CLASS UNTUK UNPICKLING PIPELINE ──────────────────
class OutlierCapper(BaseEstimator, TransformerMixin):
    """
    Transformer kustom untuk menjinakkan outlier dengan metode Capping (IQR).
    Wajib ada di sini agar pickle.load() mengenali objek di dalam model pkl.
    """
    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}

    def fit(self, X, y=None):
        X_df = pd.DataFrame(X)
        for col in X_df.columns:
            q1 = X_df[col].quantile(0.25)
            q3 = X_df[col].quantile(0.75)
            iqr = q3 - q1
            self.lower_bounds_[col] = q1 - (self.factor * iqr)
            self.upper_bounds_[col] = q3 + (self.factor * iqr)
        return self

    def transform(self, X):
        X_df = pd.DataFrame(X).copy()
        for col in X_df.columns:
            if col in self.lower_bounds_:
                X_df[col] = np.clip(X_df[col], self.lower_bounds_[col], self.upper_bounds_[col])
        return X_df.to_numpy()


# ── SINGLETON LOADER UNTUK PIPELINE MODEL ─────────────────────────────────────
_model_pipeline = None
_last_load_error = None  # Variabel penampung error agar bisa dilempar ke UI

URUTAN_FITUR = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", 
    "thalach", "exang", "oldpeak", "slope", "ca", "thal"
]

def load_model_and_tokenizer():
    global _model_pipeline, _last_load_error
    
    # Jalur absolut mengarah ke folder static/models sesuai snapshot VS Code kamu
    model_path = os.path.join(current_app.root_path, 'static', 'models', 'model_logistic_jantung.pkl')
    
    try:
        if os.path.exists(model_path):
            with open(model_path, 'rb') as file:
                _model_pipeline = pickle.load(file)
            current_app.logger.info("✅ Model Pipeline Jantung loaded successfully.")
            _last_load_error = None
        else:
            _last_load_error = f"File model tidak ditemukan di jalur absolut server: {model_path}"
            current_app.logger.error(f"❌ {_last_load_error}")
            _model_pipeline = None
    except Exception as e:
        # Menangkap error unpickling asli (misal: versi scikit-learn berbeda atau class hilang)
        _last_load_error = f"Gagal memuat file .pkl (Pickle Error): {str(e)}"
        current_app.logger.error(f"❌ {_last_load_error}")
        _model_pipeline = None

def get_model():
    return _model_pipeline

# ── VALIDASI INPUT ERROR ──────────────────────────────────────────────────────
class PredictionInputError(ValueError):
    pass

# ── CORE PREDICTION (RISIKO PENYAKIT JANTUNG - PIPELINE VERSION) ──────────────
def predict_jantung(form_data: dict) -> dict:
    """
    Fungsi prediksi terintegrasi dengan Pipeline Sklearn. 
    Menerima dictionary dari Form HTML dan mengembalikan hasil prediksi risiko jantung.
    """
    result = {
        "success": False,
        "prediction": None,
        "formatted": "",
        "problem_type": "classification",
        "input_summary": {},
        "error": None,
    }

    if not form_data:
        return result

    global _model_pipeline, _last_load_error
    if _model_pipeline is None:
        load_model_and_tokenizer()
        if _model_pipeline is None:
            result["error"] = _last_load_error or "Model tidak tersedia di server. Periksa folder static/models."
            return result

    try:
        if "age" not in form_data:
            return result

        # 1. Ambil data dari form HTML & parsing ke tipe murni
        raw_features = {
            "age": float(form_data.get("age", 0)),
            "sex": int(form_data.get("sex", 0)),
            "cp": int(form_data.get("cp", 0)),
            "trestbps": float(form_data.get("trestbps", 0)),
            "chol": float(form_data.get("chol", 0)),
            "fbs": int(form_data.get("fbs", 0)),
            "restecg": int(form_data.get("restecg", 0)),
            "thalach": float(form_data.get("thalach", 0)),
            "exang": int(form_data.get("exang", 0)),
            "oldpeak": float(form_data.get("oldpeak", 0)),
            "slope": int(form_data.get("slope", 0)),
            "ca": int(form_data.get("ca", 0)),
            "thal": int(form_data.get("thal", 0))
        }

        # 2. Buat DataFrame sesuai urutan fitur
        features_df = pd.DataFrame([raw_features], columns=URUTAN_FITUR)

        # 3. Ambil prediksi asli dari model biner pkl
        raw_pred = int(_model_pipeline.predict(features_df)[0])
        probabilitas = _model_pipeline.predict_proba(features_df)[0]
        prob_persen = probabilitas[raw_pred] * 100

        # 4. SINKRONISASI LOGIKA TARGET (Inversi Kelas SMOTE)
        # Jika model mengeluarkan 0 artinya Sakit, kita ubah jadi 1 agar dibaca Bahaya oleh HTML.
        # Jika model mengeluarkan 1 artinya Sehat, kita ubah jadi 0 agar dibaca Aman oleh HTML.
        if raw_pred == 0:
            final_prediction = 1  # Set ke 1 agar HTML memicu Alert MERAH (Risiko Tinggi)
            hasil_label = f"Berisiko Tinggi Terkena Penyakit Jantung (Keyakinan: {prob_persen:.1f}%)"
        else:
            final_prediction = 0  # Set ke 0 agar HTML memicu Alert HIJAU (Aman)
            hasil_label = f"Aman / Risiko Rendah (Keyakinan: {prob_persen:.1f}%)"

        # Salin data untuk ringkasan tabel riwayat
        summary_data = {k: int(v) if k in ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"] else v for k, v in raw_features.items()}
        summary_data["prediction"] = final_prediction  # Selipkan status final ke riwayat tabel

        result.update({
            "success": True,
            "prediction": final_prediction,
            "formatted": hasil_label,
            "input_summary": summary_data,
        })
        
    except Exception as e:
        current_app.logger.exception(f"Prediction error: {e}")
        result["error"] = f"Terjadi kesalahan saat inferensi model: {str(e)}"

    return result

def get_field_options() -> dict:
    return {}

def get_model_info() -> dict:
    return {
        "problem_type": "Pipeline Logistic Regression (Robust + Capper + SMOTE)",
        "feature_columns": URUTAN_FITUR,
        "target_column": "target",
        "model_loaded": _model_pipeline is not None,
    }