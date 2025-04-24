import logging

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/clear_logs")
def clear_logs():
    log_file = "app.log"
    try:
        # Очищаем содержимое файла
        with open(log_file, "w") as f:
            f.write("")
        logging.info("Log file cleared by user.")
        return {"status": "success", "message": "Log file cleared successfully."}
    except Exception as e:
        logging.error(f"Failed to clear log file: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear log file.")

@router.get("/test-error")
def test_error():
    # Искусственно создаём ошибку
    raise ValueError("This is a test exception.")

@router.get('/logs')
def get_logs():
    try:
        with open("app.log", "r") as f:
            log_contents = f.read()
        return log_contents
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Log file not found")