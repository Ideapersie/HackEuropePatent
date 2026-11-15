import os
import requests
import base64

public_key = os.environ["EPO_CONSUMER_KEY"]
secret_key = os.environ["EPO_CONSUMER_SECRET"]

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

