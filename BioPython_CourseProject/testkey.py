from google import genai

client = genai.Client(api_key="AIzaSyCf2-Ap8SktjyT1WLEX8MFgfmMCDW2zc38")

resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say OK"
)

print(resp.candidates[0].content.parts[0].text)
