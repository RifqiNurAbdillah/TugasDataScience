# -----------------------------------------------------------------
#  run.py
#  Veltrix - Application entry point.
# -----------------------------------------------------------------

import os
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

# ── 🚨 TITIP KELAS INI DI SINI AGAR RECOGNIZED SEBAGAI __main__ RECOGNIZED OLEH PICKLE ──
class OutlierCapper(BaseEstimator, TransformerMixin):
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


# ── KODE BAWAAN ASLI APPLIKASI VELTRIX ───────────────────────────────────────────
from app import create_app

# Create the Flask application using the factory function
app = create_app()

if __name__ == "__main__":
    # Read host and port from environment variables (with sane defaults)
    host  = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port  = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    print(f"\n  * Veltrix is running -> http://{host}:{port}\n")
    app.run(host=host, port=port, debug=debug)