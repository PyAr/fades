# Copyright 2014-2026 Facundo Batista, Nicolás Demarchi

# /// script
# dependencies = [
#   "requests<3",
#   "rich",
# ]
# ///

import requests
from rich.pretty import pprint

pprint(requests.get("https://example.com"))
