import BillSplitterApp.backend.mongodb as backendService




auth = backendService.Authenticator()
print(auth.login('arb','1234'))