# ------------------------------------------------------------------------------------------------ #
# Copyright (c) 2026 Carmenda. All rights reserved.                                                #
# This program is distributed under the terms of the PolyForm Noncommercial License 1.0.0          #
# ------------------------------------------------------------------------------------------------ #

"""API configuration.

This package provides configurations for the API.

Priority order for settings values (highest to lowest):
    1. Real environment variables (e.g. via docker-compose)
    2. The .env file loaded by pydantic-settings (path depends on environment)
    3. Default values defined on the Settings class
"""
