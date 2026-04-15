from fastapi import APIRouter, Depends, HTTPException, status
# from models import User
from config.db_conf import get_db

router = APIRouter(prefix="/api/v1/user", tags=["user"])

