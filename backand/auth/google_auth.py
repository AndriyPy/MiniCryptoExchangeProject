from backand.auth.config import settings
import urllib.parse



def generate_google_oauth_redirect_uri():
    query_params = {
        "client_id":settings.OAUTH_GOOGLE_CLIENT_ID,
        "redirect_uri":"http://exchange.algorithmux.com/google/callback",
        "response_type":"code",
        "scope": " ".join([
            "openid",
            "profile",
            "email",
        ]),
        "state":""
    }


    query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    return f"{base_url}?{query_string}"