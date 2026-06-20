# Copyright 2014-2026 Facundo Batista, Nicolás Demarchi

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests<3",
# ]
# ///

import requests  # fades
import rich  # fades

rich.print(requests.get("https://example.com"))
