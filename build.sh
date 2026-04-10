#!/usr/bin/env bash

export PYTHONPATH=$(pwd)

pip install -r requirements.txt

python -m alembic upgrade head
