import requests
import base64

public_key = "WCy9x82YtWH4d4t4B9q3mMBcN0fPCgPGiPCGM6uUFJ9zXcv7"
secret_key = "fowLZm2Bu0XHRLxoOfSdYQLfn4SVPAkTWF4djJE6hwDYg4tM9EgAD29stYhwM03c"

credentials = f"{public_key}:{secret_key}"
encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

url = "https://ops.epo.org/3.2/auth/accesstoken"

data = "grant_type=client_credentials"

headers = {
    "Authorization": f"Basic {encoded}",
    "Content-Type": "application/x-www-form-urlencoded",
}

x= requests.post(url, headers=headers, data=data)

print(x.status_code)
print(x.text)

#   "access_token": "v5EJWcil1GggCAmiTE7RoYAuRyX",