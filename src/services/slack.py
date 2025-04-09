import httpx

class SlackService:
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def send_action_response(self, response_url: str, layout: dict):
        async with httpx.AsyncClient() as client:
            await client.post(response_url, json=layout)