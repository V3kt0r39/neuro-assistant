import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import psycopg2

# --- SETTINGS ---
# Settings for connecting to local PostgreSQL (port 5432)
DB_CONFIG = {
    "dbname": "your_db_name",       # Replace with your database name
    "user": "your_bd_user",      # Replace with your database user
    "password": "your_strong_password",     # Replace with your password
    "host": "127.0.0.1",
    "port": "your_db_port"
}

# Global variable to store the selected user_id
CURRENT_USER_ID = 1

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="NeuroInterface Data Receiver")

# Model for expected data from Unity
class EEGDataRequest(BaseModel):
    concentration: float
    relaxation: float
    poor_signal: int

def init_database():
    """Creates the 'data' table if it does not already exist"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Create the 'data' table (recording time is stored in the recorded_at column)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                concentration FLOAT NOT NULL,
                relaxation FLOAT NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("✅ Database connected. 'data' table checked/created.")
    except Exception as e:
        logging.error(f"❌ Database initialization error: {e}")
        raise

@app.post("/api/analyze")
def receive_eeg_data(request_data: EEGDataRequest):
    """Receives data, checks for noise/interference, and saves to the database"""
    logging.info(f"Data received: conc={request_data.concentration}, "
                 f"relax={request_data.relaxation}, poor={request_data.poor_signal}")

    # 1. CONDITION: If poor_signal > 25, reject the request
    if request_data.poor_signal > 25:
        logging.warning(f"⛔ REQUEST REJECTED: Noise level too high (poor_signal={request_data.poor_signal} > 25). Data not saved.")
        raise HTTPException(
            status_code=400, 
            detail="Noise level too high. Please adjust the headset."
        )

    # 2. If noise is within normal limits, write to the database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO data (user_id, concentration, relaxation, recorded_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id, recorded_at;
        """, (CURRENT_USER_ID, request_data.concentration, request_data.relaxation))
        
        inserted_id, recorded_at = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        logging.info(f"✅ DATA SUCCESSFULLY SAVED: user_id={CURRENT_USER_ID}, record_id={inserted_id}, time={recorded_at}")
        
        return {
            "status": "success",
            "message": "Data successfully saved to the database",
            "user_id": CURRENT_USER_ID
        }
        
    except psycopg2.Error as db_err:
        logging.error(f"❌ Error writing to PostgreSQL: {db_err}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logging.error(f"❌ Unknown error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    print("="*50)
    print("  NEUROINTERFACE DATA RECEIVER SERVER STARTUP")
    print("="*50)
    
    # Request user_id on startup
    while True:
        try:
            user_input = input("Enter the user_id number to write to the database (integer): ")
            CURRENT_USER_ID = int(user_input)
            print(f"Selected user_id: {CURRENT_USER_ID}")
            break
        except ValueError:
            print("⚠️ Error: Please enter a valid integer.")

    # Database initialization
    init_database()

    # Start server on port 8822
    print("\n🚀 Server started and listening on port 8822...")
    print("Press Ctrl+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=8822)
