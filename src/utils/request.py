from fastapi import Request

async def parse_request(request: Request):
    form_data = await request.form()
    text = form_data.get("text")
    user_id = form_data.get("user_id")
    user_name = form_data.get("user_name")
    response_url = form_data.get("response_url")
    return text, user_id, user_name, response_url