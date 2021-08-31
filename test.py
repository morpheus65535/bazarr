from requests import Session
import json
import os

email = "mymail@gmail.com"
hashed_password=""
server_url = "https://www.ktuvit.me/"
sign_in_url = "Services/MembershipService.svc/Login"

session = Session()
data = {"request": {"Email": email, "Password": hashed_password}}
            
session.headers['Accept-Encoding'] = 'gzip'
session.headers['Accept-Language'] = 'en-us,en;q=0.5'
session.headers['Pragma'] = 'no-cache'
session.headers['Cache-Control'] = 'no-cache'
session.headers['Content-Type'] = 'application/json'
session.headers['User-Agent']: os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")

r = session.post(
    server_url + sign_in_url,
    json=data,
    allow_redirects=False,
    timeout=10,
)

# with data=data,
print(str(r.content))
# b'{"ExceptionDetail":null,"ExceptionType":null,"Message":"The server was unable to process the request due to an internal error.  For more information about the error, either turn on IncludeExceptionDetailInFaults (either from ServiceBehaviorAttribute or from the <serviceDebug> configuration behavior) on the server in order to send the exception information back to the client, or turn on tracing as per the Microsoft .NET Framework SDK documentation and inspect the server trace logs.","StackTrace":null}'


# With data=json.dumps(data),
r = session.post(
    server_url + sign_in_url,
    data=json.dumps(data),
    allow_redirects=False,
    timeout=10,
)

print(str(r.content))
# b'{"d":"{\\"IsSuccess\\":false,\\"ErrorMessage\\":\\"\xd7\xa4\xd7\xa8\xd7\x98\xd7\x99 \xd7\x94\xd7\x94\xd7\xaa\xd7\x97\xd7\x91\xd7\xa8\xd7\x95\xd7\xaa \xd7\xa9\xd7\x92\xd7\x95\xd7\x99\xd7\x99\xd7\x9d\\"}"}'