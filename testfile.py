import BillSplitterApp.backend.mongodb as backendService
import random, string


auth = backendService.Authenticator()
surveydata = auth.get_survey_data("KX0J4L5X", "test")
print(surveydata)