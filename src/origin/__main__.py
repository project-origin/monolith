from .cli import main


if __name__ == "__main__":
    main()

from authlib.integrations.requests_client import OAuth2Session

client = OAuth2Session(
            client_id=HYDRA_CLIENT_ID,
            client_secret=HYDRA_CLIENT_SECRET,
            scope=HYDRA_WANTED_SCOPES,
        )

client.create_authorization_url(
                url=HYDRA_AUTH_ENDPOINT,
                redirect_uri=LOGIN_CALLBACK_URL,
            )

client.fetch_token(
                url=HYDRA_TOKEN_ENDPOINT,
                grant_type='authorization_code',
                code=code,
                state=state,
                redirect_uri=LOGIN_CALLBACK_URL,
                verify=not DEBUG,
            )

# from .app import app
#
#
# app.run(
#     host='0.0.0.0',
#     port='8080',
# )
