# main.py
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import yaml

load_dotenv()  # loads .env into os.environ
#print("hellow")
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

defaults = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

def parse_bool(v):
    return str(v).lower() in ("true", "1", "yes", "on")

def apply_layer(base, layer):
    for k, v in (layer or {}).items():
        base[k] = v

def read_yaml(path):
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def read_env_layer():
    # From .env (already loaded into os.environ)
    layer = {}
    if os.environ.get("NUM_WORKERS") is not None:
        layer["workers"] = os.environ.get("NUM_WORKERS")
    if os.environ.get("APP_DEBUG") is not None:
        layer["debug"] = os.environ.get("APP_DEBUG")
    if os.environ.get("APP_API_KEY") is not None:
        layer["api_key"] = os.environ.get("APP_API_KEY")
    return layer

def read_os_app_layer():
    layer = {}
    for k, v in os.environ.items():
        if k.startswith("APP_"):
            key = k[4:].lower()
            layer[key] = v
    return layer

def coerce_types(cfg):
    # port/workers -> int
    try:
        cfg["port"] = int(cfg["port"])
    except Exception:
        raise HTTPException(status_code=400, detail="port must be int")
    try:
        cfg["workers"] = int(cfg["workers"])
    except Exception:
        raise HTTPException(status_code=400, detail="workers must be int")
    cfg["debug"] = parse_bool(cfg["debug"])
    cfg["log_level"] = str(cfg["log_level"])
    cfg["api_key"] = "****"
    return cfg

@app.get("/effective-config")
async def effective_config(request: Request):
    # Start with defaults
    cfg = defaults.copy()

    # YAML layer (environment-specific; assignment says config.development.yaml)
    yaml_layer = read_yaml("config.development.yaml")
    apply_layer(cfg, yaml_layer)

    # .env layer (NUM_WORKERS alias handled)
    env_layer = read_env_layer()
    apply_layer(cfg, env_layer)

    # OS env layer (APP_*)
    app_layer = read_os_app_layer()
    apply_layer(cfg, app_layer)

    # CLI overrides via repeated ?set=key=value
    sets = request.query_params.getlist("set")
    for s in sets:
        if "=" not in s:
            continue
        key, val = s.split("=", 1)
        cfg[key] = val

    # Coerce and mask
    cfg = coerce_types(cfg)

    # Return only the five keys required (ensure stable order)
    return {
        "port": cfg["port"],
        "workers": cfg["workers"],
        "debug": cfg["debug"],
        "log_level": cfg["log_level"],
        "api_key": cfg["api_key"],
    }