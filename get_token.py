from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def main():
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=8080)
    # Lưu token ra file token.json
    with open('token.json', 'w') as token_file:
        token_file.write(creds.to_json())
    print("Đã tạo file token.json thành công!")

if __name__ == '__main__':
    main()
